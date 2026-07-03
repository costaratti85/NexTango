"""Tests para tango_sync/customer_push.py — mock-based, sin servidor real."""
import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "sistema_industrial"))

from unittest.mock import MagicMock

from sistema_industrial.tango_sync.schemas import TangoCustomer
from sistema_industrial.tango_sync.customer_push import (
    CustomerSyncResult,
    _build_customer_doc,
    push_customers_to_erpnext,
)


def _customer(**kwargs) -> TangoCustomer:
    defaults = dict(
        code="001",
        name="Ferretería Lomas SA",
        cuit="30-12345678-9",
        email="contact@ferreteria.com",
        phone="011-4567",
        vat_condition="RI",
        is_active=True,
        tango_id=42,
    )
    defaults.update(kwargs)
    return TangoCustomer(**defaults)


class TestBuildCustomerDoc:
    def test_ri_maps_to_commercial_company(self):
        doc = _build_customer_doc(
            _customer(vat_condition="RI"),
            default_price_list="Precio Standard",
            default_customer_group="Commercial",
        )
        assert doc["customer_group"] == "Commercial"
        assert doc["customer_type"] == "Company"

    def test_mo_maps_to_commercial_company(self):
        doc = _build_customer_doc(
            _customer(vat_condition="MO"),
            default_price_list="Precio Standard",
            default_customer_group="Commercial",
        )
        assert doc["customer_group"] == "Commercial"
        assert doc["customer_type"] == "Company"

    def test_cf_maps_to_individual(self):
        doc = _build_customer_doc(
            _customer(vat_condition="CF"),
            default_price_list="Precio Standard",
            default_customer_group="Commercial",
        )
        assert doc["customer_group"] == "Individual"
        assert doc["customer_type"] == "Individual"

    def test_unknown_vat_uses_default_group(self):
        doc = _build_customer_doc(
            _customer(vat_condition=None),
            default_price_list="Precio Standard",
            default_customer_group="Commercial",
        )
        assert doc["customer_group"] == "Commercial"
        assert doc["customer_type"] == "Company"

    def test_inactive_sets_disabled_1(self):
        doc = _build_customer_doc(
            _customer(is_active=False),
            default_price_list="Precio Standard",
            default_customer_group="Commercial",
        )
        assert doc["disabled"] == 1

    def test_active_sets_disabled_0(self):
        doc = _build_customer_doc(
            _customer(is_active=True),
            default_price_list="Precio Standard",
            default_customer_group="Commercial",
        )
        assert doc["disabled"] == 0

    def test_si_tango_code_and_id_included(self):
        doc = _build_customer_doc(
            _customer(code="XYZ789", tango_id=99),
            default_price_list="Precio Standard",
            default_customer_group="Commercial",
        )
        assert doc["si_tango_code"] == "XYZ789"
        assert doc["si_tango_id"] == 99

    def test_price_list_propagated(self):
        doc = _build_customer_doc(
            _customer(),
            default_price_list="Lista Especial",
            default_customer_group="Commercial",
        )
        assert doc["default_price_list"] == "Lista Especial"


class TestPushCustomers:
    def _mock_client(self, find_return=None):
        client = MagicMock()
        client.find_customer_by_tango_code.return_value = find_return
        return client

    def test_new_customer_calls_create_doc(self):
        client = self._mock_client(find_return=None)

        result = push_customers_to_erpnext([_customer()], client)

        client.create_doc.assert_called_once()
        doctype_arg = client.create_doc.call_args[0][0]
        assert doctype_arg == "Customer"
        assert result.created == 1
        assert result.updated == 0
        assert result.failed == 0

    def test_existing_customer_calls_patch_doc(self):
        client = self._mock_client(
            find_return={"name": "Ferretería Lomas SA", "si_tango_code": "001", "disabled": 0}
        )

        result = push_customers_to_erpnext([_customer()], client)

        client.patch_doc.assert_called_once()
        assert client.patch_doc.call_args[0][0] == "Customer"
        assert client.patch_doc.call_args[0][1] == "Ferretería Lomas SA"
        client.create_doc.assert_not_called()
        assert result.updated == 1
        assert result.created == 0

    def test_error_on_one_does_not_stop_sync(self):
        client = MagicMock()
        client.find_customer_by_tango_code.side_effect = [
            RuntimeError("connection timeout"),
            None,
        ]

        customers = [
            _customer(code="001"),
            _customer(code="002", name="Otro SRL"),
        ]
        result = push_customers_to_erpnext(customers, client)

        assert result.failed == 1
        assert result.created == 1
        assert result.errors[0] == ("001", "connection timeout")

    def test_result_total_is_created_plus_updated_plus_failed(self):
        client = MagicMock()
        client.find_customer_by_tango_code.side_effect = [
            None,
            {"name": "Existente SA", "si_tango_code": "002", "disabled": 0},
            RuntimeError("boom"),
        ]

        customers = [
            _customer(code="001"),
            _customer(code="002", name="Existente SA"),
            _customer(code="003", name="Error SA"),
        ]
        result = push_customers_to_erpnext(customers, client)

        assert result.created == 1
        assert result.updated == 1
        assert result.failed == 1
        assert result.total == 3

    def test_inactive_customer_creates_with_disabled_1(self):
        client = self._mock_client(find_return=None)

        push_customers_to_erpnext([_customer(is_active=False)], client)

        doc_sent = client.create_doc.call_args[0][1]
        assert doc_sent["disabled"] == 1

    def test_inactive_existing_customer_updates_with_disabled_1(self):
        client = self._mock_client(
            find_return={"name": "Ferretería Lomas SA", "si_tango_code": "001", "disabled": 0}
        )

        push_customers_to_erpnext([_customer(is_active=False)], client)

        doc_sent = client.patch_doc.call_args[0][2]
        assert doc_sent["disabled"] == 1
