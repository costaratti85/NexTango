"""Tests para cuadriculado square DXF — LWPOLYLINE + flycut con CUADRADO LATINO.

Cada zona de flycut (≤200×200mm) se asigna a una capa de CypCut con
capa = (col + fila) % 16, de modo que dos zonas de la misma fila o columna nunca
comparten capa y el láser no corta áreas contiguas de forma consecutiva (evita
que el calor desplace la chapa entre pasadas). Todo el panel va en un solo DXF.
"""

import sys
import shutil
from collections import defaultdict
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "sistema_industrial"))

from sistema_industrial.presets.legacy_panel_adapter import (
    _generate_cuadriculado_square_dxf,
    calcular_zonas,
    zona_de_agujero,
    zona_a_capa,
    NUM_CAPAS_CYPCUT,
    ZONE_TARGET_MM,
    CYPCUT_APPID,
)

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


def _zona_capa_map(dxf_path, w_mm, h_mm):
    """Lee el DXF y devuelve {(col_zona, row_zona): capa} a partir de los agujeros."""
    import ezdxf
    n_cols, n_rows, zw, zh, _ = calcular_zonas(w_mm, h_mm)
    doc = ezdxf.readfile(str(dxf_path))
    out = {}
    for e in doc.modelspace():
        if e.dxf.layer == "CONTORNO":
            continue
        pts = list(e.get_points())
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        col = min(int(cx / zw), n_cols - 1)
        row = min(int(cy / zh), n_rows - 1)
        out[(col, row)] = int(e.dxf.layer)
    return out


# ---- calcular_zonas (zonas ≤ 200mm) ----

def test_zonas_target_por_defecto_200():
    assert ZONE_TARGET_MM == 200.0


def test_zonas_panel_pequeno():
    # 500×500 → min(9, ceil(500/200)=3) = 3 × 3 = 9 zonas; cada zona 166.7mm < 200
    n_cols, n_rows, zw, zh, total = calcular_zonas(500, 500)
    assert (n_cols, n_rows, total) == (3, 3, 9)
    assert zw < 200.0 and zh < 200.0


def test_n_areas_por_lado_formula():
    # N_lado = min(14, ceil(lado/200)); cada dimensión independiente
    assert calcular_zonas(1000, 1000)[:2] == (5, 5)    # ceil(1000/200)=5
    assert calcular_zonas(1500, 1500)[:2] == (8, 8)    # ceil(1500/200)=8
    assert calcular_zonas(3000, 3000)[:2] == (14, 14)  # ceil=15 → tope 14
    assert calcular_zonas(1500, 3000)[:2] == (8, 14)   # ancho≠alto


def test_ejemplos():
    # lado 3000 → 14 áreas (tope); lado 1500 → 8 áreas de 187mm
    nc, _, zw, _, _ = calcular_zonas(3000, 3000)
    assert nc == 14 and zw == pytest.approx(3000 / 14, abs=0.5)
    nc, _, zw, _, _ = calcular_zonas(1500, 1500)
    assert nc == 8 and zw == pytest.approx(1500 / 8, abs=0.5)   # 187.5


def test_area_menor_a_200_si_no_capeado():
    # Si ceil(lado/200) ≤ 14, el área queda ≤ 200
    for lado in [1000, 1500, 2799]:
        n = calcular_zonas(lado, lado)[0]
        assert lado / n <= ZONE_TARGET_MM + 1e-6


def test_area_supera_200_cuando_capeado_en_14():
    # >2800mm necesitaría >14 áreas para <200 → capeado a 14 → área > 200 (límite CypCut)
    n_cols, n_rows, zw, zh, _ = calcular_zonas(3000, 3000)
    assert n_cols == 14 and zw > 200.0


# ---- zona_a_capa (cuadrado latino) ----

def test_capa_es_col_mas_fila_mod_14_base_1():
    # CypCut: 14 canales, base 1 → capa = (col+fila)%14 + 1
    assert NUM_CAPAS_CYPCUT == 14
    assert zona_a_capa(0, 0) == 1
    assert zona_a_capa(3, 2) == 6
    assert zona_a_capa(13, 1) == 1   # (14)%14 + 1
    assert zona_a_capa(8, 8) == 3    # (16)%14 + 1


def test_capa_en_rango_1_a_14():
    for c in range(28):
        for r in range(28):
            assert 1 <= zona_a_capa(c, r) <= NUM_CAPAS_CYPCUT


# ---- resultado struct ----

def test_returns_pierce_count_and_cut_length():
    result = _make_dxf()
    # cut = perímetro de los agujeros + contorno del panel
    contorno = 2.0 * (200.0 + 150.0)
    assert result["cut_length_mm"] == pytest.approx(result["pierce_count"] * 4 * 10.0 + contorno)


def test_known_grid_dimensions():
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
    layers = {e.dxf.layer for e in ezdxf.readfile(str(_out())).modelspace()}
    assert "CONTORNO" in layers


