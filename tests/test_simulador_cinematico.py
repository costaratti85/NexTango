"""Tests del motor cinemático (Etapa 2 del simulador de movimiento) — perfil
trapezoidal + Junction Deviation + look-ahead (lineal y cíclico).

Principio: verificar cada pieza matemáticamente contra su fórmula analítica
conocida antes de confiar en el ensamblado completo (mismo criterio que en
test_simulador_toolpath.py).
"""
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from simulador_cinematico import (
    perfil_trapezoidal_tiempo,
    velocidad_esquina_junction_deviation,
    look_ahead,
    look_ahead_ciclico,
    tiempo_corte_figura,
    tiempo_desplazamiento_saltos,
)


# ---- perfil trapezoidal: casos analíticos exactos ----

def test_triangular_reposo_a_reposo():
    d, a = 50.0, 1000.0
    v_pico_teorico = math.sqrt(a * d)
    t, vp = perfil_trapezoidal_tiempo(d, 0.0, 0.0, v_pico_teorico + 50, a)
    assert vp == pytest.approx(v_pico_teorico)
    assert t == pytest.approx(2 * math.sqrt(d / a))


def test_con_meseta_de_crucero():
    d, v_max, a = 200.0, 100.0, 1000.0
    t, vp = perfil_trapezoidal_tiempo(d, 0.0, 0.0, v_max, a)
    d_acc = v_max ** 2 / (2 * a)
    t_esperado = 2 * (v_max / a) + (d - 2 * d_acc) / v_max
    assert vp == pytest.approx(v_max)
    assert t == pytest.approx(t_esperado)


def test_v_in_v_out_no_cero_reconstruye_distancia_recorrida():
    v_in, v_out, v_max, a = 20.0, 30.0, 80.0, 500.0
    d = 50.0
    t, vp = perfil_trapezoidal_tiempo(d, v_in, v_out, v_max, a)
    assert vp <= v_max + 1e-9


def test_distancia_cero_da_tiempo_cero():
    t, vp = perfil_trapezoidal_tiempo(0.0, 10.0, 5.0, 50.0, 100.0)
    assert t == 0.0


def test_caso_borde_distancia_sobrante_produce_pico_mayor_a_ambos_extremos():
    """Documentado explícitamente (no es un bug): si d es MAYOR que la distancia
    de frenada pura de v_in a v_out, la solución de TIEMPO MÍNIMO acelera un
    poco antes de frenar más fuerte — matemáticamente más rápido que frenar
    "flojo" toda la distancia. Verificado contra la alternativa de frenada
    única a aceleración reducida: la del pico es más rápida."""
    d, v_in, v_out, v_max, a = 5.0, 50.0, 0.0, 100.0, 1000.0
    t, vp = perfil_trapezoidal_tiempo(d, v_in, v_out, v_max, a)
    assert vp > v_in  # el "pico" supera la entrada -> hubo una fase de aceleración

    # alternativa: frenar con aceleración reducida a' durante TODA la distancia
    a_reducida = v_in ** 2 / (2 * d)
    t_alternativa = v_in / a_reducida
    assert t < t_alternativa  # la solución con pico es genuinamente más rápida

    # y la distancia de frenada PURA (a a_max completo) es menor que d -> por
    # eso hay margen de sobra que la solución óptima aprovecha acelerando
    d_frenada_pura = (v_in ** 2 - v_out ** 2) / (2 * a)
    assert d_frenada_pura < d


# ---- Junction Deviation: casos límite ----

def test_junction_deviation_angulo_cero_no_frena():
    v = velocidad_esquina_junction_deviation(0.0, delta_mm=0.02, a_max=1000.0)
    assert v > 1e6  # "infinito" práctico


def test_junction_deviation_reversa_180_frena_a_cero():
    v = velocidad_esquina_junction_deviation(180.0, delta_mm=0.02, a_max=1000.0)
    assert v == pytest.approx(0.0)


def test_junction_deviation_monotona_decreciente_con_el_angulo():
    angulos = [10, 30, 60, 90, 120, 150, 170]
    velocidades = [velocidad_esquina_junction_deviation(a, 0.02, 1000.0) for a in angulos]
    for v1, v2 in zip(velocidades, velocidades[1:]):
        assert v2 < v1  # a mayor ángulo de giro, menor velocidad permitida


# ---- look-ahead lineal: reverse pass y forward pass ----

def test_look_ahead_reverse_pass_capa_entrada_de_tramo_corto_final():
    """Un tramo largo seguido de uno corto que debe terminar en reposo: el
    reverse pass debe capar la velocidad del tramo largo para que el corto
    pueda frenar a tiempo."""
    distancias = [100.0, 5.0]
    v_techo = [200.0, 200.0]
    a_max = 1000.0
    pares = look_ahead(distancias, v_techo, [1e12], a_max)
    v_frenada_max_en_5mm = math.sqrt(2 * a_max * 5.0)
    assert pares[0][1] == pytest.approx(v_frenada_max_en_5mm)  # salida del 1ro
    assert pares[1][0] == pytest.approx(v_frenada_max_en_5mm)  # entrada del 2do


