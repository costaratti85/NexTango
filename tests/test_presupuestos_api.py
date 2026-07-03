"""Tests para erpnext_extensions/api.py — list_presupuestos y get_presupuesto."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "sistema_industrial"))

from unittest.mock import MagicMock, patch

import pytest

from sistema_industrial.erpnext_extensions.api import get_presupuesto, list_presupuestos


class TestListPresupuestos:
    def _mock_client(self, return_value):
        client = MagicMock()
        client.list_docs.return_value = return_value
        return client

    def test_filters_by_panel_dec_item(self):
        with patch(
            "sistema_industrial.erpnext_extensions.client.ERPNextClient"
        ) as MockClient:
            instance = MockClient.return_value
            instance.list_docs.return_value = []

            list_presupuestos()

            call_kwargs = instance.list_docs.call_args
            filters_used = call_kwargs[1]["filters"] if call_kwargs[1] else call_kwargs[0][1]
            assert ["Quotation Item", "item_code", "=", "PANEL-DEC"] in filters_used

    def test_adds_customer_filter_when_provided(self):
        with patch(
            "sistema_industrial.erpnext_extensions.client.ERPNextClient"
        ) as MockClient:
            instance = MockClient.return_value
            instance.list_docs.return_value = []

            list_presupuestos(customer="Ferretería SA")

            call_kwargs = instance.list_docs.call_args
            filters_used = call_kwargs[1]["filters"] if call_kwargs[1] else call_kwargs[0][1]
            assert ["party_name", "=", "Ferretería SA"] in filters_used

    def test_no_customer_filter_when_not_provided(self):
        with patch(
            "sistema_industrial.erpnext_extensions.client.ERPNextClient"
        ) as MockClient:
            instance = MockClient.return_value
            instance.list_docs.return_value = []

            list_presupuestos()

            call_kwargs = instance.list_docs.call_args
            filters_used = call_kwargs[1]["filters"] if call_kwargs[1] else call_kwargs[0][1]
            assert len(filters_used) == 1

    def test_returns_list_from_client(self):
        expected = [
            {"name": "SAL-QTN-2026-00001", "grand_total": 30000},
            {"name": "SAL-QTN-2026-00002", "grand_total": 15000},
        ]
        with patch(
            "sistema_industrial.erpnext_extensions.client.ERPNextClient"
        ) as MockClient:
            MockClient.return_value.list_docs.return_value = expected

            result = list_presupuestos()

            assert result == expected

    def test_custom_limit_is_passed(self):
        with patch(
            "sistema_industrial.erpnext_extensions.client.ERPNextClient"
        ) as MockClient:
            instance = MockClient.return_value
            instance.list_docs.return_value = []

            list_presupuestos(limit=10)

            call_kwargs = instance.list_docs.call_args
            limit_used = call_kwargs[1].get("limit") or call_kwargs[0][3]
            assert limit_used == 10


class TestGetPresupuesto:
    def test_returns_doc_when_found(self):
        expected = {"name": "SAL-QTN-2026-00001", "grand_total": 30000, "status": "Draft"}
        with patch(
            "sistema_industrial.erpnext_extensions.client.ERPNextClient"
        ) as MockClient:
            MockClient.return_value.get_doc.return_value = expected

            result = get_presupuesto("SAL-QTN-2026-00001")

            assert result == expected
            MockClient.return_value.get_doc.assert_called_once_with(
                "Quotation", "SAL-QTN-2026-00001"
            )

    def test_raises_key_error_when_not_found(self):
        with patch(
            "sistema_industrial.erpnext_extensions.client.ERPNextClient"
        ) as MockClient:
            MockClient.return_value.get_doc.return_value = None

            with pytest.raises(KeyError, match="SAL-QTN-2026-99999"):
                get_presupuesto("SAL-QTN-2026-99999")
