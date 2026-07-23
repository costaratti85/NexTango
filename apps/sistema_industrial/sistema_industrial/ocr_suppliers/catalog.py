"""Lectura del catálogo de Items desde ERPNext para el matching del OCR de proveedores.

Reemplaza el export manual `Artículos.xlsx` de Tango: el OCR lee el catálogo
directo de ERPNext (in-process vía ORM Frappe) para matchear las líneas de la
factura contra los Items reales.

Principio de diseño (Constantino, 2026-07-23): aprovechar lo nativo de ERPNext y
construir solo el hueco. Acá el hueco es "exponer el catálogo en el formato que
el matcher del OCR necesita"; los datos salen de los DocTypes nativos Item /
Item Barcode / Item Supplier.

Contrato de salida (una fila por Item), coordinado con OCR y Atlas:
    {
        "item_code":      str,            # = COD_STA11 (código Tango y ERPNext)
        "item_name":      str,
        "description":    str | None,
        "item_group":     str,            # categoría (ej. "Ferretería")
        "stock_uom":      str,
        "si_tango_id":    int | None,     # ID interno de Tango (mapeo Tango<->Item)
        "barcodes":       list[str],      # códigos de barras (matching prioritario)
        "supplier_items": list[{          # código con el que cada proveedor lo llama
            "supplier":         str,      # nombre del Supplier
            "supplier_part_no": str,      # código del proveedor (matching prioritario)
        }],
    }
"""
from __future__ import annotations

import frappe

# Campos planos del Item que necesita el matcher del OCR.
_ITEM_FIELDS = [
    "item_code",
    "item_name",
    "description",
    "item_group",
    "stock_uom",
    "si_tango_id",
]


def build_item_catalog(
    item_group: str | None = None,
    tango_only: bool = False,
    include_disabled: bool = False,
) -> list[dict]:
    """Devuelve el catálogo de Items para el matching del OCR.

    Eficiente: 3 queries totales (Items + Item Barcode + Item Supplier), agrupadas
    en memoria. NO hace N+1 (no consulta child tables por Item).

    Args:
        item_group: si se pasa, filtra por ese Item Group (ej. "Ferretería").
        tango_only: si True, solo Items con `si_tango_id` seteado.
        include_disabled: si False (default), excluye Items deshabilitados.

    Returns:
        list[dict] con el contrato documentado en el docstring del módulo.
    """
    filters: dict = {}
    if item_group:
        filters["item_group"] = item_group
    if not include_disabled:
        filters["disabled"] = 0

    items = frappe.get_all(
        "Item",
        filters=filters,
        fields=_ITEM_FIELDS,
        order_by="item_code asc",
        limit_page_length=0,  # 0 = sin límite (el default de Frappe es 20)
    )

    if tango_only:
        items = [it for it in items if it.get("si_tango_id")]

    codes = [it["item_code"] for it in items]
    barcodes_by_item = _group_child("Item Barcode", codes, ["barcode"])
    suppliers_by_item = _group_child("Item Supplier", codes, ["supplier", "supplier_part_no"])

    for it in items:
        code = it["item_code"]
        it["barcodes"] = [
            row["barcode"] for row in barcodes_by_item.get(code, []) if row.get("barcode")
        ]
        it["supplier_items"] = suppliers_by_item.get(code, [])

    return items


def _group_child(child_doctype: str, parent_codes: list[str], fields: list[str]) -> dict[str, list[dict]]:
    """Trae en UNA query las filas de una child table de Item y las agrupa por parent."""
    if not parent_codes:
        return {}

    rows = frappe.get_all(
        child_doctype,
        filters={"parenttype": "Item", "parent": ["in", parent_codes]},
        fields=["parent", *fields],
        limit_page_length=0,
    )

    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row["parent"], []).append({k: row.get(k) for k in fields})
    return grouped


@frappe.whitelist()
def get_item_catalog(item_group: str | None = None, tango_only=0, include_disabled=0) -> list[dict]:
    """Wrapper whitelisted para debug / consumo externo.

    El módulo OCR (server-side) debe llamar a `build_item_catalog()` directo
    (in-process), no este endpoint HTTP. Este wrapper existe para inspección
    manual y para cualquier cliente externo que lo necesite.

    Los flags llegan como texto por HTTP → se castean con int().
    """
    return build_item_catalog(
        item_group=item_group or None,
        tango_only=bool(int(tango_only)),
        include_disabled=bool(int(include_disabled)),
    )
