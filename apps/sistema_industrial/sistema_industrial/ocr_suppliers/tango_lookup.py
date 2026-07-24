"""Consulta a Tango antes de crear un artículo + check liviano de catálogo.

PURO (sin frappe): recibe un `client` que cumple el protocolo de tango_sync.

1) `consultar_articulo_en_tango(codigo, client)` — antes de dar de alta un Item
   nuevo, preguntar a Tango si el artículo YA existe (por su código). Si existe,
   devolver sus datos para que el humano decida (no duplicar catálogo).

   ⚠️ Requiere que el TangoClient exponga `get_article_by_code(codigo) ->
   TangoArticle | None` (a agregar por Forge en `tango_sync/client.py` +
   `http_client.py`). Si el client no lo soporta todavía, devuelve
   `existe=None` (desconocido) — NO bloquea el flujo.

2) `check_catalogo(catalog_rows)` — sanity liviano del catálogo por corrida
   (cuántos items, con barcode, con código de proveedor, sin nombre).
"""
from __future__ import annotations


def consultar_articulo_en_tango(codigo, client) -> dict:
    """¿Existe el artículo en Tango? -> {existe: bool|None, articulo: dict|None, error?}."""
    cod = str(codigo or "").strip()
    if not cod:
        return {"existe": None, "articulo": None, "error": "codigo vacío"}
    fn = getattr(client, "get_article_by_code", None)
    if not callable(fn):
        # El adapter todavía no expone la consulta puntual → desconocido, no bloquea.
        return {"existe": None, "articulo": None,
                "error": "TangoClient sin get_article_by_code (pendiente Forge)"}
    try:
        art = fn(cod)
    except Exception as exc:  # noqa: BLE001
        return {"existe": None, "articulo": None, "error": f"consulta Tango falló: {exc}"}
    if not art:
        return {"existe": False, "articulo": None}
    return {
        "existe": True,
        "articulo": {
            "code": getattr(art, "code", None),
            "description": getattr(art, "description", None),
            "barcode": getattr(art, "barcode", None),
            "uom": getattr(art, "uom", None),
            "tango_id": getattr(art, "tango_id", None),
        },
    }


def check_catalogo(catalog_rows) -> dict:
    """Sanity liviano del catálogo cargado para el matching."""
    rows = list(catalog_rows or [])
    n = len(rows)

    def _tiene_barcode(r):
        return bool(r.get("barcodes"))

    def _tiene_cod_prov(r):
        # soporta ambos formatos: Forge build_item_catalog (supplier_items)
        # y item_matcher.build_catalog (supplier_codes)
        return bool(r.get("supplier_items") or r.get("supplier_codes"))

    con_barcode = sum(1 for r in rows if _tiene_barcode(r))
    con_cod_prov = sum(1 for r in rows if _tiene_cod_prov(r))
    sin_nombre = sum(1 for r in rows if not str(r.get("item_name", "") or "").strip())

    avisos = []
    if n == 0:
        avisos.append("Catálogo vacío: el matching no va a encontrar nada.")
    if sin_nombre:
        avisos.append(f"{sin_nombre} item(s) sin item_name.")

    return {
        "items": n,
        "con_barcode": con_barcode,
        "con_codigo_proveedor": con_cod_prov,
        "sin_nombre": sin_nombre,
        "ok": n > 0,
        "avisos": avisos,
    }
