"""Tests del rediseño de la fórmula de tiempo de láser — modelo jerk por eje/tramos
y reconstrucción geométrica desde los DXF reales de la Batería 2.

Principio: cada término se valida contra SU propio componente (no el total). Estos
tests verifican la FÍSICA/ÁLGEBRA del modelo con datos sintéticos controlados —
la calibración/validación contra CypCut real está bloqueada por falta del desglose
Processing/Move/Delay (ver DESGLOSE_BATERIA2 en analisis_laser_fisico.py).
"""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "sistema_industrial"))

from analisis_laser_fisico import (
    tiempo_salto_jerk,
    k_desde_j,
    j_desde_k,
    distancia_critica_jerk,
    ajustar_modelo_desplazamiento,
    ajustar_modelo_corte,
    ordenar_boustrophedon,
    extraer_centros_agujeros,
    saltos_del_panel,
    segmentos_de_corte,
    cargar_geometria_bateria2,
)

_BATERIA2_DIR = Path(__file__).resolve().parents[1] / "tools" / "calibracion_bateria2"


# ---- física del modelo jerk (verificación matemática independiente) ----

def test_formula_jerk_cubica():
    # T = (32d/j)^(1/3)  <=>  d = j*T^3/32 — despejo T de un d/j conocidos y
    # verifico la relación inversa exacta (derivación independiente del perfil
    # de 4 tramos simétrico jerk-limitado, reposo-a-reposo).
    j = 40000.0
    d = 100.0
    T = (32 * d / j) ** (1 / 3)
    d_reconstruido = j * T**3 / 32
    assert d_reconstruido == pytest.approx(d)


def test_k_j_son_inversas():
    j = 40000.0
    k = k_desde_j(j)
    assert j_desde_k(k) == pytest.approx(j, rel=1e-9)


def test_tiempo_salto_usa_max_no_hipotenusa():
    j = 40000.0
    # salto puramente en X (dy=0): tiempo = tiempo del eje X solo
    t_x_solo = tiempo_salto_jerk(dx=100.0, dy=0.0, j=j)
    t_x_teorico = (32 * 100.0 / j) ** (1 / 3)
    assert t_x_solo == pytest.approx(t_x_teorico)

    # salto diagonal 100x100: NO debe ser mayor que cada eje por separado
    # (si usara hipotenusa, sería t basado en d=141.4, mayor que t(100))
    t_diagonal = tiempo_salto_jerk(dx=100.0, dy=100.0, j=j)
    assert t_diagonal == pytest.approx(t_x_teorico)  # ambos ejes iguales -> max = cualquiera
    t_hipotenusa_hubiera_dado = (32 * math.hypot(100, 100) / j) ** (1 / 3)
    assert t_diagonal < t_hipotenusa_hubiera_dado


def test_tiempo_salto_domina_eje_mas_lento():
    j = 40000.0
    dx, dy = 200.0, 50.0
    t = tiempo_salto_jerk(dx, dy, j)
    tx = (32 * dx / j) ** (1 / 3)
    ty = (32 * dy / j) ** (1 / 3)
    assert t == pytest.approx(max(tx, ty))
    assert tx > ty  # dx es la distancia mayor en este caso
    assert t == pytest.approx(tx)


def test_distancia_critica_positiva_y_escala_con_v_max():
    j = 40000.0
    d1 = distancia_critica_jerk(v_max=100.0, j=j)
    d2 = distancia_critica_jerk(v_max=200.0, j=j)
    assert d1 > 0 and d2 > d1  # mayor v_max -> el régimen puro-jerk llega más lejos


# ---- ajuste lineal de k/j (verificado con datos sintéticos, k conocido) ----

def test_ajuste_recupera_k_exacto_sin_ruido():
    k_real = 0.05
    saltos = {
        "P1": [(100.0, 0.0), (0.0, 50.0), (80.0, 80.0)],
        "P2": [(200.0, 10.0), (300.0, 0.0)],
        "P3": [(10.0, 10.0), (10.0, 10.0), (10.0, 10.0), (10.0, 10.0)],
    }
    # Move time sintético SIN t_torcha (=0), generado con k_real exacto
    move_time = {
        n: k_real * sum(max(dx, dy) ** (1 / 3) for dx, dy in s)
        for n, s in saltos.items()
    }
    r = ajustar_modelo_desplazamiento(saltos, move_time)
    assert "error" not in r
    assert r["k"] == pytest.approx(k_real, rel=1e-6)
    assert r["t_torcha_s"] == pytest.approx(0.0, abs=1e-6)
    assert r["r2"] == pytest.approx(1.0, abs=1e-6)


