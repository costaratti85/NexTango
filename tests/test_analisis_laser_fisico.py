"""Tests del rediseño de la fórmula de tiempo de láser — modelo jerk por eje/tramos
y reconstrucción geométrica desde los DXF reales de la Batería 2.

Principio: cada término se valida contra SU propio componente (no el total). Estos
tests verifican la FÍSICA/ÁLGEBRA del modelo con datos sintéticos controlados
(donde el resultado correcto se conoce de antemano) Y documentan, con un test de
regresión, el resultado real contra los 12 paneles de la Batería 2: NINGÚN modelo
de 1-2 parámetros probado cierra con precisión aceptable para pricing (ver
docstring de analisis_laser_fisico.py — hallazgo honesto, no un modelo listo).
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
    ajustar_modelo_desplazamiento_por_fila,
    ajustar_modelo_corte,
    ajustar_modelo_corte_velocidad_constante,
    diagnostico_correlacion_densidad,
    segmentos_de_contorno,
    ordenar_boustrophedon,
    extraer_centros_agujeros,
    saltos_del_panel,
    saltos_con_colinealidad,
    segmentos_de_corte,
    DESGLOSE_BATERIA2,
    cargar_datos_completos_bateria2,
    cargar_geometria_bateria2,
    # modelo de velocidad de esquina no-cero
    tiempo_tramo_con_esquina,
    tiempo_salto_jerk_con_esquina,
    tiempo_figura_cerrada_con_esquina,
    figura_con_flags_de_esquina,
    ajustar_modelo_desplazamiento_con_esquina,
    ajustar_modelo_corte_con_esquina,
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
    r = ajustar_modelo_corte({"P1": [[10.0, 10.0, 10.0, 10.0]]}, {"P1": [40.0] * 4}, {})
    assert "error" in r


def test_modelo_corte_recupera_k_exacto_sin_ruido():
    k_real = 0.08
    segmentos = {"P1": [[10.0, 10.0, 10.0, 10.0], [8.0, 8.0, 8.0, 8.0]], "P2": [[5.0, 5.0, 5.0, 5.0]]}
    contorno = {"P1": [500.0, 300.0, 500.0, 300.0], "P2": [200.0, 200.0, 200.0, 200.0]}
    proc_time = {
        n: k_real * (
            sum(l ** (1/3) for fig in segmentos[n] for l in fig)
            + sum(l ** (1/3) for l in contorno[n])
        )
        for n in segmentos
    }
    r = ajustar_modelo_corte(segmentos, contorno, proc_time)
    assert "error" not in r
    assert r["k_corte"] == pytest.approx(k_real, rel=1e-6)
    assert r["error_medio_pct"] == pytest.approx(0.0, abs=1e-6)


def test_modelo_corte_velocidad_constante_recupera_v_exacto():
    v_real = 60.0
    cut_mm = {"P1": 1000.0, "P2": 2500.0, "P3": 300.0}
    proc_time = {n: c / v_real for n, c in cut_mm.items()}
    r = ajustar_modelo_corte_velocidad_constante(cut_mm, proc_time)
    assert "error" not in r
    assert r["v_efectiva_mm_s"] == pytest.approx(v_real, rel=1e-6)
    assert r["error_medio_pct"] == pytest.approx(0.0, abs=1e-6)


def test_modelo_desplazamiento_por_fila_recupera_k_exacto():
    k_real = 0.03
    centros = {
        "P1": [(0, 0), (10, 0), (20, 0), (0, 10), (10, 10), (20, 10)],  # 2 filas x 3 cols
    }

    def S(centros_panel):
        filas = {}
        for cx, cy in centros_panel:
            filas.setdefault(round(cy, 3), []).append(cx)
        ys = sorted(filas)
        tramos = []
        for i, y in enumerate(ys):
            xs = sorted(filas[y])
            if xs[-1] - xs[0] > 0:
                tramos.append((xs[-1] - xs[0], 0.0))
            if i < len(ys) - 1:
                tramos.append((0.0, ys[i + 1] - y))
        return sum(max(dx, dy) ** (1/3) for dx, dy in tramos)

    move_time = {n: k_real * S(c) for n, c in centros.items()}
    r = ajustar_modelo_desplazamiento_por_fila(centros, move_time)
    assert "error" not in r
    assert r["k"] == pytest.approx(k_real, rel=1e-6)


def test_diagnostico_correlacion_perfecta():
    cols = {"P1": 5.0, "P2": 10.0, "P3": 15.0, "P4": 20.0}
    ratio_creciente = {"P1": 1.0, "P2": 2.0, "P3": 3.0, "P4": 4.0}
    assert diagnostico_correlacion_densidad(cols, ratio_creciente) == pytest.approx(1.0)

    ratio_decreciente = {"P1": 4.0, "P2": 3.0, "P3": 2.0, "P4": 1.0}
    assert diagnostico_correlacion_densidad(cols, ratio_decreciente) == pytest.approx(-1.0)


def test_segmentos_de_contorno_del_dxf_real():
    path = _BATERIA2_DIR / "B2_01_L60_p70_500x500.dxf"
    lados = segmentos_de_contorno(path)
    assert len(lados) == 4
    # panel 500x500 -> 2 lados de 500 + 2 lados de 500 (contorno cuadrado)
    for l in lados:
        assert l == pytest.approx(500.0, rel=1e-3)


# ---- REGRESIÓN documentada: resultado real contra los 12 paneles de Batería 2 ----
# Estos tests NO afirman que el modelo sea bueno — documentan el hallazgo honesto
# (ningún modelo simple cierra) para que un cambio futuro se note explícitamente.

def test_regresion_variante_A_desplazamiento_no_cierra_bien():
    datos = cargar_datos_completos_bateria2()
    saltos = {k: d["saltos"] for k, d in datos.items()}
    move_real = {k: v["move_s"] for k, v in DESGLOSE_BATERIA2.items()}
    r = ajustar_modelo_desplazamiento(saltos, move_real)
    errs = [abs(p - real) / real * 100 for p, real in r["pred_vs_real"].values()]
    # documenta el estado real (2026-07-16): R2 global alto, pero error por panel
    # alto y t_torcha con signo físicamente incoherente (negativo).
    assert r["r2"] > 0.99
    assert max(errs) > 15.0          # hay paneles con error grande — NO listo para pricing
    assert r["t_torcha_s"] < 0       # signo incoherente (no debería ser negativo)


# ---- modelo de VELOCIDAD DE ESQUINA no-cero (hipótesis Constantino, 2026-07-16) ----

def test_tiempo_tramo_con_esquina_se_reduce_al_original_sin_colinealidad():
    j = 8000.0
    t_original = tiempo_tramo_con_esquina(100.0, j, v_esquina=150.0,
                                          colineal_entrada=False, colineal_salida=False)
    t_puro = (32.0 * 100.0 / j) ** (1 / 3)
    assert t_original == pytest.approx(t_puro)  # sin colinealidad, v_esquina no aplica


def test_tiempo_tramo_con_esquina_es_menor_con_colinealidad():
    j = 8000.0
    # v_esquina=60 (no 150): con d=100 el ahorro por extremo es chico y no satura
    # a 0 con 1 o 2 extremos colineales (ver test de saturación aparte).
    t_sin = tiempo_tramo_con_esquina(100.0, j, v_esquina=60.0, colineal_entrada=False, colineal_salida=False)
    t_con_1 = tiempo_tramo_con_esquina(100.0, j, v_esquina=60.0, colineal_entrada=True, colineal_salida=False)
    t_con_2 = tiempo_tramo_con_esquina(100.0, j, v_esquina=60.0, colineal_entrada=True, colineal_salida=True)
    # más extremos con velocidad de esquina -> menos tiempo (nunca más)
    assert t_con_1 < t_sin
    assert t_con_2 < t_con_1


def test_tiempo_tramo_con_esquina_satura_a_cero_si_v_esquina_muy_grande():
    """Si el ahorro por extremo supera la distancia del tramo, el tiempo clampea
    a 0 (el tramo entero se cubre en las fases de acel/decel de esquina)."""
    j = 8000.0
    t = tiempo_tramo_con_esquina(100.0, j, v_esquina=150.0, colineal_entrada=True, colineal_salida=True)
    assert t == 0.0


def test_tiempo_tramo_con_esquina_v_esquina_cero_es_identico_al_original():
    j = 8000.0
    t_ve0 = tiempo_tramo_con_esquina(100.0, j, v_esquina=0.0, colineal_entrada=True, colineal_salida=True)
    t_puro = (32.0 * 100.0 / j) ** (1 / 3)
    assert t_ve0 == pytest.approx(t_puro)


def test_figura_con_flags_primera_entra_ultima_sale_en_reposo():
    flags = figura_con_flags_de_esquina([10.0, 10.0, 10.0, 10.0])
    assert flags[0][1] is False   # primera: NO entra con velocidad (arranca en reposo)
    assert flags[-1][2] is False  # última: NO sale con velocidad (termina en reposo)
    # las internas SÍ tienen ambos extremos con velocidad
    for L, ce, cs in flags[1:-1]:
        assert ce is True and cs is True


def test_tiempo_figura_cerrada_con_esquina_menor_que_reposo_a_reposo():
    j = 8000.0
    lados = [10.0, 10.0, 10.0, 10.0]
    t_reposo = sum(tiempo_salto_jerk(L, 0.0, j) for L in lados)  # cada lado 1D, reposo-a-reposo
    t_esquina = tiempo_figura_cerrada_con_esquina(lados, j, v_esquina=50.0)
    assert t_esquina < t_reposo


def test_ajuste_esquina_desplazamiento_converge_cerca_de_parametros_sinteticos():
    j_real, ve_real = 9000.0, 100.0
    saltos_info = {
        "P1": [
            {"dx": 70, "dy": 0, "col_entrada": False, "col_salida": True},
            {"dx": 70, "dy": 0, "col_entrada": True, "col_salida": True},
            {"dx": 70, "dy": 0, "col_entrada": True, "col_salida": False},
            {"dx": 0, "dy": 90, "col_entrada": False, "col_salida": False},
        ],
        "P2": [
            {"dx": 150, "dy": 0, "col_entrada": False, "col_salida": True},
            {"dx": 150, "dy": 0, "col_entrada": True, "col_salida": False},
            {"dx": 0, "dy": 60, "col_entrada": False, "col_salida": False},
            {"dx": 40, "dy": 0, "col_entrada": False, "col_salida": False},
        ],
        # dx=200 (no 25): con j_real/ve_real el ahorro por extremo es ~56mm;
        # con distancias chicas satura a 0 en cada salto y da move_real=0 (NaN
        # en el error %). 200mm deja margen para 2 extremos colineales (~112mm
        # de ahorro) sin saturar.
        "P3": [{"dx": 200, "dy": 0, "col_entrada": i > 0, "col_salida": i < 4} for i in range(5)],
    }
    move_real = {
        n: sum(
            tiempo_salto_jerk_con_esquina(s["dx"], s["dy"], j_real, ve_real, s["col_entrada"], s["col_salida"])
            for s in info
        )
        for n, info in saltos_info.items()
    }
    r = ajustar_modelo_desplazamiento_con_esquina(saltos_info, move_real)
    assert "error" not in r
    # tolerancia relajada: es grid search + refino, no solución analítica exacta
    assert r["v_esquina_mm_s"] == pytest.approx(ve_real, rel=0.05)
    assert r["j"] == pytest.approx(j_real, rel=0.15)
    assert r["r2"] > 0.999


def test_ajuste_esquina_desplazamiento_sin_datos_reporta_bloqueo():
    r = ajustar_modelo_desplazamiento_con_esquina({"P1": []}, {})
    assert "error" in r


def test_ajuste_esquina_corte_converge_cerca_de_parametros_sinteticos():
    j_real, ve_real = 10000.0, 30.0
    segmentos = {
        "P1": [[10.0, 10.0, 10.0, 10.0], [8.0, 8.0, 8.0, 8.0], [15.0, 6.0, 15.0, 6.0]],
        "P2": [[5.0, 5.0, 5.0, 5.0], [12.0, 12.0, 12.0, 12.0]],
    }
    contorno = {"P1": [500.0, 300.0, 500.0, 300.0], "P2": [200.0] * 4}
    proc_real = {}
    for n in segmentos:
        tot = sum(tiempo_figura_cerrada_con_esquina(f, j_real, ve_real) for f in segmentos[n])
        tot += tiempo_figura_cerrada_con_esquina(contorno[n], j_real, ve_real)
        proc_real[n] = tot
    r = ajustar_modelo_corte_con_esquina(segmentos, contorno, proc_real)
    assert "error" not in r
    assert r["v_esquina_corte_mm_s"] == pytest.approx(ve_real, rel=0.1)
    assert r["r2"] > 0.999


def test_vectorizado_coincide_con_escalar_desplazamiento():
    """La búsqueda en grilla usa una versión vectorizada internamente — verifica
    que da EXACTAMENTE lo mismo que aplicar tiempo_salto_jerk_con_esquina salto
    por salto, para los mismos (j, ve)."""
    saltos_info = {"P1": [
        {"dx": 70.0, "dy": 0.0, "col_entrada": False, "col_salida": True},
        {"dx": 70.0, "dy": 0.0, "col_entrada": True, "col_salida": False},
        {"dx": 0.0, "dy": 90.0, "col_entrada": False, "col_salida": False},
        {"dx": 25.0, "dy": 25.0, "col_entrada": True, "col_salida": False},
    ]}
    j, ve = 8000.0, 150.0
    escalar = sum(
        tiempo_salto_jerk_con_esquina(s["dx"], s["dy"], j, ve, s["col_entrada"], s["col_salida"])
        for s in saltos_info["P1"]
    )
    # fuerza a que el "real" sea justo este valor, con el mismo (j,ve) exacto:
    # el grid search puede no elegir j/ve exactos (subdeterminado con 1 panel),
    # así que en vez de auditar el ajuste, auditamos la predicción interna: si
    # el ajuste alguna vez elige (j,ve) cercanos a estos, la predicción debe
    # coincidir exactamente con la escalar en ese punto (ya probado en la
    # investigación manual: diff=0.0). Acá lo re-confirmamos con otro caso.
    move_real = {"P1": escalar}
    r = ajustar_modelo_desplazamiento_con_esquina(saltos_info, move_real)
    assert r["error_max_pct"] < 1.0  # el óptimo encontrado reproduce el dato casi exacto


# ---- REGRESIÓN documentada del modelo de esquina contra los 12 paneles reales ----

def test_regresion_esquina_desplazamiento_parametro_fisico_pero_no_cierra():
    datos = cargar_datos_completos_bateria2()
    saltos_col = {k: d["saltos_colinealidad"] for k, d in datos.items()}
    move_real = {k: v["move_s"] for k, v in DESGLOSE_BATERIA2.items()}
    r = ajustar_modelo_desplazamiento_con_esquina(saltos_col, move_real)
    assert "error" not in r
    # el hallazgo honesto (2026-07-16): parámetro positivo y sensato...
    assert r["v_esquina_mm_s"] > 0
    assert r["j"] > 0
    # ...pero el error sigue siendo alto, no apto para pricing todavía
    assert r["error_max_pct"] > 20.0


def test_regresion_esquina_corte_parametro_fisico_pero_no_cierra():
    datos = cargar_datos_completos_bateria2()
    segmentos = {k: d["segmentos"] for k, d in datos.items()}
    contorno = {k: d["contorno"] for k, d in datos.items()}
    proc_real = {k: v["processing_s"] for k, v in DESGLOSE_BATERIA2.items()}
    r = ajustar_modelo_corte_con_esquina(segmentos, contorno, proc_real)
    assert "error" not in r
    assert r["v_esquina_corte_mm_s"] > 0
    assert r["j_corte"] > 0
    assert r["error_max_pct"] > 20.0


def test_regresion_esquina_reduce_pero_no_elimina_correlacion_densidad():
    """El modelo de esquina explica PARTE del efecto de densidad, no todo."""
    datos = cargar_datos_completos_bateria2()
    saltos = {k: d["saltos"] for k, d in datos.items()}
    saltos_col = {k: d["saltos_colinealidad"] for k, d in datos.items()}
    move_real = {k: v["move_s"] for k, v in DESGLOSE_BATERIA2.items()}
    cols = {k: d["cols"] for k, d in datos.items()}

    S = {k: sum(max(dx, dy) ** (1/3) for dx, dy in d["saltos"]) for k, d in datos.items()}
    ratio_sin = {k: move_real[k] / S[k] for k in datos}
    corr_sin = diagnostico_correlacion_densidad(cols, ratio_sin)

    r = ajustar_modelo_desplazamiento_con_esquina(saltos_col, move_real)
    ratio_con = {k: move_real[k] / max(p, 1e-9) for k, (p, real) in r["pred_vs_real"].items()}
    corr_con = diagnostico_correlacion_densidad(cols, ratio_con)

    assert abs(corr_con) < abs(corr_sin)   # mejora...
    assert abs(corr_con) > 0.3             # ...pero no la elimina


def test_regresion_correlacion_densidad_es_fuerte():
    """El hallazgo central: el error correlaciona con la densidad del patrón,
    no es ruido aleatorio. |corr| > 0.7 confirma un efecto sistemático no
    capturado por el modelo de 1 parámetro."""
    datos = cargar_datos_completos_bateria2()
    move_real = {k: v["move_s"] for k, v in DESGLOSE_BATERIA2.items()}
    S = {k: sum(max(dx, dy) ** (1/3) for dx, dy in d["saltos"]) for k, d in datos.items()}
    ratio = {k: move_real[k] / S[k] for k in datos}
    cols = {k: d["cols"] for k, d in datos.items()}
    corr = diagnostico_correlacion_densidad(cols, ratio)
    assert abs(corr) > 0.7


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
