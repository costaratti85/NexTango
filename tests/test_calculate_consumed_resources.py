"""Tests para calculate_consumed_resources — modelo del PIERCE prescripto (Constantino,
2026-07-14): 3s sin flycut / 1s con flycut, universal, NO calibrado por regresión.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "sistema_industrial"))

from sistema_industrial.presets.legacy_panel_adapter import (
    calculate_consumed_resources,
    PIERCE_SECONDS_SIN_FLYCUT,
    PIERCE_SECONDS_CON_FLYCUT,
)

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


def test_prescripto_valores():
    assert PIERCE_SECONDS_SIN_FLYCUT == 3.0
    assert PIERCE_SECONDS_CON_FLYCUT == 1.0


def test_calibrado_sin_flycut_usa_3s_por_pierce():
    r = calculate_consumed_resources(
        cut_length_m=1.0, pierce_count=10, sheet_area_m2=0.09,
        material_entry=MATERIAL_CALIBRADO, travel_length_mm=500.0,
        apto_flycut=False,
    )
    esperado = 0.013372 * 1000.0 + 0.004946 * 500.0 + 3.0 * 10 + 0.0
    assert r["machine_seconds"] == pytest.approx(round(esperado, 1))


def test_calibrado_con_flycut_usa_1s_por_pierce():
    r = calculate_consumed_resources(
        cut_length_m=1.0, pierce_count=10, sheet_area_m2=0.09,
        material_entry=MATERIAL_CALIBRADO, travel_length_mm=500.0,
        apto_flycut=True,
    )
    esperado = 0.013372 * 1000.0 + 0.004946 * 500.0 + 1.0 * 10 + 0.0
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


def test_legacy_sin_flycut_usa_3s_por_pierce_ignora_tiempo_perforacion_tabla():
    r = calculate_consumed_resources(
        cut_length_m=1.0, pierce_count=10, sheet_area_m2=0.09,
        material_entry=MATERIAL_LEGACY, apto_flycut=False,
    )
    esperado_cut = 1000.0 / 280.0
    esperado = esperado_cut + 3.0 * 10
    assert r["machine_seconds"] == pytest.approx(round(esperado, 1))


def test_legacy_con_flycut_usa_1s_por_pierce():
    r = calculate_consumed_resources(
        cut_length_m=1.0, pierce_count=10, sheet_area_m2=0.09,
        material_entry=MATERIAL_LEGACY, apto_flycut=True,
    )
    esperado_cut = 1000.0 / 280.0
    esperado = esperado_cut + 1.0 * 10
    assert r["machine_seconds"] == pytest.approx(round(esperado, 1))


def test_pierce_zero_no_suma_tiempo():
    r = calculate_consumed_resources(
        cut_length_m=1.0, pierce_count=0, sheet_area_m2=0.09,
        material_entry=MATERIAL_CALIBRADO, apto_flycut=False,
    )
    esperado = 0.013372 * 1000.0
    assert r["machine_seconds"] == pytest.approx(round(esperado, 1))
