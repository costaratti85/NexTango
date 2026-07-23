"""
Matching multicriterio de líneas OCR contra el catálogo de ERPNext.

Firma pedida por Nova (CONTRATO_INTEGRACION_OCR_MVP §5) y llamada por la
orquestación de Atlas (OCR_PAGINA_CONTRATO §3):

    match_lines(lineas, catalog) -> list

- `catalog`: filas en el formato de Forge `build_item_catalog()` (MSG_005):
    {item_code, item_name, description, item_group, stock_uom, si_tango_id,
     barcodes: [str], supplier_items: [{supplier, supplier_part_no}]}
- `lineas`: las de `extraction.extract_invoice(...)["lineas"]`.
- PURA: no lee ERPNext ni escribe nada. El catálogo se lo pasa la orquestación.

Prioridad (como la V9): código de barras / código de proveedor > descripción.
El `match` de salida es un SUPERSET que sirve a los dos contratos en juego:
  score 0..100 + reason (Atlas)  ·  confidence 0..1 + status + criterio (Nova/Vega).
"""
from __future__ import annotations

from .engine import Catalogo, UMBRAL_CONFIANZA_DEFAULT

# Umbral de auto-match (coincide con V9 y con AUTO_MIN de Atlas)
UMBRAL_AUTO = UMBRAL_CONFIANZA_DEFAULT  # 82
# Umbrales de semáforo (Nova §4)
VERDE_MIN = 85
AMARILLO_MIN = 50


def _catalogo_desde_forge(catalog_rows):
    arts = []
    for r in catalog_rows or []:
        barcodes = [str(b).strip() for b in (r.get("barcodes") or []) if str(b).strip()]
        partes = [str(si.get("supplier_part_no") or "").strip()
                  for si in (r.get("supplier_items") or []) if str(si.get("supplier_part_no") or "").strip()]
        desc_adic = " ".join(filter(None, [str(r.get("description") or "")] + barcodes + partes))
        arts.append({
            "codigo": str(r.get("item_code") or "").strip(),
            "descripcion": str(r.get("item_name") or "").strip(),
            "desc_adic": desc_adic.strip(),
            "sinonimo": partes[0] if partes else "",
            "codigo_barras": barcodes[0] if barcodes else "",
        })
    cat = Catalogo()
    cat.cargar_desde_articulos(arts)
    return cat


def _criterio(metodo):
    m = (metodo or "").lower()
    if "barras" in m or "barcode" in m:
        return "barcode"
    if "descripcion" in m and "codigo proveedor" not in m:
        return "descripcion"
    if "codigo" in m or "sinonimo" in m or "proveedor" in m:
        return "codigo"
    return None


def _status(score):
    if score >= VERDE_MIN:
        return "verde"
    if score >= AMARILLO_MIN:
        return "amarillo"
    return "rojo"


def _match_dict(art, metodo, score):
    return {
        "item_code": art["codigo"],
        "item_name": art["descripcion"],
        "score": int(score),
        "confidence": round(score / 100.0, 3),
        "criterio": _criterio(metodo),
        "reason": metodo or "",
    }


def match_lines(lineas, catalog, umbral=UMBRAL_AUTO):
    cat = _catalogo_desde_forge(catalog)
    out = []
    for idx, ln in enumerate(lineas):
        cod_prov = ln.get("codigo_proveedor", "") or ""
        cod_barras = ln.get("codigo_barras", "") or ""
        desc = ln.get("descripcion", "") or ""

        art, metodo, score = cat.buscar(codigo_proveedor=cod_prov, codigo_barras=cod_barras,
                                        descripcion=desc, umbral=umbral)
        candidatos = cat.buscar_candidatos(codigo_proveedor=cod_prov, codigo_barras=cod_barras,
                                           descripcion=desc, top=5)
        best_score = candidatos[0][2] if candidatos else (score if art else 0)

        match = _match_dict(art, metodo, score) if art else None
        out.append({
            "idx": idx,
            "codigo_proveedor": cod_prov,
            "codigo_barras": cod_barras,
            "descripcion": desc,
            "cantidad": ln.get("cantidad"),
            "precio_unitario": ln.get("precio_unitario"),
            "raw_text": ln.get("raw_text", ""),
            "match": match,
            "confianza": int(best_score),
            "status": _status(best_score),
            "candidatos": [_match_dict(c[0], c[1], c[2]) for c in candidatos],
        })
    return out