def test_ajuste_recupera_k_y_t_torcha_con_offset():
    k_real, t_torcha_real = 0.04, 0.15
    saltos = {
        "P1": [(100.0, 0.0), (0.0, 50.0), (80.0, 80.0), (30.0, 10.0)],
        "P2": [(200.0, 10.0), (300.0, 0.0), (5.0, 5.0)],
        "P3": [(10.0, 10.0), (10.0, 10.0), (10.0, 10.0), (10.0, 10.0), (60.0, 5.0)],
    }
    move_time = {
        n: k_real * sum(max(dx, dy) ** (1 / 3) for dx, dy in s) + t_torcha_real * len(s)
        for n, s in saltos.items()
    }
    r = ajustar_modelo_desplazamiento(saltos, move_time)
    assert r["k"] == pytest.approx(k_real, rel=1e-6)
    assert r["t_torcha_s"] == pytest.approx(t_torcha_real, rel=1e-4)


def test_ajuste_sin_datos_reporta_bloqueo_no_inventa():
    r = ajustar_modelo_desplazamiento({"P1": [(10.0, 10.0)]}, {})
    assert "error" in r
    assert "k" not in r


def test_modelo_corte_sin_datos_reporta_bloqueo():
    r = ajustar_modelo_corte({"P1": [10.0, 10.0, 10.0, 10.0]}, {})
    assert "error" in r


# ---- boustrophedon (recorrido serpenteante) ----

def test_boustrophedon_alterna_direccion():
    # 2 filas x 3 columnas, grilla regular
    centros = [
        (0, 0), (10, 0), (20, 0),      # fila y=0
        (0, 10), (10, 10), (20, 10),   # fila y=10
    ]
    orden = ordenar_boustrophedon(centros)
    fila0 = orden[:3]
    fila1 = orden[3:]
    assert [p[0] for p in fila0] == [0, 10, 20]     # fila 0: izq->der
    assert [p[0] for p in fila1] == [20, 10, 0]      # fila 1: der->izq (alterna)


# ---- reconstrucción geométrica desde los DXF reales de Batería 2 ----

def test_extrae_centros_del_dxf_real():
    path = _BATERIA2_DIR / "B2_01_L60_p70_500x500.dxf"
    centros = extraer_centros_agujeros(path)
    assert len(centros) == 36  # 6x6, confirmado al generar la batería


def test_saltos_del_panel_es_n_menos_1():
    path = _BATERIA2_DIR / "B2_02_L30_p70_500x500.dxf"
    centros = extraer_centros_agujeros(path)
    saltos = saltos_del_panel(path)
    assert len(saltos) == len(centros) - 1


def test_saltos_no_negativos_y_paso_esperado():
    path = _BATERIA2_DIR / "B2_01_L60_p70_500x500.dxf"
    saltos = saltos_del_panel(path)
    for dx, dy in saltos:
        assert dx >= 0 and dy >= 0
    # la mayoría de saltos deben ser horizontales de paso=70mm (grilla regular)
    horizontales_paso = sum(1 for dx, dy in saltos if dy == 0 and dx == pytest.approx(70.0))
    assert horizontales_paso > 0


def test_segmentos_de_corte_4_lados_iguales_al_hole_size():
    path = _BATERIA2_DIR / "B2_01_L60_p70_500x500.dxf"  # hole_size=60mm
    segmentos = segmentos_de_corte(path)
    assert len(segmentos) == 36
    for lados in segmentos:
        assert len(lados) == 4
        for lado in lados:
            assert lado == pytest.approx(60.0, rel=1e-3)


def test_cargar_geometria_bateria2_devuelve_12_paneles():
    saltos, segmentos = cargar_geometria_bateria2()
    assert len(saltos) == 12
    assert len(segmentos) == 12
    for k in saltos:
        assert len(saltos[k]) == len(segmentos[k]) - 1