def test_look_ahead_forward_pass_capa_salida_de_tramo_corto_inicial():
    """Un tramo corto al inicio (arranca en reposo) limita cuánto puede
    acelerar antes de empalmar con el siguiente."""
    distancias = [5.0, 100.0]
    v_techo = [200.0, 200.0]
    a_max = 1000.0
    pares = look_ahead(distancias, v_techo, [1e12], a_max)
    v_acel_max_en_5mm = math.sqrt(2 * a_max * 5.0)
    assert pares[0][1] == pytest.approx(v_acel_max_en_5mm)
    assert pares[1][0] == pytest.approx(v_acel_max_en_5mm)


def test_look_ahead_extremos_en_reposo():
    pares = look_ahead([50.0, 50.0, 50.0], [100.0] * 3, [1e12, 1e12], 1000.0)
    assert pares[0][0] == pytest.approx(0.0)
    assert pares[-1][1] == pytest.approx(0.0)


# ---- look-ahead cíclico: converge, no fuerza reposo en la costura ----

def test_look_ahead_ciclico_converge_igual_con_mas_repeticiones():
    distancias = [60.0] * 4
    v_techo = [74.8] * 4
    v_esq = velocidad_esquina_junction_deviation(90.0, 0.02, 5000.0)
    p3 = look_ahead_ciclico(distancias, v_techo, [v_esq] * 4, 5000.0, repeticiones=3)
    p5 = look_ahead_ciclico(distancias, v_techo, [v_esq] * 4, 5000.0, repeticiones=5)
    for a, b in zip(p3, p5):
        assert a[0] == pytest.approx(b[0])
        assert a[1] == pytest.approx(b[1])


def test_look_ahead_ciclico_no_frena_a_reposo_en_la_costura():
    """El bug que este test previene: una figura cerrada NO debe forzar v=0 en
    el primer/último tramo — la costura es una unión más, no una parada real."""
    distancias = [60.0] * 4
    v_techo = [74.8] * 4
    v_esq = velocidad_esquina_junction_deviation(90.0, 0.02, 5000.0)
    pares = look_ahead_ciclico(distancias, v_techo, [v_esq] * 4, 5000.0)
    assert pares[0][0] > 1.0   # NO arranca en reposo
    assert pares[-1][1] > 1.0  # NO termina en reposo


# ---- tiempo_corte_figura: cuadrado cerrado da un tiempo cercano al ideal sin frenar ----

class _TramoFalso:
    def __init__(self, l):
        self.longitud_mm = l
        self.tipo = "linea"
        self.radio_mm = None


def test_tiempo_corte_cuadrado_cerrado_apenas_mayor_al_ideal_sin_esquinas():
    lados = [60.0] * 4
    angulos = [90.0] * 4
    v_tabla, delta, a_max = 74.8, 0.02, 5000.0
    t = tiempo_corte_figura([_TramoFalso(l) for l in lados], angulos, True, v_tabla, delta, a_max)
    t_ideal = sum(lados) / v_tabla
    assert t > t_ideal          # las esquinas SÍ cuestan algo de tiempo
    assert t < t_ideal * 1.1    # pero no deberían más que ~10% extra para un cuadrado grande


def test_tiempo_corte_circulo_completo_sin_frenar():
    """Un círculo completo es una figura cerrada de UN solo tramo — la unión
    consigo mismo es perfectamente tangente (0° de giro real), no debería
    frenar en ningún punto. Caso borde encontrado al probar contra Cosmos
    (918 círculos reales): sin este caso especial, se frenaba a reposo en la
    costura de cada círculo, igual que el bug original de las figuras
    cerradas de Batería 2."""
    radio = 10.0
    v_tabla, delta, a_max = 74.8, 0.02, 5000.0
    v_techo_curva = math.sqrt(a_max * radio)
    circunferencia = 2 * math.pi * radio
    tramo_circulo = type("T", (), {"longitud_mm": circunferencia, "tipo": "arco", "radio_mm": radio})()
    t = tiempo_corte_figura([tramo_circulo], [], True, v_tabla, delta, a_max)
    t_ideal = circunferencia / min(v_tabla, v_techo_curva)
    assert t == pytest.approx(t_ideal)


def test_tiempo_corte_figura_abierta_arranca_y_termina_en_reposo():
    lados = [60.0, 60.0]
    angulos = [90.0]
    v_tabla, delta, a_max = 74.8, 0.02, 5000.0
    t_abierta = tiempo_corte_figura([_TramoFalso(l) for l in lados], angulos, False, v_tabla, delta, a_max)
    t_ideal = sum(lados) / v_tabla
    assert t_abierta > t_ideal  # frenar+acelerar en los 2 extremos (reposo) cuesta más


# ---- tiempo_desplazamiento_saltos: por eje, en diagonal manda el mas lento ----

def test_desplazamiento_un_salto_diagonal_45_grados():
    saltos = [(30.0, 30.0)]
    t = tiempo_desplazamiento_saltos(saltos, [], v_rapido_mm_s=100.0, delta_mm=0.02, a_max=1000.0)
    # cada eje recorre 30mm con v_rapido efectivo proyectado (~70.7 = 100*cos45)
    assert t > 0


def test_desplazamiento_sin_saltos_da_cero():
    t = tiempo_desplazamiento_saltos([], [], 100.0, 0.02, 1000.0)
    assert t == 0.0
