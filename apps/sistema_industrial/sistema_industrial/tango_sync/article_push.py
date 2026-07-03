"""Sincronización de artículos Tango (STA11) → ERPNext Item.

Idempotente: usa item_code = COD_STA11 como clave natural (es el código de artículo
en Tango y también en ERPNext). No requiere custom fields adicionales para el lookup.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field as dc_field

from sistema_industrial.erpnext_extensions.client import ERPNextClient
from sistema_industrial.tango_sync.schemas import TangoArticle

logger = logging.getLogger(__name__)

_FAMILIA_TO_ITEM_GROUP: dict[str, str] = {
    "01 - PERFILERIA": "Tubos y Perfiles",
    "02 - TUBOS ESTRUCTURALES": "Tubos y Perfiles",
    "04 - MALLAS ACINDAR": "Materiales",
    "05 - METAL DESPLEGADO PESADO": "Chapas y Flejes",
    "06 - FERRETERIA": "Ferretería",
    "07 - CHAPA": "Chapas y Flejes",
    "50 - GRUPO B&D": "Insumos",
}
_DEFAULT_ITEM_GROUP = "Materiales"

_UOM_MAP: dict[str, str] = {
    "unidad": "Nos",
    "UNIDAD": "Nos",
    "kg": "Kg",
    "KG": "Kg",
    "m": "Meter",
    "M": "Meter",
    "m2": "Square Meter",
    "M2": "Square Meter",
}
_DEFAULT_UOM = "Nos"


@dataclass
class ArticleSyncResult:
    created: int = 0
    updated: int = 0
    failed: int = 0
    errors: list[tuple[str, str]] = dc_field(default_factory=list)

    @property
    def total(self) -> int:
        return self.created + self.updated + self.failed


def _map_uom(tango_uom: str | None) -> str:
    if not tango_uom:
        return _DEFAULT_UOM
    return _UOM_MAP.get(tango_uom) or _UOM_MAP.get(tango_uom.upper(), _DEFAULT_UOM)


def _map_item_group(familia: str | None) -> str:
    if not familia:
        return _DEFAULT_ITEM_GROUP
    clean = " ".join(familia.split())
    return _FAMILIA_TO_ITEM_GROUP.get(clean, _DEFAULT_ITEM_GROUP)


def _build_item_doc(ta: TangoArticle) -> dict:
    item_name = " ".join(ta.description.split()) if ta.description else ta.code
    description = item_name
    if ta.synonym:
        clean_syn = " ".join(ta.synonym.split())
        if clean_syn and clean_syn != item_name:
            description = f"{item_name} — {clean_syn}"

    return {
        "item_code": ta.code,
        "item_name": item_name,
        "item_group": _map_item_group(ta.family),
        "stock_uom": _map_uom(ta.uom),
        "is_stock_item": 0,
        "description": description,
    }


def push_articles_to_erpnext(
    articles: list[TangoArticle],
    client: ERPNextClient,
) -> ArticleSyncResult:
    """Sincroniza una lista de TangoArticle hacia ERPNext Item.

    - Si ya existe un Item con item_code == ta.code → actualiza (PUT).
    - Si no existe → crea (POST).
    - Errores individuales no detienen el sync; quedan en result.errors.
    """
    result = ArticleSyncResult()

    for ta in articles:
        try:
            existing = client.get_doc("Item", ta.code)
            doc = _build_item_doc(ta)

            if existing:
                client.patch_doc("Item", ta.code, doc)
                result.updated += 1
                logger.debug("Actualizado %s", ta.code)
            else:
                client.create_doc("Item", doc)
                result.created += 1
                logger.debug("Creado %s (%s)", ta.code, ta.description[:50])

        except Exception as exc:
            result.failed += 1
            result.errors.append((ta.code, str(exc)))
            logger.warning("Error sincronizando artículo %s: %s", ta.code, exc)

    return result
