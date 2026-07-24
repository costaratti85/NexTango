"""Consulta de artículos en Tango (STA11) — SOLO LECTURA.

Antes de crear un artículo nuevo desde el OCR, conviene chequear si ya existe en
Tango (aunque todavía no esté en la copia de ERPNext) para no duplicar y para
traer sus datos. Este módulo lee de Tango (GET) y busca por código / código de
barras / descripción.

CERO escritura a Tango. La lista de artículos se cachea en Redis (TTL corto) para
no golpear la API de Tango en cada renglón; se invalida en el sync on-demand
(`tango_sync.api.manual_sync_articles`).
"""
from __future__ import annotations

import logging

import frappe

logger = logging.getLogger(__name__)

_CACHE_KEY = "tango_sync:articles_snapshot"
_CACHE_TTL = 900  # 15 min


def _art_to_dict(a) -> dict:
    return {
        "code": a.code,
        "description": a.description,
        "barcode": a.barcode,
        "uom": a.uom,
        "tango_id": a.tango_id,
        "family": a.family,
        "group": a.group,
        "classification": a.classification,
        "synonym": a.synonym,
    }


def _fetch_articles_cached(force: bool = False) -> list[dict]:
    """Trae los artículos de Tango (cacheados). force=True re-consulta la API."""
    cache = frappe.cache()
    if not force:
        cached = cache.get_value(_CACHE_KEY)
        if cached is not None:
            return cached

    from sistema_industrial.tango_sync.http_client import TangoHTTPClient, make_tango_config_from_env

    config = make_tango_config_from_env()
    if not config.token:
        frappe.throw("APP_INSTANCE_ID no configurado: no se puede consultar Tango.")

    arts = [_art_to_dict(a) for a in TangoHTTPClient(config).get_articles()]
    cache.set_value(_CACHE_KEY, arts, expires_in_sec=_CACHE_TTL)
    logger.info("tango lookup: %d artículos cacheados desde Tango", len(arts))
    return arts


def _norm(s) -> str:
    return " ".join((s or "").upper().split())


def find_tango_article(
    code: str | None = None,
    descripcion: str | None = None,
    barcode: str | None = None,
    force_refresh: bool = False,
) -> dict:
    """¿Existe el artículo en Tango? Busca por código > código de barras > descripción.

    Returns:
        {
            "encontrado": bool,
            "match": "codigo"|"barcode"|"descripcion_exacta"|"descripcion_parcial"|None,
            "articulo": {code, description, barcode, uom, tango_id, family, ...} | None,
        }
    """
    arts = _fetch_articles_cached(force=force_refresh)

    if code:
        c = code.strip()
        for a in arts:
            if a["code"] == c:
                return {"encontrado": True, "match": "codigo", "articulo": a}

    if barcode:
        b = barcode.strip()
        for a in arts:
            if a["barcode"] and a["barcode"] == b:
                return {"encontrado": True, "match": "barcode", "articulo": a}

    if descripcion:
        d = _norm(descripcion)
        if d:
            for a in arts:
                if _norm(a["description"]) == d:
                    return {"encontrado": True, "match": "descripcion_exacta", "articulo": a}
            for a in arts:
                ad = _norm(a["description"])
                if ad and (d in ad or ad in d):
                    return {"encontrado": True, "match": "descripcion_parcial", "articulo": a}

    return {"encontrado": False, "match": None, "articulo": None}


@frappe.whitelist()
def find_tango_article_api(code=None, descripcion=None, barcode=None) -> dict:
    """Wrapper whitelisted del lookup (para la orquestación / UI / debug). Solo lee."""
    return find_tango_article(code=code, descripcion=descripcion, barcode=barcode)
