"""Tests para calculate_consumed_resources — modelo del PIERCE (Constantino):
SIN_FLYCUT derivado por regresión de Batería 2 (2026-07-23, ver
tools/derivar_pierce_seconds.py); CON_FLYCUT fijado por Constantino (0.2s).
Los tests usan los símbolos importados, no los valores numéricos hardcodeados,
para no romper si el valor derivado se recalibra con más datos.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "sistema_industrial"))

from sistema_industrial.presets.legacy_panel_adapter import (
    calculate_consumed_resources,
    calculate_pierce_count,
    PIERCE_SECONDS_SIN_FLYCUT,
    PIERCE_SECONDS_CON_FLYCUT,
)


class _FakeFigure:
    """Agujero: tiene .entities (como Figure/Piece del motor legacy)."""
    def __init__(self):
        self.entities = []


class Polyline:
    """Contorno/borde: SIN .entities -- se detecta por nombre de clase 'Polyline'."""
    pass


class _OtraClaseSinEntities:
    """Cualquier otra cosa sin .entities y que NO se llame Polyline -- no debe
    contarse como pierce (para no inflar el conteo con basura inesperada)."""
    pass

# Coeficientes reales de la Batería 2 (α, β, δ calibrados; γ ya no se lee de acá).
MATERIAL_CALIBRADO = {
    "densidad_kg_m2": 16.03,
    "consumible_por_perforacion": 0.0,
    "laser_a_s_per_mm": 0.013372,
    "laser_b_s_per_hole": 0.004946,
    "laser_c_s_per_m2": 1.1852,   # valor viejo, presente en el dict — debe ser IGNORADO
    "laser_d_base_s": 0.0,
}

MATERIAL_LEGACY = {
    "densidad_kg_m2": 4.48,
    "consumible_por_perforacion": 0.0,
    "velocidad_corte_mm_s": 280.0,
    "tiempo_perforacion_s": 0.10,   # valor viejo por-material — debe ser IGNORADO
}


def test_valores_pierce():
    assert PIERCE_SECONDS_SIN_FLYCUT == 0.72
    assert PIERCE_SECONDS_CON_FLYCUT == 0.2


def test_calibrado_sin_flycut_usa_gamma_derivado_por_pierce():
    r = calculate_consumed_resources(
        cut_length_m=1.0, pierce_count=10, sheet_area_m2=0.09,
        material_entry=MATERIAL_CALIBRADO, travel_length_mm=500.0,
        apto_flycut=False,
    )
    esperado = 0.013372 * 1000.0 + 0.004946 * 500.0 + PIERCE_SECONDS_SIN_FLYCUT * 10 + 0.0
    assert r["machine_seconds"] == pytest.approx(round(esperado, 1))


def test_calibrado_con_flycut_usa_02s_por_pierce():
    r = calculate_consumed_resources(
        cut_length_m=1.0, pierce_count=10, sheet_area_m2=0.09,
        material_entry=MATERIAL_CALIBRADO, travel_length_mm=500.0,
        apto_flycut=True,
    )
    esperado = 0.013372 * 1000.0 + 0.004946 * 500.0 + PIERCE_SECONDS_CON_FLYCUT * 10 + 0.0
    assert r["machine_seconds"] == pytest.approx(round(esperado, 1))


def test_calibrado_ignora_laser_c_s_per_m2_del_material_entry():
    """El campo viejo (1.1852) NO debe influir — el pierce es universal, no por material."""
    con_c_alto = dict(MATERIAL_CALIBRADO, laser_c_s_per_m2=99.0)
    r1 = calculate_consumed_resources(
        cut_length_m=1.0, pierce_count=10, sheet_area_m2=0.09,
        material_entry=MATERIAL_CALIBRADO, apto_flycut=False,
    )
    r2 = calculate_consumed_resources(
        cut_length_m=1.0, pierce_count=10, sheet_area_m2=0.09,
        material_entry=con_c_alto, apto_flycut=False,
    )
    assert r1["machine_seconds"] == r2["machine_seconds"]


def test_apto_flycut_default_false():
    r_default = calculate_consumed_resources(
        cut_length_m=1.0, pierce_count=10, sheet_area_m2=0.09,
        material_entry=MATERIAL_CALIBRADO,
    )
    r_explicito = calculate_consumed_resources(
        cut_length_m=1.0, pierce_count=10, sheet_area_m2=0.09,
        material_entry=MATERIAL_CALIBRADO, apto_flycut=False,
    )
    assert r_default["machine_seconds"] == r_explicito["machine_seconds"]


def test_legacy_sin_flycut_usa_gamma_derivado_ignora_tiempo_perforacion_tabla():
    r = calculate_consumed_resources(
        cut_length_m=1.0, pierce_count=10, sheet_area_m2=0.09,
        material_entry=MATERIAL_LEGACY, apto_flycut=False,
    )
    esperado_cut = 1000.0 / 280.0
    esperado = esperado_cut + PIERCE_SECONDS_SIN_FLYCUT * 10
    assert r["machine_seconds"] == pytest.approx(round(esperado, 1))


def test_legacy_con_flycut_usa_02s_por_pierce():
    r = calculate_consumed_resources(
        cut_length_m=1.0, pierce_count=10, sheet_area_m2=0.09,
        material_entry=MATERIAL_LEGACY, apto_flycut=True,
    )
    esperado_cut = 1000.0 / 280.0
    esperado = esperado_cut + PIERCE_SECONDS_CON_FLYCUT * 10
    assert r["machine_seconds"] == pytest.approx(round(esperado, 1))


def test_pierce_zero_no_suma_tiempo():
    r = calculate_consumed_resources(
        cut_length_m=1.0, pierce_count=0, sheet_area_m2=0.09,
        material_entry=MATERIAL_CALIBRADO, apto_flycut=False,
    )
    esperado = 0.013372 * 1000.0
    assert r["machine_seconds"] == pytest.approx(round(esperado, 1))


# ------------------------------------------ calculate_pierce_count (contorno incluido)
#
# Constantino confirmó (2026-07-23): el contorno de cada pieza TAMBIÉN necesita su
# propio pierce -- es la convención que dio el ajuste más ajustado (spread 1.5% vs
# 4.2%) contra los 12 paneles reales de Batería 2 (ver derivar_pierce_seconds.py).

def test_pierce_count_agujeros_mas_un_contorno():
    items = [_FakeFigure(), _FakeFigure(), _FakeFigure(), Polyline()]
    assert calculate_pierce_count(items) == 4  # 3 agujeros + 1 contorno


def test_pierce_count_sin_agujeros_solo_contorno():
    items = [Polyline()]
    assert calculate_pierce_count(items) == 1


def test_pierce_count_sin_geometria_da_cero():
    assert calculate_pierce_count([]) == 0


def test_pierce_count_multiples_polylines_cuentan_cada_una():
    """Si el motor emite más de un Polyline (ej. un border path aparte del
    contorno), cada uno necesita su propio pierce -- no se hardcodea un +1
    fijo, se cuenta lo que realmente hay."""
    items = [_FakeFigure(), Polyline(), Polyline()]
    assert calculate_pierce_count(items) == 3


def test_pierce_count_ignora_objetos_sin_entities_que_no_son_polyline():
    items = [_FakeFigure(), _OtraClaseSinEntities()]
    assert calculate_pierce_count(items) == 1
