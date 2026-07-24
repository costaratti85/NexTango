"""Configuración de stock para el OCR de proveedores (Fase 3): company + warehouse
destino de la Recepción de Compra, y el flip de `is_stock_item` de ferretería.

Nativo-first: la Recepción de Compra (Purchase Receipt) mueve stock solo si el Item
es `is_stock_item=1` y hay un warehouse destino. Acá se resuelven ambas cosas, de
forma **configurable** (sin hardcodear) y con fallbacks seguros.

Config (opcional) por `site_config.json`:
    "ocr_default_company":   "<Company>"     # si falta -> default de usuario / primera
    "ocr_default_warehouse": "<Warehouse>"   # si falta -> heurística por nombre (abajo)
"""
from __future__ import annotations

import frappe

# Preferencias de nombre para elegir el warehouse por defecto si no hay config.
_WAREHOUSE_NAME_HINTS = ("Ferretería", "Ferreteria", "Almacén Principal", "Almacen Principal")
# Almacenes que NUNCA deben ser el default (no son stock real).
_WAREHOUSE_EXCLUDE = ("tránsito", "transito", "transit", "devoluc", "merma", "retazo", "wip", "proceso")


def _is_excluded_warehouse(name: str) -> bool:
    n = (name or "").lower()
    return any(bad in n for bad in _WAREHOUSE_EXCLUDE)


def get_default_company() -> str | None:
    """Company por defecto para la recepción. Configurable; fallback razonable."""
    return (
        frappe.conf.get("ocr_default_company")
        or frappe.defaults.get_user_default("Company")
        or frappe.defaults.get_global_default("company")
        or frappe.db.get_value("Company", {}, "name")
    )


def get_default_warehouse(company: str | None = None) -> str | None:
    """Warehouse destino por defecto de la recepción (configurable).

    Orden: (1) `ocr_default_warehouse` de site_config si existe;
    (2) un warehouse no-grupo de la company cuyo nombre matchee las pistas
    (Ferretería / Almacén Principal); (3) el primer warehouse no-grupo activo.
    """
    company = company or get_default_company()

    configured = frappe.conf.get("ocr_default_warehouse")
    if configured and frappe.db.exists("Warehouse", configured):
        return configured

    for hint in _WAREHOUSE_NAME_HINTS:
        wh = frappe.db.get_value(
            "Warehouse",
            {"company": company, "is_group": 0, "disabled": 0,
             "warehouse_name": ["like", f"%{hint}%"]},
            "name",
        )
        if wh and not _is_excluded_warehouse(wh):
            return wh

    # último recurso: primer almacén de stock REAL (no tránsito/devoluciones/merma/wip)
    for wh in frappe.get_all(
        "Warehouse",
        filters={"company": company, "is_group": 0, "disabled": 0},
        pluck="name",
        order_by="creation asc",
    ):
        if not _is_excluded_warehouse(wh):
            return wh
    return None


def receipt_defaults(company: str | None = None) -> dict:
    """Atajo para el stock-IN (Purchase Receipt): {company, set_warehouse}."""
    company = company or get_default_company()
    return {"company": company, "set_warehouse": get_default_warehouse(company)}


def delivery_defaults(company: str | None = None) -> dict:
    """Atajo para la BAJA (Delivery Note / Stock Entry de ventas): {company, set_warehouse}.

    Usa **el mismo** `get_default_warehouse` que el stock-IN → warehouse destino
    COMPARTIDO entre recepción de compra y baja de ventas (no se duplica config).
    """
    company = company or get_default_company()
    return {"company": company, "set_warehouse": get_default_warehouse(company)}


@frappe.whitelist()
def ensure_ferreteria_stock_tracked(prefix: str = "06-") -> dict:
    """Pone `is_stock_item=1` en los artículos de ferretería que estén en 0.

    Idempotente: solo toca los que están en 0. Seguro: esos Items no tienen
    movimientos de stock (eran no-stock), así que el flip no rompe ledger.
    Lo corre Orbit una vez en el deploy (o vía bench execute). NO lo corre Forge.

    Returns: {"updated": int, "item_codes": [...]}.
    """
    codes = frappe.get_all(
        "Item",
        filters={"item_code": ["like", prefix + "%"], "is_stock_item": 0},
        pluck="name",
    )
    for code in codes:
        frappe.db.set_value("Item", code, "is_stock_item", 1)
    frappe.db.commit()
    return {"updated": len(codes), "item_codes": codes}
