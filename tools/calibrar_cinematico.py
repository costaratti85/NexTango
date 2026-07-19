#!/usr/bin/env python3
"""ETAPA 3 — calibración de los parámetros de MÁQUINA del motor cinemático
contra los 12 paneles reales de Batería 2.

Principio (Constantino, MSG_154): cada parámetro se ajusta contra SU
componente medido por separado (Processing_s para corte, Move_s para
desplazamiento) — nunca contra el total. No forzar: si el mínimo del grid da
un valor físicamente imposible (negativo, absurdamente alto/bajo para una
máquina real), es señal de modelo mal, se reporta así, no se sigue afinando
hasta que "cierre" con un valor sin sentido.

Geometría se precomputa UNA sola vez por panel (reconstruida desde los DXF
reales) y se reutiliza en todo el grid — el motor cinemático en sí es barato,
lo caro es leer los 12 DXF (hasta 1521 agujeros en el más denso).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from analisis_laser_fisico import (
    _BATERIA2_DIR, _PANELES_B2, DESGLOSE_BATERIA2,
    extraer_centros_agujeros, ordenar_boustrophedon,
    segmentos_de_corte, segmentos_de_contorno,
)
from simulador_cinematico import tiempo_corte_figura, tiempo_desplazamiento_saltos


class _TramoFalso:
    __slots__ = ("longitud_mm", "tipo", "radio_mm")
    def __init__(self, longitud_mm):
        self.longitud_mm = longitud_mm
        self.tipo = "linea"
        self.radio_mm = None


def _angulo_entre_vectores_grados(v1, v2) -> float:
    n1, n2 = math.hypot(*v1), math.hypot(*v2)
    if n1 == 0 or n2 == 0:
        return 0.0
    ux1, uy1 = v1[0] / n1, v1[1] / n1
    ux2, uy2 = v2[0] / n2, v2[1] / n2
    cos_ang = max(-1.0, min(1.0, ux1 * ux2 + uy1 * uy2))
    return math.degrees(math.acos(cos_ang))


def cargar_geometria_precomputada():
    """Lee los 12 DXF UNA sola vez. Devuelve, por panel: las figuras de corte
    (lista de (lados, angulos, cerrada) — agujeros + contorno) y los saltos de
    desplazamiento (lista de (dx,dy) + ángulos de giro reales)."""
    datos = {}
    for nombre in _PANELES_B2:
        key = nombre.split("_L")[0]
        path = _BATERIA2_DIR / f"{nombre}.dxf"

        figuras_corte = []
        for lados in segmentos_de_corte(path):
            figuras_corte.append((lados, [90.0] * len(lados), True))
        lados_contorno = segmentos_de_contorno(path)
        if lados_contorno:
            figuras_corte.append((lados_contorno, [90.0] * len(lados_contorno), True))

        centros = ordenar_boustrophedon(extraer_centros_agujeros(path))
        vectores = [(x1 - x0, y1 - y0) for (x0, y0), (x1, y1) in zip(centros, centros[1:])]
        saltos_abs = [(abs(dx), abs(dy)) for dx, dy in vectores]
        angulos_travel = [_angulo_entre_vectores_grados(vectores[i], vectores[i + 1])
                          for i in range(len(vectores) - 1)]

        datos[key] = {
            "figuras_corte": figuras_corte,
            "saltos_abs": saltos_abs,
            "angulos_travel": angulos_travel,
            "processing_real": DESGLOSE_BATERIA2[key]["processing_s"],
            "move_real": DESGLOSE_BATERIA2[key]["move_s"],
        }
    return datos


def costo_corte(geo: dict, v_tabla: float, a_max: float, delta_mm: float) -> float:
    total = 0.0
    for lados, angulos, cerrada in geo["figuras_corte"]:
        tramos = [_TramoFalso(l) for l in lados]
        total += tiempo_corte_figura(tramos, angulos, cerrada, v_tabla, delta_mm, a_max)
    return total


def costo_travel(geo: dict, v_rapido: float, a_max: float, delta_mm: float) -> float:
    return tiempo_desplazamiento_saltos(geo["saltos_abs"], geo["angulos_travel"],
                                        v_rapido, delta_mm, a_max)


def error_medio_max_corte(datos: dict, v_tabla, a_max, delta_mm):
    errores = []
    for geo in datos.values():
        pred = costo_corte(geo, v_tabla, a_max, delta_mm)
        errores.append(abs(pred - geo["processing_real"]) / geo["processing_real"] * 100)
    return sum(errores) / len(errores), max(errores)


def error_medio_max_travel(datos: dict, v_rapido, a_max, delta_mm):
    errores = []
    for geo in datos.values():
        pred = costo_travel(geo, v_rapido, a_max, delta_mm)
        errores.append(abs(pred - geo["move_real"]) / geo["move_real"] * 100)
    return sum(errores) / len(errores), max(errores)


def grid_search_corte(datos, v_tabla_range, a_max_range, delta_range):
    mejor = None
    for v_tabla in v_tabla_range:
        for a_max in a_max_range:
            for delta in delta_range:
                m, mx = error_medio_max_corte(datos, v_tabla, a_max, delta)
                if mejor is None or m < mejor[0]:
                    mejor = (m, mx, v_tabla, a_max, delta)
    return mejor


def grid_search_travel(datos, v_rapido_range, a_max_range, delta_range):
    mejor = None
    for v_rapido in v_rapido_range:
        for a_max in a_max_range:
            for delta in delta_range:
                m, mx = error_medio_max_travel(datos, v_rapido, a_max, delta)
                if mejor is None or m < mejor[0]:
                    mejor = (m, mx, v_rapido, a_max, delta)
    return mejor


def reporte_detallado(datos, v_tabla, a_max_cut, delta_cut, v_rapido, a_max_trav, delta_trav):
    print(f"{'panel':8} {'corte_pred':>10} {'corte_real':>10} {'err%':>7}   "
          f"{'travel_pred':>11} {'travel_real':>11} {'err%':>7}")
    ec, et = [], []
    for key, geo in datos.items():
        pc = costo_corte(geo, v_tabla, a_max_cut, delta_cut)
        pt = costo_travel(geo, v_rapido, a_max_trav, delta_trav)
        rc, rt = geo["processing_real"], geo["move_real"]
        eec = abs(pc - rc) / rc * 100
        eet = abs(pt - rt) / rt * 100
        ec.append(eec); et.append(eet)
        print(f"{key:8} {pc:10.2f} {rc:10.2f} {eec:6.1f}%   {pt:11.2f} {rt:11.2f} {eet:6.1f}%")
    print(f"\nerror medio CORTE:  {sum(ec)/len(ec):.1f}%  (max {max(ec):.1f}%)")
    print(f"error medio TRAVEL: {sum(et)/len(et):.1f}%  (max {max(et):.1f}%)")


def _refinar(centro, factor_rango, n, minimo=1e-6):
    """n valores entre centro*(1-factor) y centro*(1+factor)."""
    lo = max(centro * (1 - factor_rango), minimo)
    hi = centro * (1 + factor_rango)
    paso = (hi - lo) / (n - 1)
    return [lo + i * paso for i in range(n)]


if __name__ == "__main__":
    datos = cargar_geometria_precomputada()

    print("=== Grid GRUESO CORTE (v_tabla, a_max_cut, delta_cut) vs Processing_s ===")
    r0 = grid_search_corte(
        datos,
        v_tabla_range=[60, 70, 80, 90, 100],
        a_max_range=[500, 1500, 3000, 6000, 12000, 20000],
        delta_range=[0.01, 0.03, 0.06, 0.12, 0.2],
    )
    print("mejor grueso:", r0)
    _, _, v_tabla0, a_max0, delta0 = r0
    print("=== Grid FINO CORTE (refinado alrededor del grueso) ===")
    r_corte = grid_search_corte(
        datos,
        v_tabla_range=_refinar(v_tabla0, 0.15, 5),
        a_max_range=_refinar(a_max0, 0.5, 5),
        delta_range=_refinar(delta0, 0.5, 5),
    )
    print("mejor (err_medio%, err_max%, v_tabla, a_max, delta):", r_corte)

    print("\n=== Grid GRUESO TRAVEL (v_rapido, a_max_trav, delta_trav) vs Move_s ===")
    rt0 = grid_search_travel(
        datos,
        v_rapido_range=[80, 100, 120, 140, 170, 200],
        a_max_range=[500, 1500, 3000, 6000, 12000, 20000],
        delta_range=[0.01, 0.03, 0.06, 0.12, 0.2],
    )
    print("mejor grueso:", rt0)
    _, _, v_rap0, a_maxt0, deltat0 = rt0
    print("=== Grid FINO TRAVEL (refinado alrededor del grueso) ===")
    r_travel = grid_search_travel(
        datos,
        v_rapido_range=_refinar(v_rap0, 0.15, 5),
        a_max_range=_refinar(a_maxt0, 0.5, 5),
        delta_range=_refinar(deltat0, 0.5, 5),
    )
    print("mejor (err_medio%, err_max%, v_rapido, a_max, delta):", r_travel)

    print("\n=== Reporte final por panel con los parámetros ganadores ===")
    _, _, v_tabla, a_max_cut, delta_cut = r_corte
    _, _, v_rapido, a_max_trav, delta_trav = r_travel
    reporte_detallado(datos, v_tabla, a_max_cut, delta_cut, v_rapido, a_max_trav, delta_trav)
