"""Limpieza de PriceCache + fuente única de precios (MSG_019 / MSG_165).

Tres cosas se testean acá:
  (c) PriceCache.load FALLA RUIDOSAMENTE ante un JSON sin clave "prices"
      (antes devolvía cache vacío en silencio -> bug del $0).
  - El testigo del bug: daily_prices.json (dict plano) -> ahora lanza, no da $0.
  (a) La cotización lee de la FUENTE ÚNICA (daily_prices + SI Precios Globales
      vía calculate_cost/_precio_segundo_laser) y produce un total > 0 real.
"""
import json
import sys
import os
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "sistema_industrial"))

from sistema_industrial.pricing_sync.price_cache import PriceCache, PriceRecord


# ---------------------------------------------------------------- (c) falla ruidosa

def test_load_falla_sin_clave_prices(tmp_path):
    """Un JSON sin 'prices' NO es un PriceCache -> ValueError, no cache vacío."""
    p = tmp_path / "cualquiera.json"
    p.write_text(json.dumps({"foo": 1, "bar": 2}), encoding="utf-8")
    with pytest.raises(ValueError, match="prices"):
        PriceCache.load(p)


def test_load_falla_con_daily_prices_json_TESTIGO_DEL_BUG(tmp_path):
    """TESTIGO del bug del $0: daily_prices.json (dict plano de precio_kg_*) tiene
    el esquema equivocado. Antes -> data.get('prices', []) -> cache VACÍO -> rate 0
    silencioso. Ahora -> excepción ruidosa. Este test existe para que no vuelva."""
    daily = tmp_path / "daily_prices.json"
    daily.write_text(json.dumps({
        "precio_kg_doble_decapada": 8804.0,
        "precio_kg_galvanizado": 9798.0,
        "precio_segundo_maquina": 60.0,
    }), encoding="utf-8")
    with pytest.raises(ValueError) as exc:
        PriceCache.load(daily)
    assert "prices" in str(exc.value)          # mensaje claro del esquema esperado


def test_load_ok_con_esquema_correcto(tmp_path):
    """Con el esquema correcto {'prices': [...]} carga normal."""
    p = tmp_path / "prices.json"
    p.write_text(json.dumps({"prices": [
        {"item_code": "PANEL_DECORATIVO", "unit_price": 1234.5},
    ]}), encoding="utf-8")
    cache = PriceCache.load(p)
    assert cache.get("PANEL_DECORATIVO").amount == 1234.5


def test_save_load_roundtrip(tmp_path):
    p = tmp_path / "rt.json"
    PriceCache({"X": PriceRecord("X", 10.0)}).save(p)
    assert PriceCache.load(p).get("X").amount == 10.0


# ---------------------------------------------- (a) fuente única -> total > 0

def test_cotizacion_de_fuente_unica_da_total_positivo():
    """calculate_cost lee la fuente única (daily_prices por kg + precio por segundo)
    y produce un total > 0 con datos reales. Sin frappe, _precio_segundo_laser
    cae al fallback del propio dict de precios (precio_segundo_maquina)."""
    from sistema_industrial.presets.panel_sales_local_app import calculate_cost
    daily = {
        "precio_kg_doble_decapada": 8804.0,
        "precio_segundo_maquina": 60.0,      # fallback del precio por segundo
    }
    consumed = {"material_kg": 4.686, "machine_seconds": 2181.7, "pierce_count": 632}
    cost = calculate_cost(consumed, "Chapa doble decapada", daily)
    assert cost["costo_material"] > 0
    assert cost["costo_maquina"] > 0
    assert cost["costo_total"] == pytest.approx(
        cost["costo_material"] + cost["costo_maquina"], rel=1e-6)
    assert cost["costo_total"] > 0            # NO es $0


def test_sin_precios_da_cero_pero_no_es_el_bug_del_pricecache():
    """Si el vendedor no cargó precios, el total es 0 — pero eso es un estado
    explícito de la fuente única (dict vacío), no el cache vaciado en silencio."""
    from sistema_industrial.presets.panel_sales_local_app import calculate_cost
    cost = calculate_cost({"material_kg": 5, "machine_seconds": 100}, "Acero", {})
    assert cost["costo_total"] == 0          # visible: faltan precios, no un bug oculto


def test_produccion_no_usa_pricecache():
    """_run_all_batches (camino de producción) ya no instancia PriceCache: el
    precio viene del `cost` del motor (fuente única), no del cache."""
    import inspect
    from sistema_industrial.presets import panel_sales_local_app as mod
    src = inspect.getsource(mod._run_all_batches)
    assert "PriceCache.load" not in src
    assert "price_cache = None" in src
