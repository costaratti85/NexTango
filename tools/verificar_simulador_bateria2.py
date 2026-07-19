#!/usr/bin/env python3
"""ETAPA 2 — primeros números del motor cinemático contra Batería 2 real.

Compara Processing_s (corte) y Move_s (desplazamiento) MEDIDOS por CypCut
contra lo que predice el simulador (perfil trapezoidal + Junction Deviation +
look-ahead), para los 12 paneles reales.

Parámetros de MÁQUINA que hacen falta acá (v_rapido, a_max, delta_mm) NO están
calibrados todavía — son un punto de partida razonable para tener primeros
números, sujeto a que Constantino los revise/corrija con datos reales de la
Cypcut/Bystronic. v_tabla (velocidad de corte) SÍ viene de una calibración
física previa ya validada (Batería 2, α≈1/75mm/s).
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
    """Objeto mínimo compatible con tiempo_corte_figura (solo usa .longitud_mm
    y .tipo) — Batería 2 es toda cuadriculado square, 90° en cada vértice, así
    que no hace falta el parser DXF completo de la Etapa 1 para esto (ya sabemos
    los ángulos de antemano); se reserva para la figura orgánica (Corazón)."""
    def __init__(self, longitud_mm):
        self.longitud_mm = longitud_mm
        self.tipo = "linea"
        self.radio_mm = None


def _angulo_entre_vectores_grados(v1, v2) -> float:
    """Misma convención que angulo_de_giro_grados (Etapa 1): 0°=sigue derecho,
    180°=revierte. v1, v2 son vectores (dx, dy) CON signo (dirección real de
    movimiento), no absolutos."""
    n1, n2 = math.hypot(*v1), math.hypot(*v2)
    if n1 == 0 or n2 == 0:
        return 0.0
    ux1, uy1 = v1[0] / n1, v1[1] / n1
    ux2, uy2 = v2[0] / n2, v2[1] / n2
    cos_ang = max(-1.0, min(1.0, ux1 * ux2 + uy1 * uy2))
    return math.degrees(math.acos(cos_ang))


def tiempo_predicho_panel(dxf_path, v_tabla, v_rapido, a_max, delta_mm):
    # --- CORTE: cada agujero es un cuadrado, 90° en cada vértice ---
    lados_por_agujero = segmentos_de_corte(dxf_path)
    t_corte = 0.0
    for lados in lados_por_agujero:
        tramos = [_TramoFalso(l) for l in lados]
        angulos = [90.0] * len(lados)  # cuadrado: 4 esquinas de 90°, todas iguales
        t_corte += tiempo_corte_figura(tramos, angulos, cerrada=True,
                                       v_tabla_mm_s=v_tabla, delta_mm=delta_mm, a_max=a_max)
    lados_contorno = segmentos_de_contorno(dxf_path)
    if lados_contorno:
        tramos_c = [_TramoFalso(l) for l in lados_contorno]
        angulos_c = [90.0] * len(lados_contorno)
        t_corte += tiempo_corte_figura(tramos_c, angulos_c, cerrada=True,
                                       v_tabla_mm_s=v_tabla, delta_mm=delta_mm, a_max=a_max)

    # --- DESPLAZAMIENTO: boustrophedon real, ángulo real entre saltos consecutivos ---
    centros = ordenar_boustrophedon(extraer_centros_agujeros(dxf_path))
    vectores = [(x1 - x0, y1 - y0) for (x0, y0), (x1, y1) in zip(centros, centros[1:])]
    saltos_abs = [(abs(dx), abs(dy)) for dx, dy in vectores]
    angulos_travel = [_angulo_entre_vectores_grados(vectores[i], vectores[i + 1])
                      for i in range(len(vectores) - 1)]
    t_travel = tiempo_desplazamiento_saltos(saltos_abs, angulos_travel, v_rapido, delta_mm, a_max)

    return t_corte, t_travel


def evaluar(v_tabla, v_rapido, a_max, delta_mm, verbose=True):
    errores_corte, errores_travel = [], []
    filas = []
    for nombre in _PANELES_B2:
        key = nombre.split("_L")[0]
        path = _BATERIA2_DIR / f"{nombre}.dxf"
        t_corte, t_travel = tiempo_predicho_panel(path, v_tabla, v_rapido, a_max, delta_mm)
        real = DESGLOSE_BATERIA2[key]
        e_c = abs(t_corte - real["processing_s"]) / real["processing_s"] * 100
        e_t = abs(t_travel - real["move_s"]) / real["move_s"] * 100
        errores_corte.append(e_c)
        errores_travel.append(e_t)
        filas.append((key, t_corte, real["processing_s"], e_c, t_travel, real["move_s"], e_t))
    if verbose:
        print(f"{'panel':8} {'corte_pred':>10} {'corte_real':>10} {'err%':>7}   "
              f"{'travel_pred':>11} {'travel_real':>11} {'err%':>7}")
        for f in filas:
            print(f"{f[0]:8} {f[1]:10.2f} {f[2]:10.2f} {f[3]:6.1f}%   "
                  f"{f[4]:11.2f} {f[5]:11.2f} {f[6]:6.1f}%")
        print(f"\nerror medio CORTE:   {sum(errores_corte)/len(errores_corte):.1f}%  "
              f"(max {max(errores_corte):.1f}%)")
        print(f"error medio TRAVEL:  {sum(errores_travel)/len(errores_travel):.1f}%  "
              f"(max {max(errores_travel):.1f}%)")
    return errores_corte, errores_travel


if __name__ == "__main__":
    # Punto de partida: v_tabla del α ya calibrado (1/0.013372 ≈ 74.8mm/s);
    # v_rapido/a_max/delta_mm son GUESSES razonables de firmware CNC típico,
    # sujetos a corrección con datos reales de la máquina.
    print("=== Primeros números (parámetros de máquina SIN calibrar, valores de partida) ===")
    evaluar(v_tabla=74.8, v_rapido=250.0, a_max=5000.0, delta_mm=0.02)
