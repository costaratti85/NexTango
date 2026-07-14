"""Tests para tresbolillo con HEXÁGONOS — flat-top + flycut por áreas (cuadrado latino + XDATA)."""

import sys
import shutil
from collections import defaultdict
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "sistema_industrial"))

from sistema_industrial.presets.legacy_panel_adapter import (
    _generate_tresbolillo_hex_dxf,
    _hexagon_vertices,
    calcular_zonas,
    NUM_CAPAS_CYPCUT,
    CYPCUT_APPID,
)

_TMP = Path(__file__).resolve().parent / "_tmp_hex"


@pytest.fixture(autouse=True)
def _clean_tmp():
    _TMP.mkdir(exist_ok=True)
    yield
    shutil.rmtree(_TMP, ignore_errors=True)


def _gen(**kw):
    defaults = dict(
        hole_diameter_mm=10.0, hole_distance_mm=18.0,
        sheet_width_mm=300.0, sheet_height_mm=300.0, margin_mm=20.0,
        output_path=_TMP / "hex.dxf",
    )
    defaults.update(kw)
    return _generate_tresbolillo_hex_dxf(**defaults)


# ---- geometría del hexágono ----

def test_hexagono_flat_top_6_vertices():
    v = _hexagon_vertices(0.0, 0.0, across_flats=10.0)
    assert len(v) == 6
    # flat-top: dos lados horizontales → across-flats (alto) = 10
    ys = [p[1] for p in v]
    assert max(ys) - min(ys) == pytest.approx(10.0)
    # dos vértices arriba a la misma Y y dos abajo (lados horizontales)
    assert sum(1 for y in ys if y == pytest.approx(5.0)) == 2
    assert sum(1 for y in ys if y == pytest.approx(-5.0)) == 2


# ---- generación ----

def test_genera_hexagonos():
    g = _gen()
    assert g["pierce_count"] > 0
    assert g["n_files"] == 1


def test_cada_hexagono_tiene_6_vertices_y_es_lwpolyline():
    import ezdxf
    _gen()
    msp = ezdxf.readfile(str(_TMP / "hex.dxf")).modelspace()
    hexes = [e for e in msp if e.dxf.layer != "CONTORNO"]
    assert len(hexes) > 0
    for e in hexes:
        assert e.dxftype() == "LWPOLYLINE"
        assert len(list(e.get_points())) == 6
        assert bool(e.closed)


def test_across_flats_igual_al_diametro():
    import ezdxf
    _gen(hole_diameter_mm=12.0)
    msp = ezdxf.readfile(str(_TMP / "hex.dxf")).modelspace()
    e = next(x for x in msp if x.dxf.layer != "CONTORNO")
    ys = [p[1] for p in e.get_points()]
    assert max(ys) - min(ys) == pytest.approx(12.0)


# ---- flycut: XDATA + cuadrado latino ----

def test_appid_y_xdata_channel_por_hexagono():
    import ezdxf
    _gen()
    doc = ezdxf.readfile(str(_TMP / "hex.dxf"))
    assert CYPCUT_APPID in doc.appids
    for e in doc.modelspace():
        if e.dxf.layer == "CONTORNO":
            continue
        xd = e.get_xdata(CYPCUT_APPID)
        channel = next(xd[i + 1][1] for i, (c, v) in enumerate(xd)
                       if c == 1000 and v == "Channel")
        assert channel == int(e.dxf.layer)
        assert 1 <= channel <= NUM_CAPAS_CYPCUT


def test_latin_square_hexagonos_adyacentes_distinta_capa():
    """Panel grande: ninguna zona adyacente comparte capa."""
    import ezdxf
    _gen(sheet_width_mm=1500.0, sheet_height_mm=1500.0, output_path=_TMP / "big.dxf")
    doc = ezdxf.readfile(str(_TMP / "big.dxf"))
    n_cols, n_rows, zw, zh, _ = calcular_zonas(1500.0, 1500.0)
    zc = {}
    for e in doc.modelspace():
        if e.dxf.layer == "CONTORNO":
            continue
        pts = list(e.get_points())
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        col = min(int(cx / zw), n_cols - 1)
        row = min(int(cy / zh), n_rows - 1)
        zc[(col, row)] = int(e.dxf.layer)
    for (c, r), capa in zc.items():
        for dc, dr in ((1, 0), (0, 1)):
            vecino = zc.get((c + dc, r + dr))
            assert vecino != capa, f"zona ({c},{r}) y vecina comparten capa {capa}"


# ---- integración con el adapter (dispatch tresbolillo+hexagon) ----

def test_adapter_dispatch_tresbolillo_hexagon():
    from sistema_industrial.presets.legacy_panel_adapter import LegacyPanelAdapter, LegacyPanelRunRequest
    req = LegacyPanelRunRequest(
        preset_code="hex", preset_name="Tresbolillo Hex", material="chapa",
        thickness_mm=2.0, width_mm=300.0, height_mm=300.0, quantity=1,
        output_dxf_path=_TMP / "adapter.dxf",
        pattern_type="tresbolillo", hole_shape="hexagon",
        hole_diameter_mm=10.0, hole_distance_mm=18.0, margin_mm=20.0,
    )
    result = LegacyPanelAdapter().run(req)
    assert (_TMP / "adapter.dxf").exists()
    assert result.legacy_result_raw["generator"] == "tresbolillo_hex_direct"
    assert result.calculated_resources[0]["pierce_count"] > 0
