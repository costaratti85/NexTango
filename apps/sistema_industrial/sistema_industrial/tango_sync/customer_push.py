"""Sincronización de clientes Tango → ERPNext.

Usa si_tango_code (= COD_GVA14) como clave de lookup para evitar colisiones
por customer_name. Los Customers manuales de ERPNext (sin si_tango_code) no
son tocados.

Prerequisito: Custom Fields si_tango_code (Data) y si_tango_id (Int) deben
existir en el doctype Customer. Crearlos una vez con tools/bootstrap_customer_fields.py
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field as dc_field

from sistema_industrial.erpnext_extensions.client import ERPNextClient
from sistema_industrial.tango_sync.schemas import TangoCustomer

logger = logging.getLogger(__name__)

import re as _re


def _sanitize_phone(raw: str | None) -> str:
    """Extrae el primer número de teléfono de un string de texto libre de Tango.

    Tango almacena teléfonos como "4864-4240 / 4857-0297", "Beatriz 155-123",
    "5279-4800 int 6079 Lucas", "4779-6906    4779-6900", etc.
    ERPNext rechaza todo lo que no sea un solo número limpio.
    """
    if not raw:
        return ""
    # Partir en separadores explícitos primero
    for sep in ("/", ";", "  "):  # doble espacio = segundo número
        raw = raw.split(sep)[0]
    raw = raw.strip()
    # Extraer solo dígitos, +, -, espacios simples, paréntesis desde el inicio
    m = _re.match(r"^[\d\+\-\(\)\. ]+", raw)
    result = m.group(0).strip() if m else ""
    # Eliminar espacios internos extra (ej. "4864 4240" → "4864-4240" no, pero al menos limpiar)
    result = _re.sub(r" {2,}", " ", result).strip()
    # Solo devolver si tiene al menos 6 dígitos (descarta texto puro)
    digits = _re.sub(r"\D", "", result)
    return result if len(digits) >= 6 else ""


def _sanitize_email(raw: str | None) -> str:
    """Toma solo el primer email de un campo que puede tener múltiples (a/b)."""
    if not raw:
        return ""
    # Separadores comunes para múltiples emails en Tango
    for sep in ("/", ";", ",", " "):
        candidate = raw.split(sep)[0].strip()
        if "@" in candidate:
            return candidate
    return raw.strip() if "@" in raw else ""


_VAT_TO_GROUP: dict[str, str] = {
    "CF": "Individual",
    "RI": "Commercial",
    "RS": "Commercial",
    "MO": "Commercial",
    "EX": "Commercial",
}

_VAT_TO_TYPE: dict[str, str] = {
    "CF": "Individual",
}


@dataclass
class CustomerSyncResult:
    created: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[tuple[str, str]] = dc_field(default_factory=list)

    @property
    def total(self) -> int:
        return self.created + self.updated + self.skipped + self.failed


def _build_customer_doc(
    tc: TangoCustomer,
    *,
    default_price_list: str,
    default_customer_group: str,
) -> dict:
    group = _VAT_TO_GROUP.get(tc.vat_condition or "", default_customer_group)
    ctype = _VAT_TO_TYPE.get(tc.vat_condition or "", "Company")
    return {
        "customer_name": tc.name,
        "customer_type": ctype,
        "customer_group": group,
        "territory": "All Territories",
        "tax_id": tc.cuit or "",
        "mobile_no": _sanitize_phone(tc.phone),
        "email_id": _sanitize_email(tc.email),
        "default_price_list": default_price_list,
        "disabled": 0 if tc.is_active else 1,
        "si_tango_code": tc.code,
        "si_tango_id": tc.tango_id,
        "si_tango_discount": tc.discount,
    }


def push_customers_to_erpnext(
    customers: list[TangoCustomer],
    client: ERPNextClient,
    *,
    default_price_list: str = "Precio Standard",
    default_customer_group: str = "Commercial",
) -> CustomerSyncResult:
    """Sincroniza una lista de TangoCustomer hacia ERPNext.

    - Si ya existe un Customer con si_tango_code == tc.code → actualiza (PUT).
    - Si no existe → crea (POST).
    - Clientes sin si_tango_code (manuales de ERPNext) nunca son tocados.
    - Errores individuales no detienen el sync; quedan en result.errors.
    """
    result = CustomerSyncResult()

    for tc in customers:
        try:
            existing = client.find_customer_by_tango_code(tc.code)
            doc = _build_customer_doc(
                tc,
                default_price_list=default_price_list,
                default_customer_group=default_customer_group,
            )

            if existing:
                erpnext_name = existing["name"]
                client.patch_doc("Customer", erpnext_name, doc)
                result.updated += 1
                logger.debug("Actualizado %s (si_tango_code=%s)", erpnext_name, tc.code)
            else:
                client.create_doc("Customer", doc)
                result.created += 1
                logger.debug("Creado %s (si_tango_code=%s)", tc.name, tc.code)

        except Exception as exc:
            result.failed += 1
            result.errors.append((tc.code, str(exc)))
            logger.warning("Error sincronizando cliente %s: %s", tc.code, exc)

    return result
