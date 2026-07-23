"""Persistencia de la "experiencia de scaneo" del OCR por proveedor (Fase 2).

Guarda/lee el layout aprendido (zonas de la factura por CUIT) en el custom field
**`Supplier.si_ocr_layout`** (JSON, creado por Forge en `after_migrate`). Es el
mismo aprendizaje por proveedor de la V9, pero persistido en ERPNext en vez de la
SQLite del programa de escritorio.

Flujo (lo cablea Atlas en `_procesar_job`, cambiando UNA línea):
    extract_invoice(path)  →  extract_invoice_learning(path)

`extract_invoice_learning`:
  1. inyecta un `layout_loader` → el motor, al leer el QR y obtener el CUIT, carga
     el layout de ese Supplier (OCR DIRIGIDO: lee mejor la zona de artículos).
  2. corre `extract_invoice` (puro; sin frappe adentro).
  3. persiste lo aprendido (`meta.layout_learned`) en `Supplier.si_ocr_layout`,
     incrementando `veces_procesado` (el modo dirigido se activa con ≥2, como la V9).

Fronteras: NO crea Suppliers (si el CUIT no tiene Supplier, no persiste — zona
fiscal/Tango). El campo es interno del OCR; NO escribe stock/precios/Tango (Regla 8).
Si el custom field todavía no existe (Forge sin mergear / sin `bench migrate`),
todo degrada a no-op silencioso → el OCR sigue andando, aprendiendo de cero.
"""
from __future__ import annotations

import json
import re

from .extraction import extract_invoice

_FIELD = "si_ocr_layout"


def _norm(cuit) -> str:
    return re.sub(r"\D", "", str(cuit or ""))


def _find_supplier(cuit: str):
    """name del Supplier cuyo tax_id == CUIT (clave nativa), o None."""
    import frappe
    cn = _norm(cuit)
    if not cn:
        return None
    name = frappe.db.get_value("Supplier", {"tax_id": cn}, "name")
    if name:
        return name
    # fallback: tax_id guardado con guiones/espacios
    for s in frappe.get_all("Supplier", fields=["name", "tax_id"], limit_page_length=0):
        if _norm(s.get("tax_id")) == cn:
            return s["name"]
    return None


def _leer_campo(name: str):
    """Devuelve el dict guardado en Supplier.si_ocr_layout, o None (tolera field ausente)."""
    import frappe
    try:
        raw = frappe.db.get_value("Supplier", name, _FIELD)
    except Exception:
        return None  # custom field aún no creado (Forge/bench migrate pendiente)
    if not raw:
        return None
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return None


def load_supplier_layout(cuit: str):
    """Layout aprendido de ese CUIT en la forma que espera el motor
    (`engine.obtener_layout`), o None si no hay zonas todavía."""
    name = _find_supplier(cuit)
    if not name:
        return None
    d = _leer_campo(name)
    if not d or d.get("y0_pct") is None:
        return None
    return {
        "proveedor": d.get("proveedor"),
        "page_w": d.get("page_w"), "page_h": d.get("page_h"),
        "y0_pct": d.get("y0_pct"), "y1_pct": d.get("y1_pct"),
        "x0_pct": d.get("x0_pct"), "x1_pct": d.get("x1_pct"),
        "es_pdf_nativo": bool(d.get("es_pdf_nativo")),
        "necesita_ocr": bool(d.get("necesita_ocr")),
        "veces_procesado": int(d.get("veces_procesado") or 1),
    }


def save_supplier_layout(layout_learned) -> bool:
    """Persiste `meta.layout_learned` ({cuit: {zonas...}}) en Supplier.si_ocr_layout,
    incrementando veces_procesado sobre lo previo. No-op si vacío (modo dirigido no
    re-aprende) o si el Supplier no existe. Devuelve True si escribió algo."""
    if not layout_learned:
        return False
    import frappe
    saved = False
    for cuit, lay in layout_learned.items():
        name = _find_supplier(cuit)
        if not name:
            continue  # sin Supplier: no creamos (zona fiscal)
        prev = _leer_campo(name)
        veces = 1
        if prev:
            try:
                veces = int(prev.get("veces_procesado") or 0) + 1
            except Exception:
                veces = 1
        payload = {
            "version": 1, "cuit": _norm(cuit), "proveedor": lay.get("proveedor"),
            "page_w": lay.get("page_w"), "page_h": lay.get("page_h"),
            "y0_pct": lay.get("y0_pct"), "y1_pct": lay.get("y1_pct"),
            "x0_pct": lay.get("x0_pct"), "x1_pct": lay.get("x1_pct"),
            "es_pdf_nativo": bool(lay.get("es_pdf_nativo")),
            "necesita_ocr": bool(lay.get("necesita_ocr")),
            "veces_procesado": veces,
        }
        try:
            # set_value directo: no dispara save() del Supplier (no molesta a tango_sync)
            frappe.db.set_value("Supplier", name, _FIELD,
                                json.dumps(payload, ensure_ascii=False),
                                update_modified=False)
            saved = True
        except Exception:
            frappe.log_error(f"save_supplier_layout CUIT {cuit}", "ocr_suppliers")
    return saved


def extract_invoice_learning(file_path, options=None):
    """Drop-in de `extract_invoice` con aprendizaje persistido (Fase 2).
    Úsalo desde la orquestación en lugar de `extract_invoice(path)`."""
    opts = dict(options or {})
    opts.setdefault("layout_loader", load_supplier_layout)
    extracted = extract_invoice(file_path, opts)
    try:
        save_supplier_layout((extracted.get("meta") or {}).get("layout_learned"))
    except Exception:
        import frappe
        frappe.log_error("save layout tras extract", "ocr_suppliers")
    return extracted
