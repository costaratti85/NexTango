#!/usr/bin/env python3
"""ETAPA 3 — cotejo del experimento de validación v2 (MSG_167/168) contra lo
medido por Constantino en CypCut (chapa N°14/2.0mm). Datos reales cargados a
mano (medición a ciegas, comunicados por Dispatch) — NO se generan ni se
vuelven a bajar del server acá.

Reproduce: (1) predicción de Bloque 1 (corte puro) con los parámetros vigentes
de CORTE (sin cambios, siguen validados); (2) predicción de Bloque 2/3 con los
parámetros VIEJOS de travel (de Batería 2) vs un reajuste fino SOLO con estos
3 datos nuevos; (3) cruce del reajuste nuevo contra Batería 2 para chequear
honestamente si sigue siendo consistente o no.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from simulador_cinematico import tiempo_corte_figura, tiempo_desplazamiento_saltos
from calibrar_cinematico import cargar_geometria_precomputada, error_medio_max_travel, error_medio_max_corte

# Parámetros de CORTE vigentes (Etapa 3, sin cambios -- ver más abajo por qué)
V_TABLA, A_MAX_CUT, DELTA_CUT = 74.0, 625.0, 0.2

# Parámetros de TRAVEL: viejos (de Batería 2) vs el reajuste de este experimento.
# TRAVEL_NUEVO es el resultado del refit conjunto con los 5 puntos (MSG_172:
# se agregaron travel_muylejos_1/2, 1000mm y 3000mm, que resuelven la duda de
# si hay meseta de crucero -- SÍ la hay, cerca de 200-205mm/s, lejísimos del
# nominal de 1650mm/s).
TRAVEL_VIEJO = dict(v_rapido=129.5, a_max=750.0, delta=0.005)
TRAVEL_NUEVO = dict(v_rapido=204.9, a_max=382.0, delta=0.005)  # delta sin testear (todo angulo=0 acá)

# (xs, altura_mm) de cada archivo de Bloque 2/3 -- fuente única, reusada por
# las predicciones de corte/travel y por el refit.
LAYOUT_BLOQUE23 = {
    "travel_cerca":   ([0, 20, 40, 60], 10.0),
    "travel_lejos":   ([0, 200, 400, 600], 10.0),
    "tamano_grande":  ([0, 20, 40, 60], 40.0),
    "travel_muylejos_1": ([0, 1000], 10.0),
    "travel_muylejos_2": ([0, 3000], 10.0),
}


class _TramoFalso:
    __slots__ = ("longitud_mm", "tipo", "radio_mm")
    def __init__(self, l, tipo="linea", radio=None):
        self.longitud_mm = l; self.tipo = tipo; self.radio_mm = radio


MEDIDO_BLOQUE1 = {
    # nombre: (cut_mm, processing_s)
    "radio_05mm":     (7.85, 0.236),
    "radio_15mm":     (23.56, 0.445),
    "radio_40mm":     (62.83, 0.969),
    "radio_100mm":    (157.08, 2.226),
    "angulo_015deg":  (100.00, 1.497),
    "angulo_045deg":  (100.00, 1.503),
    "angulo_090deg":  (100.00, 1.517),
    "angulo_135deg":  (100.00, 1.521),
    "angulo_165deg":  (100.00, 1.523),
    "recta_020mm":    (20.00, 0.398),
    "recta_080mm":    (80.00, 1.198),
    "recta_250mm":    (250.00, 3.465),
}

MEDIDO_BLOQUE23 = {
    # nombre: (processing_s, move_s, delay_s)
    "tamano_grande":     (2.658, 1.137, 3.043),
    "travel_cerca":      (1.058, 0.800, 3.043),
    "travel_lejos":      (1.058, 3.538, 3.043),
    "travel_muylejos_1": (0.529, 5.179, 1.607),  # 2 figuras (1 salto), no 4
    "travel_muylejos_2": (0.529, 15.179, 1.607),
}


def pred_radio(radio_mm):
    arco = radio_mm * math.pi / 2
    return tiempo_corte_figura([_TramoFalso(arco, "arco", radio_mm)], [], False, V_TABLA, DELTA_CUT, A_MAX_CUT)


def pred_angulo(turn_deg):
    return tiempo_corte_figura([_TramoFalso(50.0), _TramoFalso(50.0)], [float(turn_deg)], False,
                               V_TABLA, DELTA_CUT, A_MAX_CUT)


def pred_recta(largo_mm):
    return tiempo_corte_figura([_TramoFalso(largo_mm)], [], False, V_TABLA, DELTA_CUT, A_MAX_CUT)


def pred_bloque1():
    preds = {}
    for r in [5, 15, 40, 100]:
        preds[f"radio_{r:02d}mm" if r < 100 else f"radio_{r}mm"] = pred_radio(r)
    for a in [15, 45, 90, 135, 165]:
        preds[f"angulo_{a:03d}deg"] = pred_angulo(a)
    for l in [20, 80, 250]:
        preds[f"recta_{l:03d}mm"] = pred_recta(l)
    return preds


def _saltos_y_angulos(xs, h):
    hh = h / 2.0
    puntos = [{"entrada": (x, -hh), "salida": (x, hh)} for x in xs]
    saltos, vecs = [], []
    for i in range(1, len(puntos)):
        dx = puntos[i]["entrada"][0] - puntos[i - 1]["salida"][0]
        dy = puntos[i]["entrada"][1] - puntos[i - 1]["salida"][1]
        vecs.append((dx, dy)); saltos.append((abs(dx), abs(dy)))
    angs = []
    for i in range(len(vecs) - 1):
        v1, v2 = vecs[i], vecs[i + 1]
        n1, n2 = math.hypot(*v1), math.hypot(*v2)
        cos_a = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2))) if n1 and n2 else 1.0
        angs.append(math.degrees(math.acos(cos_a)))
    return saltos, angs


def pred_bloque23(xs, h, travel_params):
    corte = len(xs) * tiempo_corte_figura([_TramoFalso(h)], [], False, V_TABLA, DELTA_CUT, A_MAX_CUT)
    saltos, angs = _saltos_y_angulos(xs, h)
    travel = tiempo_desplazamiento_saltos(saltos, angs, travel_params["v_rapido"],
                                          travel_params["delta"], travel_params["a_max"])
    return corte, travel


def refit_travel(rango_v, rango_a, delta=0.005, nombres=None):
    nombres = nombres or list(LAYOUT_BLOQUE23)
    casos = {n: (*LAYOUT_BLOQUE23[n], MEDIDO_BLOQUE23[n][1]) for n in nombres}
    mejor = None
    for v in rango_v:
        for a in rango_a:
            errs = []
            for xs, h, real in casos.values():
                saltos, angs = _saltos_y_angulos(xs, h)
                pred = tiempo_desplazamiento_saltos(saltos, angs, v, delta, a)
                errs.append(abs(pred - real) / real * 100)
            m, mx = sum(errs) / len(errs), max(errs)
            if mejor is None or m < mejor[0]:
                mejor = (m, mx, v, a)
    return mejor


if __name__ == "__main__":
    print("=== BLOQUE 1 — CORTE puro (parámetros SIN cambios: v_tabla=74.0, a_max=625, delta=0.2) ===")
    preds1 = pred_bloque1()
    errs1 = []
    for nombre, (cut_mm, real) in MEDIDO_BLOQUE1.items():
        pred = preds1[nombre]
        e = abs(pred - real) / real * 100
        errs1.append(e)
        print(f"  {nombre:16s} pred={pred:.4f}s  real={real:.4f}s  err={e:5.2f}%")
    print(f"  -> error medio={sum(errs1)/len(errs1):.2f}%  max={max(errs1):.2f}%")

    print("\n=== BLOQUE 2/3 — CORTE de los segmentos (sin cambios) ===")
    for nombre, (xs, h) in LAYOUT_BLOQUE23.items():
        corte_pred, _ = pred_bloque23(xs, h, TRAVEL_VIEJO)
        real = MEDIDO_BLOQUE23[nombre][0]
        e = abs(corte_pred - real) / real * 100
        print(f"  {nombre:20s} pred={corte_pred:.4f}s  real={real:.4f}s  err={e:5.2f}%")

    print("\n=== BLOQUE 2/3 — TRAVEL, parámetros VIEJOS (de Batería 2: v_rapido=129.5, a_max=750) ===")
    for nombre, (xs, h) in LAYOUT_BLOQUE23.items():
        _, travel_pred = pred_bloque23(xs, h, TRAVEL_VIEJO)
        real = MEDIDO_BLOQUE23[nombre][1]
        e = abs(travel_pred - real) / real * 100
        print(f"  {nombre:20s} pred={travel_pred:.4f}s  real={real:.4f}s  err={e:5.2f}%")

    print("\n=== Medición directa de v_max (tasa marginal entre los 2 saltos largos) ===")
    d1, d2 = 1000.05, 3000.02
    t1, t2 = MEDIDO_BLOQUE23["travel_muylejos_1"][1], MEDIDO_BLOQUE23["travel_muylejos_2"][1]
    v_marginal = (d2 - d1) / (t2 - t1)
    print(f"  (d2-d1)/(t2-t1) = ({d2}-{d1})/({t2}-{t1}) = {v_marginal:.2f} mm/s")
    print(f"  -> independiente de a_max (ambos puntos ya en crucero) -- MUY lejos del nominal 1650mm/s")

    print("\n=== Reajuste conjunto de TRAVEL con los 5 puntos (grid grueso + fino) ===")
    grueso = refit_travel(range(100, 260, 5), range(100, 2000, 25))
    print("  mejor grueso (err_medio,err_max,v_rapido,a_max):", grueso)
    fino = refit_travel([x / 10 for x in range(int(grueso[2] * 10 - 100), int(grueso[2] * 10 + 100))],
                        range(max(grueso[3] - 75, 25), grueso[3] + 75, 2))
    print("  mejor fino:", fino)
    TRAVEL_NUEVO_CALC = dict(v_rapido=fino[2], a_max=fino[3], delta=0.005)

    print("\n=== BLOQUE 2/3 — TRAVEL con el reajuste conjunto (5 puntos) ===")
    for nombre, (xs, h) in LAYOUT_BLOQUE23.items():
        _, travel_pred = pred_bloque23(xs, h, TRAVEL_NUEVO_CALC)
        real = MEDIDO_BLOQUE23[nombre][1]
        e = abs(travel_pred - real) / real * 100
        print(f"  {nombre:20s} pred={travel_pred:.4f}s  real={real:.4f}s  err={e:5.2f}%")

    print("\n=== Cruce honesto: ¿el reajuste nuevo sigue siendo consistente con Batería 2? ===")
    datos_b2 = cargar_geometria_precomputada()
    m_viejo, mx_viejo = error_medio_max_travel(datos_b2, TRAVEL_VIEJO["v_rapido"], TRAVEL_VIEJO["a_max"], TRAVEL_VIEJO["delta"])
    m_nuevo, mx_nuevo = error_medio_max_travel(datos_b2, TRAVEL_NUEVO_CALC["v_rapido"], TRAVEL_NUEVO_CALC["a_max"], TRAVEL_NUEVO_CALC["delta"])
    print(f"  TRAVEL viejo  contra Batería 2: err_medio={m_viejo:.2f}%  max={mx_viejo:.2f}%")
    print(f"  TRAVEL nuevo  contra Batería 2: err_medio={m_nuevo:.2f}%  max={mx_nuevo:.2f}%")
    m_corte, mx_corte = error_medio_max_corte(datos_b2, V_TABLA, A_MAX_CUT, DELTA_CUT)
    print(f"  CORTE (sin cambios) contra Batería 2: err_medio={m_corte:.2f}%  max={mx_corte:.2f}%")
