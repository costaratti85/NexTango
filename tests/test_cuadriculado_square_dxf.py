"""Tests para cuadriculado square DXF — LWPOLYLINE + flycut zone layers (CypCut capas 0-15)."""

import sys
import math
import shutil
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "sistema_industrial"))

from sistema_industrial.presets.legacy_panel_adapter import (
    _generate_cuadriculado_square_dxf,
    _generate_cuadriculado_square_dxf_files,
    calcular_zonas,
    zona_de_agujero,
)

# Directorio temporal propio (evita el PermissionError sistémico de pytest tmp_path)
_TESTS_TMP = Path(__file__).resolve().parent / "_tmp_cuad_sq"


@pytest.fixture(autouse=True)
def _clean_tmp():
    _TESTS_TMP.mkdir(exist_ok=True)
    yield
    shutil.rmtree(_TESTS_TMP, ignore_errors=True)


def _out(name="test.dxf"):
    return _TESTS_TMP / name


def _make_dxf(**kwargs):
    defaults = dict(
        hole_size_mm=10.0,
        step_x_mm=30.0,
        step_y_mm=30.0,
        sheet_width_mm=200.0,
        sheet_height_mm=150.0,
        margin_mm=20.0,
        output_path=_out(),
    )
    defaults.update(kwargs)
    return _generate_cuadriculado_square_dxf(**defaults)


# ---- calcular_zonas (spec tests) ----

def test_zonas_panel_pequeno():
    # 500×500mm → ceil(500/250)=2 × ceil(500/250)=2 = 4 zonas → 1 DXF
    n_cols, n_rows, zw, zh, total = calcular_zonas(500, 500)
    assert n_cols == 2
    assert n_rows == 2
    assert total == 4


def test_zonas_panel_grande():
    # 1220×2440mm → ceil(1220/250)=5 × ceil(2440/250)=10 = 50 zonas → 4 DXFs
    n_cols, n_rows, zw, zh, total = calcular_zonas(1220, 2440)
    assert n_cols == 5
    assert n_rows == 10
    assert total == 50
    assert math.ceil(total / 16) == 4


def test_asignacion_zona_esquinas():
    # Panel 500×500 con 4 zonas: zona_w=250, zona_h=250
    n_cols, n_rows, zw, zh, _ = calcular_zonas(500, 500)
    assert zona_de_agujero(125, 125, n_cols, n_rows, zw, zh) == 0  # inf-izq
    assert zona_de_agujero(375, 125, n_cols, n_rows, zw, zh) == 1  # inf-der
    assert zona_de_agujero(125, 375, n_cols, n_rows, zw, zh) == 2  # sup-izq
    assert zona_de_agujero(375, 375, n_cols, n_rows, zw, zh) == 3  # sup-der


# ---- resultado struct ----

def test_returns_pierce_count_and_cut_length():
    result = _make_dxf()
    assert "pierce_count" in result
    assert "cut_length_mm" in result
    assert result["pierce_count"] >= 0
    assert result["cut_length_mm"] == pytest.approx(result["pierce_count"] * 4 * 10.0)


def test_known_grid_dimensions():
    # usable = 200-40=160 × 150-40=110; step=30, hole=10
    # cols = floor(160/30)=5; check (4)*30+10=130 ≤ 160 ✓
    # rows = floor(110/30)=3; check (2)*30+10=70 ≤ 110 ✓
    result = _make_dxf()
    assert result["pierce_count"] == 5 * 3


def test_no_holes_when_hole_too_big():
    result = _make_dxf(hole_size_mm=300.0)
    assert result["pierce_count"] == 0
    assert result["cut_length_mm"] == 0.0


# ---- estructura del DXF ----

def test_dxf_file_created():
    _make_dxf()
    assert _out().exists()


def test_dxf_has_contorno_layer():
    import ezdxf
    _make_dxf()
    doc = ezdxf.readfile(str(_out()))
    msp = doc.modelspace()
    layers = {e.dxf.layer for e in msp}
    assert "CONTORNO" in layers


def test_dxf_squares_are_lwpolyline():
    import ezdxf
    _make_dxf()
    doc = ezdxf.readfile(str(_out()))
    msp = doc.modelspace()
    # Holes are on numeric layers (zone % 16), not "CORTE"
    holes = [e for e in msp if e.dxf.layer != "CONTORNO"]
    assert len(holes) == 5 * 3
    for e in holes:
        assert e.dxftype() == "LWPOLYLINE"


def test_dxf_squares_have_4_vertices():
    import ezdxf
    _make_dxf()
    doc = ezdxf.readfile(str(_out()))
    msp = doc.modelspace()
    holes = [e for e in msp if e.dxf.layer != "CONTORNO"]
    for e in holes:
        assert len(list(e)) == 4


def test_dxf_squares_are_closed():
    import ezdxf
    _make_dxf()
    doc = ezdxf.readfile(str(_out()))
    msp = doc.modelspace()
    holes = [e for e in msp if e.dxf.layer != "CONTORNO"]
    for e in holes:
        assert bool(e.closed)


def test_holes_on_numeric_layers():
    """Cada agujero va en una capa numérica (0-15), no en 'CORTE'."""
    import ezdxf
    _make_dxf()
    doc = ezdxf.readfile(str(_out()))
    msp = doc.modelspace()
    hole_layers = {e.dxf.layer for e in msp if e.dxf.layer != "CONTORNO"}
    assert "CORTE" not in hole_layers
    for lyr in hole_layers:
        assert lyr.isdigit(), f"Layer '{lyr}' no es numérico"
        assert 0 <= int(lyr) <= 15


# ---- zone size ----

def test_zone_size_respected():
    """Las zonas se calculan sobre las dimensiones del panel completo."""
    # 930×1540mm → ceil(930/250)=4 cols × ceil(1540/250)=7 rows
    result = _make_dxf(
        hole_size_mm=10.0,
        step_x_mm=20.0,
        step_y_mm=20.0,
        sheet_width_mm=930.0,
        sheet_height_mm=1540.0,
        margin_mm=0.0,
        zone_size_mm=250.0,
        output_path=_out("large.dxf"),
    )
    assert result["zone_cols"] == 4
    assert result["zone_rows"] == 7


# ---- multi-file generation ----

def test_single_zone_produces_one_file():
    """Panel pequeño (≤16 zonas) → 1 archivo DXF."""
    geo = _generate_cuadriculado_square_dxf_files(
        hole_size_mm=10.0, step_x_mm=30.0, step_y_mm=30.0,
        sheet_width_mm=200.0, sheet_height_mm=150.0, margin_mm=20.0,
        output_dir=_TESTS_TMP, stem="small_panel",
    )
    assert geo["n_files"] == 1
    assert len(geo["paths"]) == 1
    assert geo["paths"][0].name == "small_panel.dxf"


def test_large_panel_produces_multiple_files():
    """Panel 1220×2440mm → 50 zonas → 4 archivos flycut."""
    geo = _generate_cuadriculado_square_dxf_files(
        hole_size_mm=10.0, step_x_mm=20.0, step_y_mm=20.0,
        sheet_width_mm=1220.0, sheet_height_mm=2440.0, margin_mm=0.0,
        output_dir=_TESTS_TMP, stem="large_panel",
    )
    assert geo["n_files"] == 4
    assert len(geo["paths"]) == 4
    assert geo["paths"][0].name == "large_panel_flycut_1de4.dxf"
    assert geo["paths"][3].name == "large_panel_flycut_4de4.dxf"