def test_todas_las_capas_declaradas_en_tabla():
    """CypCut necesita las capas en la tabla LAYER, no solo como atributo de entidad."""
    import ezdxf
    _make_dxf(
        hole_size_mm=10.0, step_x_mm=40.0, step_y_mm=40.0,
        sheet_width_mm=1000.0, sheet_height_mm=1000.0, margin_mm=20.0,
        output_path=_out("capas.dxf"),
    )
    doc = ezdxf.readfile(str(_out("capas.dxf")))
    usadas = {e.dxf.layer for e in doc.modelspace()}
    declaradas = {l.dxf.name for l in doc.layers}
    assert usadas <= declaradas, f"capas usadas sin declarar en la tabla: {usadas - declaradas}"


def test_holes_on_numeric_layers_1_14():
    import ezdxf
    _make_dxf()
    msp = ezdxf.readfile(str(_out())).modelspace()
    hole_layers = {e.dxf.layer for e in msp if e.dxf.layer != "CONTORNO"}
    assert "CORTE" not in hole_layers
    assert "0" not in hole_layers  # CypCut no usa la capa 0 para flycut
    for lyr in hole_layers:
        assert lyr.isdigit() and 1 <= int(lyr) <= NUM_CAPAS_CYPCUT


# ---- XDATA FS_CYPCUT (lo que CypCut usa para separar capas) ----

def test_appid_fs_cypcut_registrado():
    import ezdxf
    _make_dxf(
        hole_size_mm=10.0, step_x_mm=50.0, step_y_mm=50.0,
        sheet_width_mm=1000.0, sheet_height_mm=1000.0, margin_mm=20.0,
        output_path=_out("xd.dxf"),
    )
    doc = ezdxf.readfile(str(_out("xd.dxf")))
    assert CYPCUT_APPID in doc.appids


def test_cada_agujero_tiene_xdata_con_channel_igual_a_capa():
    import ezdxf
    _make_dxf(
        hole_size_mm=10.0, step_x_mm=50.0, step_y_mm=50.0,
        sheet_width_mm=1000.0, sheet_height_mm=1000.0, margin_mm=20.0,
        output_path=_out("xd.dxf"),
    )
    doc = ezdxf.readfile(str(_out("xd.dxf")))
    n_holes = 0
    for e in doc.modelspace():
        if e.dxf.layer == "CONTORNO":
            continue
        n_holes += 1
        xd = e.get_xdata(CYPCUT_APPID)   # lanza si no existe
        channel = next(xd[i + 1][1] for i, (c, v) in enumerate(xd)
                       if c == 1000 and v == "Channel")
        # el Channel del XDATA debe coincidir con la capa (layer) del agujero
        assert channel == int(e.dxf.layer), f"Channel {channel} != capa {e.dxf.layer}"
    assert n_holes > 0


# ---- un solo archivo, cualquier tamaño ----

def test_panel_grande_un_solo_archivo():
    """Antes se dividía en N bloques; con cuadrado latino todo va en 1 archivo."""
    geo = _make_dxf(
        step_x_mm=20.0, step_y_mm=20.0,
        sheet_width_mm=1220.0, sheet_height_mm=2440.0, margin_mm=0.0,
        output_path=_out("grande.dxf"),
    )
    assert geo["n_files"] == 1
    assert _out("grande.dxf").exists()


# ---- propiedad del cuadrado latino ----

def test_latin_square_sin_repeticion_en_fila_ni_columna():
    """Panel 1500×1500 → 8×8 zonas (cerca del tope 9): ninguna fila ni columna repite capa."""
    _make_dxf(
        hole_size_mm=10.0, step_x_mm=40.0, step_y_mm=40.0,
        sheet_width_mm=1500.0, sheet_height_mm=1500.0, margin_mm=20.0,
        output_path=_out("latin.dxf"),
    )
    zc = _zona_capa_map(_out("latin.dxf"), 1500.0, 1500.0)
    filas, cols = defaultdict(list), defaultdict(list)
    for (c, r), capa in zc.items():
        filas[r].append(capa)
        cols[c].append(capa)
    for r, capas in filas.items():
        assert len(capas) == len(set(capas)), f"fila {r} repite capa"
    for c, capas in cols.items():
        assert len(capas) == len(set(capas)), f"columna {c} repite capa"


def test_latin_square_zonas_adyacentes_distinta_capa():
    """Ninguna zona adyacente (horizontal o vertical) comparte capa."""
    _make_dxf(
        hole_size_mm=10.0, step_x_mm=40.0, step_y_mm=40.0,
        sheet_width_mm=1500.0, sheet_height_mm=1500.0, margin_mm=20.0,
        output_path=_out("adj.dxf"),
    )
    zc = _zona_capa_map(_out("adj.dxf"), 1500.0, 1500.0)
    for (c, r), capa in zc.items():
        for dc, dr in ((1, 0), (0, 1)):
            vecino = zc.get((c + dc, r + dr))
            assert vecino != capa, f"zona ({c},{r}) y vecina comparten capa {capa}"
