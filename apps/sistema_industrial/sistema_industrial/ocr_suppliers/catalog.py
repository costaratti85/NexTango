"""Carga del catálogo de Items de ERPNext para el matching OCR.

Trae los Items nativos (item_code, item_name), sus códigos de barra (Item
Barcode) y códigos de proveedor (Item Supplier), normaliza y cachea. El
catálogo cambia poco; se cachea en Redis con TTL para no golpear la DB en cada
factura (server modesto).

Coordinación con Forge: los Items ya están cargados (~2189 con si_tango_id).
Si Forge agrega un campo de "código de proveedor" nativo por Supplier, se suma
acá sin tocar el matcher.
"""
from .item_matcher import build_catalog

try:
    import frappe
except ImportError:  # pragma: no cover
    frappe = None


_CACHE_KEY = "ocr_suppliers:item_catalog"
_CACHE_TTL = 1800  # 30 min


def _fetch_rows() -> list:
    """Lee Items activos + barcodes + códigos de proveedor desde ERPNext."""
    items = frappe.get_all(
        "Item",
        filters={"disabled": 0},
        fields=["name as item_code", "item_name"],
        limit_page_length=0,
    )
    by_code = {it["item_code"]: {**it, "barcodes": [], "supplier_codes": []}
               for it in items}

    # códigos de barra (Item Barcode child)
    try:
        for b in frappe.get_all("Item Barcode",
                                fields=["parent", "barcode"],
                                limit_page_length=0):
            row = by_code.get(b["parent"])
            if row and b.get("barcode"):
                row["barcodes"].append(b["barcode"])
    except Exception:
        pass

    # códigos de proveedor (Item Supplier child: supplier_part_no)
    try:
        for s in frappe.get_all("Item Supplier",
                                fields=["parent", "supplier_part_no"],
                                limit_page_length=0):
            row = by_code.get(s["parent"])
            if row and s.get("supplier_part_no"):
                row["supplier_codes"].append(s["supplier_part_no"])
    except Exception:
        pass

    return list(by_code.values())


def load_catalog(force: bool = False) -> list:
    """Devuelve la lista de CatalogItem (cacheada). force=True re-lee de la DB."""
    if frappe is None:
        return []
    cache = frappe.cache()
    if not force:
        cached = cache.get_value(_CACHE_KEY)
        if cached:
            return build_catalog(cached)
    rows = _fetch_rows()
    cache.set_value(_CACHE_KEY, rows, expires_in_sec=_CACHE_TTL)
    return build_catalog(rows)


def invalidate():
    if frappe is not None:
        frappe.cache().delete_value(_CACHE_KEY)
