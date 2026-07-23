"""Export de artículos ERPNext → plantilla de actualización masiva de Tango (STA11).

Espejo inverso de `article_push.py` (que trae Tango→ERPNext). Acá vamos
ERPNext→Tango, para el caso de uso del OCR de proveedores: los artículos de
**ferretería** (prefijo `06-`) que el flujo OCR crea en ERPNext a partir de las
facturas, se bajan a Tango con la plantilla masiva.

ALCANCE Y SEGURIDAD (leer):
- Esta capa es **pura y de solo lectura**: arma las FILAS de datos a partir de los
  Items. **No escribe en Tango, no hace submit, no genera el .xlsx final.**
- El paso final —pegar estas filas en la **plantilla oficial de Tango** (que trae
  81 hojas + `_metadata` con claves que Tango valida) y subirla— es un paso
  **separado y gateado**: es **zona fiscal**, requiere OK de Constantino y depende
  de la prueba "¿Tango pisa o respeta celdas vacías?" (caso A/B) y de si el alta
  de artículo nuevo exige columnas fiscales. Ver
  `coordination/reports/FORGE_PROPUESTA_EXPORT_FERRETERIA_A_TANGO.md`.
- Entrada flexible: acepta un **conjunto puntual de item_codes** (los nuevos del
  OCR) o un filtro por Item Group (default "Ferretería" = todo `06-`).

Contrato de salida por Item:
    {
        "item_code": str,
        "filled": {  <encabezado exacto de la columna Tango>: <valor>, ... },
        "gaps":   [ <encabezados fiscales/TBD que quedan vacíos>, ... ],
    }
"""
from __future__ import annotations

import frappe

# --- Mapeos de ferretería (uniformes, verificados sobre los 50 items 06-) ---

# stock_uom (ERPNext) -> código MEDIDA de Tango. Ferretería es por unidad.
# (KG/METRO/M² no aplican a ferretería; si aparece algo distinto -> gap.)
_UOM_TO_TANGO: dict[str, str] = {
    "Nos": "UNIDAD",
    "Unidad": "UNIDAD",
    "Unit": "UNIDAD",
}

# Encabezados exactos de las columnas de la hoja "Artículos" de la plantilla Tango.
COL_CODIGO = "Código"
COL_DESCRIPCION = "Descripción"
COL_PERFIL = "Perfil"
COL_UM_STOCK1 = "Código de UM de stock 1 (Precios y costos)"
COL_LLEVA_STOCK = "Lleva stock"
COL_ELIMINAR = "Eliminar"

# Columnas fiscales/comerciales que ERPNext no tiene hoy → gaps (se completan
# según la decisión de alcance de Constantino / caso A-B de la plantilla).
_FISCAL_GAPS = [
    "Código de IVA Ventas",
    "Código de IVA Compras",
    "Código de base",
]

_ITEM_FIELDS = [
    "item_code",
    "item_name",
    "item_group",
    "stock_uom",
    "is_stock_item",
    "is_sales_item",
    "is_purchase_item",
    "si_tango_id",
]


def _perfil(is_sales: int, is_purchase: int) -> str:
    """Perfil Tango: A=Compra-Venta, V=Venta, C=Compra, N=Inhabilitado."""
    if is_sales and is_purchase:
        return "A"
    if is_sales:
        return "V"
    if is_purchase:
        return "C"
    return "N"


def select_export_items(
    item_codes: list[str] | None = None,
    item_group: str = "Ferretería",
) -> list[dict]:
    """Resuelve el conjunto de Items a exportar.

    Args:
        item_codes: lista puntual de códigos (los nuevos del OCR). Tiene prioridad.
        item_group: si no se pasan item_codes, filtra por este grupo (default
            "Ferretería" = todo `06-`).

    Returns:
        list[dict] con los campos de `_ITEM_FIELDS`.
    """
    if item_codes:
        filters: dict = {"item_code": ["in", list(item_codes)]}
    else:
        filters = {"item_group": item_group}

    return frappe.get_all(
        "Item",
        filters=filters,
        fields=_ITEM_FIELDS,
        order_by="item_code asc",
        limit_page_length=0,
    )


def build_tango_article_rows(
    item_codes: list[str] | None = None,
    item_group: str = "Ferretería",
) -> list[dict]:
    """Arma las filas Tango para un conjunto de Items (o un grupo).

    PURO / SOLO LECTURA: no escribe nada. Devuelve las filas listas para que el
    paso gateado las pegue en la plantilla oficial de Tango.

    Uso desde el flujo OCR (tras la confirmación humana de los artículos nuevos):
        from sistema_industrial.tango_sync.article_export import build_tango_article_rows
        filas = build_tango_article_rows(item_codes=nuevos_codigos_ocr)
    """
    items = select_export_items(item_codes=item_codes, item_group=item_group)
    rows: list[dict] = []

    for it in items:
        uom_tango = _UOM_TO_TANGO.get(it.get("stock_uom") or "")
        filled: dict = {
            COL_CODIGO: it["item_code"],
            COL_DESCRIPCION: it.get("item_name") or it["item_code"],
            COL_PERFIL: _perfil(it.get("is_sales_item") or 0, it.get("is_purchase_item") or 0),
            # "Lleva stock": la plantilla usa codificación true/false
            COL_LLEVA_STOCK: "true" if it.get("is_stock_item") else "false",
            COL_ELIMINAR: "No",
        }

        gaps = list(_FISCAL_GAPS)
        if uom_tango:
            filled[COL_UM_STOCK1] = uom_tango
        else:
            # unidad inesperada para ferretería → queda como gap explícito
            gaps.append(f"{COL_UM_STOCK1} (unidad ERPNext '{it.get('stock_uom')}' sin mapeo Tango)")

        rows.append({"item_code": it["item_code"], "filled": filled, "gaps": gaps})

    return rows


@frappe.whitelist()
def preview_tango_export(item_codes=None, item_group: str = "Ferretería") -> dict:
    """Wrapper whitelisted de PREVIEW (debug). No escribe nada.

    item_codes puede venir como CSV o JSON por HTTP.
    """
    codes = None
    if item_codes:
        if isinstance(item_codes, str):
            item_codes = item_codes.strip()
            if item_codes.startswith("["):
                codes = frappe.parse_json(item_codes)
            else:
                codes = [c.strip() for c in item_codes.split(",") if c.strip()]
        else:
            codes = list(item_codes)

    rows = build_tango_article_rows(item_codes=codes, item_group=item_group)
    return {
        "count": len(rows),
        "rows": rows,
        "note": (
            "PREVIEW de solo lectura. Generar el .xlsx sobre la plantilla oficial de "
            "Tango y subirlo es un paso separado y gateado (fiscal, OK Constantino)."
        ),
    }
