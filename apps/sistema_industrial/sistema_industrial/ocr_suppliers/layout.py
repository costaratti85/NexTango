"""Helpers de lectura/escritura del layout aprendido del OCR (`Supplier.si_ocr_layout`).

El OCR aprende, por proveedor, dónde caen los campos en su factura (la "experiencia
de scaneo") y lo guarda como JSON en el custom field `si_ocr_layout` del Supplier
(creado por `ocr_suppliers.custom_fields`). Estos helpers estandarizan el acceso
para que el motor OCR no toque el ORM directo ni se preocupe por serializar.

**El OCR es dueño de la FORMA del JSON** (zonas como % de página, page_w/h, flags,
etc.); acá solo se guarda/lee un dict arbitrario. Resolución por CUIT vía
`Supplier.tax_id`.
"""
from __future__ import annotations

import json

import frappe

_FIELD = "si_ocr_layout"


def find_supplier_by_cuit(cuit: str) -> str | None:
    """Devuelve el name del Supplier cuyo `tax_id` == cuit (o None)."""
    if not cuit:
        return None
    return frappe.db.get_value("Supplier", {"tax_id": cuit}, "name")


def get_supplier_layout(supplier: str) -> dict | None:
    """Lee el layout aprendido de un Supplier. None si no hay o el Supplier no existe."""
    if not supplier:
        return None
    raw = frappe.db.get_value("Supplier", supplier, _FIELD)
    return _loads(raw)


def save_supplier_layout(supplier: str, layout: dict) -> None:
    """Guarda (pisa) el layout aprendido de un Supplier.

    Lo llama el OCR **después de procesar cada factura** para persistir/actualizar
    la experiencia de scaneo del proveedor.
    """
    if not supplier:
        raise ValueError("save_supplier_layout: falta el supplier")
    frappe.db.set_value("Supplier", supplier, _FIELD, json.dumps(layout, ensure_ascii=False))


def get_layout_by_cuit(cuit: str) -> dict | None:
    """Atajo: resuelve el Supplier por CUIT y devuelve su layout (None si no hay)."""
    supplier = find_supplier_by_cuit(cuit)
    return get_supplier_layout(supplier) if supplier else None


def save_layout_by_cuit(cuit: str, layout: dict) -> str | None:
    """Atajo: resuelve el Supplier por CUIT y guarda su layout.

    Returns:
        El name del Supplier si se guardó; None si no existe un Supplier con ese CUIT
        (en ese caso el alta del Supplier la decide el humano — Regla 8 —, no este helper).
    """
    supplier = find_supplier_by_cuit(cuit)
    if not supplier:
        return None
    save_supplier_layout(supplier, layout)
    return supplier


def _loads(raw) -> dict | None:
    """Normaliza el valor del campo JSON (puede venir como str o dict según versión)."""
    if not raw:
        return None
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return None
