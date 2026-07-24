"""
SEAM del motor OCR — implementa el contrato acordado con la orquestación (Atlas)
y las firmas puras de Nova (CONTRATO_INTEGRACION_OCR_MVP.md §5 / OCR_PAGINA_CONTRATO.md §3).

Funciones PURAS (archivo → estructura). NO hacen matching contra ERPNext ni escriben
nada (eso lo hace la orquestación). Respetan Regla 8.

  extract_invoice(file_path, options=None) -> dict   ← seam de Atlas (§3)
  read_qr(file_path) -> dict                          ← firma de Nova (§5)
  parse_lines(file_path, layout=None) -> list         ← firma de Nova (§5)
"""
from __future__ import annotations

import os

from .engine import FacturaTableReader


class _CaptureStore:
    """Store liviano por-request: entrega el layout conocido (si options lo trae) y
    captura lo aprendido, sin persistir en disco/DB. La persistencia real
    (Supplier.si_ocr_layout, decisión de Forge) la hace la orquestación con
    meta['layout_learned']."""

    def __init__(self, layout_por_cuit=None):
        self._in = {_norm(k): v for k, v in (layout_por_cuit or {}).items()}
        self.learned = {}

    def obtener_layout(self, cuit):
        return self._in.get(_norm(cuit))

    def guardar_layout(self, cuit, proveedor, page_w, page_h,
                       y0_pct, y1_pct, x0_pct, x1_pct, es_pdf_nativo, necesita_ocr):
        self.learned[_norm(cuit)] = {
            "proveedor": proveedor, "page_w": page_w, "page_h": page_h,
            "y0_pct": y0_pct, "y1_pct": y1_pct, "x0_pct": x0_pct, "x1_pct": x1_pct,
            "es_pdf_nativo": bool(es_pdf_nativo), "necesita_ocr": bool(necesita_ocr),
        }

    def obtener_qr_cache(self, cuit):
        return None

    def guardar_qr_cache(self, cuit, proveedor, datos_json):
        pass


def extract_invoice(file_path, options=None):
    """Extrae proveedor + líneas de una factura (PDF/imagen). PURA.
    options:
      - layout_por_cuit: {cuit: {y0_pct,y1_pct,x0_pct,x1_pct,...}} layout aprendido previo
        (p.ej. de Supplier.si_ocr_layout) para modo dirigido.
    Devuelve la forma de OCR_PAGINA_CONTRATO §3."""
    options = options or {}
    warnings = []
    reader = FacturaTableReader(base=_CaptureStore(options.get("layout_por_cuit")))

    try:
        items, debug, datos = reader.analizar(file_path, aprender=True)
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            f"Falta dependencia OCR en el server ({e}). Instalar tesseract-ocr / "
            f"PyMuPDF / opencv-python-headless / pyzbar / numpy / pillow.")

    lineas = []
    for it in items:
        lineas.append({
            "codigo_proveedor": it.get("codigo_proveedor", "") or "",
            "codigo_barras": it.get("codigo_barras", "") or "",
            "descripcion": it.get("descripcion", "") or "",
            "cantidad": _f(reader.parse_decimal(it.get("cantidad"))),
            "precio_unitario": _f(reader.parse_decimal(it.get("precio"))),
            # IVA % del renglón (el engine lo calcula) → contrato de línea. De acá lo
            # toma la orquestación (Atlas) para guardarlo en Item.si_iva_pct, que a su
            # vez llena la columna "Código de IVA" del Excel de importación a Tango.
            "iva_pct": _f(reader.parse_decimal(it.get("iva"))),
            "raw_text": it.get("linea_detectada", "") or "",
        })

    store = reader._base
    cuit = datos.get("cuit_proveedor", "") or ""
    layout_cuit = store.learned.get(_norm(cuit)) if cuit else None
    ext = os.path.splitext(file_path)[1].lower()
    # es_pdf_nativo/necesita_ocr: SIEMPRE bool (contrato de Atlas). Si aprendimos
    # layout usamos su flag; si no, aproximamos por extensión.
    if layout_cuit:
        es_pdf_nativo = bool(layout_cuit["es_pdf_nativo"])
        necesita_ocr = bool(layout_cuit["necesita_ocr"])
    else:
        es_pdf_nativo = (ext == ".pdf")
        necesita_ocr = (ext != ".pdf")
    page_ref = None
    if debug:
        page_ref = {"w": debug[0].get("page_w"), "h": debug[0].get("page_h")}
    if not items:
        warnings.append("No se detectaron renglones de artículos (layout desconocido o factura ilegible).")
    if not cuit:
        warnings.append("No se pudo determinar el CUIT del proveedor (¿sin QR AFIP legible?).")

    return {
        "proveedor": {"cuit": cuit, "nombre": datos.get("proveedor", "") or ""},
        "lineas": lineas,
        "meta": {
            "es_pdf_nativo": es_pdf_nativo,
            "necesita_ocr": necesita_ocr,
            "page_ref": page_ref,
            "warnings": warnings,
            "fuente_encabezado": "qr" if datos.get("_datos_qr") else "texto",
            "layout_learned": store.learned,   # {cuit: {zonas...}} para persistir en Supplier.si_ocr_layout
            "clave_factura": datos.get("clave", ""),
            "tipo": datos.get("tipo", ""),
            "numero_completo": datos.get("numero_completo", ""),
            "fecha": datos.get("fecha", ""),
            "total": datos.get("total", ""),
        },
    }


def read_qr(file_path):
    """QR AFIP → {cuit, tipo, punto_venta, numero, numero_completo, fecha, importe_total, fuente} o {}."""
    return FacturaTableReader().leer_qr_afip(file_path)


def parse_lines(file_path, layout=None):
    """Líneas parseadas (sin matching). `layout` opcional: {cuit: {...}} para modo dirigido."""
    return extract_invoice(file_path, {"layout_por_cuit": layout} if layout else None)["lineas"]


def _norm(cuit):
    import re
    return re.sub(r"\D", "", str(cuit or ""))


def _f(v):
    try:
        return float(v) if v is not None else 0.0
    except Exception:
        return 0.0
