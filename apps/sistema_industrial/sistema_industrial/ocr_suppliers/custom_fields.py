"""Custom fields del módulo OCR proveedores.

Se crean de forma **idempotente** en cada `bench migrate` (via hook `after_migrate`
en hooks.py). Es la forma reproducible y versionada de declarar custom fields
(a diferencia de `si_tango_id`, que se creó ad-hoc en producción y no está en el repo).
"""
from __future__ import annotations

from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

# Definición declarativa de los custom fields del módulo.
OCR_CUSTOM_FIELDS: dict[str, list[dict]] = {
    "Supplier": [
        {
            "fieldname": "si_ocr_layout",
            "label": "OCR Layout (aprendido)",
            "fieldtype": "JSON",
            "insert_after": "supplier_details",
            "read_only": 1,
            "no_copy": 1,
            "description": (
                "Zonas/posiciones de la factura aprendidas por el OCR de proveedores, "
                "en JSON. Lo escribe y lee el módulo ocr_suppliers (aprendizaje por CUIT). "
                "Vacío hasta la primera pasada de aprendizaje."
            ),
        }
    ],
}


def ensure_ocr_custom_fields() -> None:
    """Crea/actualiza los custom fields del OCR de forma idempotente.

    Llamado desde `after_migrate` (hooks.py). Correr varias veces es seguro:
    `create_custom_fields` con `update=True` no duplica ni pisa datos existentes.
    """
    create_custom_fields(OCR_CUSTOM_FIELDS, ignore_validate=True)
