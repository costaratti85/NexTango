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
    # Dedup de facturas de proveedor (Fase 3, Nova/MSG_036): identidad de la factura
    # "{cuit}-{tipo}-{numero_completo}" en la Recepción de Compra, con ÍNDICE ÚNICO.
    # Las PR nativas (sin OCR) quedan con el campo NULL -> MariaDB permite múltiples
    # NULLs, así que el único no las choca. Solo las PR de OCR llevan un ref no vacío.
    "Purchase Receipt": [
        {
            "fieldname": "factura_proveedor_ref",
            "label": "Factura Proveedor (ref OCR)",
            "fieldtype": "Data",
            "insert_after": "supplier_delivery_note",
            "unique": 1,
            "read_only": 1,
            "no_copy": 1,
            "description": (
                "Identidad de la factura de proveedor '{cuit}-{tipo}-{numero_completo}' "
                "que originó esta recepción. Índice único: impide cargar dos veces la "
                "misma factura (dedup del OCR de proveedores). Vacío en recepciones "
                "cargadas a mano."
            ),
        }
    ],
    # Dedup FÉRREO de la baja de stock por ventas (Fase T5, Nova/MSG_035 D-dedup):
    # identidad única del comprobante de venta de Tango en el Stock Entry, con
    # ÍNDICE ÚNICO. Segunda capa junto al high-water mark: nunca descontar dos veces.
    # Las Stock Entry manuales quedan con el campo NULL (múltiples NULLs permitidos).
    "Stock Entry": [
        {
            "fieldname": "tango_comprobante_ref",
            "label": "Comprobante Tango (ref baja)",
            "fieldtype": "Data",
            "insert_after": "remarks",
            "unique": 1,
            "read_only": 1,
            "no_copy": 1,
            "description": (
                "Identidad del comprobante de venta de Tango 'tipo-letra-ptovta-numero' "
                "(ej. 'FA-A-0003-00012345') que originó esta baja de stock. Índice único: "
                "impide descontar dos veces el mismo comprobante. Vacío en movimientos "
                "cargados a mano."
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
