"""IVA del artículo del OCR: código Tango (para el Excel) + Item Tax Template nativo.

Dos caras del mismo IVA:
  - `si_iva_pct` (custom field) → lo usa `tango_sync.article_export` para llenar la
    columna "Código de IVA" del Excel de importación a Tango (mapeo %→código).
  - **Item Tax Template nativo** (child `taxes` del Item) → para que ERPNext calcule
    el impuesto en la Recepción de Compra / ventas. Es el modo nativo de ERPNext.

⚠️ Hoy solo existen templates genéricos ("Argentina Tax - NXT/HSRS"), no uno por
alícuota. Por eso este helper es **defensivo**: resuelve un template por convención
de nombre o por config, y si no hay uno para esa alícuota devuelve `[]` (no rompe;
el `si_iva_pct` + Excel siguen funcionando). El máster fiscal sigue siendo Tango.

Config (opcional) en site_config: mapear alícuota → nombre de Item Tax Template:
    "ocr_item_tax_templates": {"21": "IVA 21% - NXT", "10.5": "IVA 10,5% - NXT"}
"""
from __future__ import annotations

import frappe


def _pct_key(pct) -> str | None:
    try:
        return "%g" % float(pct)
    except (TypeError, ValueError):
        return None


def get_item_tax_template(pct, company: str | None = None) -> str | None:
    """Devuelve el Item Tax Template para esa alícuota, o None si no hay.

    Orden: (1) config `ocr_item_tax_templates`; (2) por convención de nombre
    ("IVA <pct>%..."); no inventa un genérico (evita asignar la alícuota equivocada).
    """
    key = _pct_key(pct)
    if key is None:
        return None

    configured = (frappe.conf.get("ocr_item_tax_templates") or {})
    name = configured.get(key)
    if name and frappe.db.exists("Item Tax Template", name):
        return name

    # convención de nombre: "IVA 21%..." / "IVA 10,5%..." (coma o punto)
    for pat in (f"IVA {key}%", f"IVA {key.replace('.', ',')}%"):
        found = frappe.db.get_value(
            "Item Tax Template",
            {"name": ["like", f"{pat}%"]} if not company else
            {"name": ["like", f"{pat}%"], "company": company},
            "name",
        )
        if found:
            return found
    return None


def item_tax_rows(pct, company: str | None = None) -> list[dict]:
    """Filas para el child `taxes` del Item (o [] si no hay template para esa alícuota).

    Uso desde el alta del Item (Atlas):
        payload["taxes"] = item_tax_rows(linea.get("iva_pct"), company)
    """
    template = get_item_tax_template(pct, company)
    return [{"item_tax_template": template}] if template else []
