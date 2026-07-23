#!/usr/bin/env python3
"""Deriva PIERCE_SECONDS_SIN_FLYCUT desde datos REALES (Delay_s de Batería 2,
DESGLOSE_BATERIA2 en analisis_laser_fisico.py) — no un valor prescripto.

Constantino observó en vivo que la máquina empieza a bajar ANTES de llegar al
punto de perforación (el pierce se solapa con el posicionamiento) -- 3.0s
(el valor prescripto actual) es una sobreestimación. Pide el número real,
derivado con el mismo rigor auditable que β (informe de MSG_134/137).

Método: regresión lineal de Delay_s contra pierce_count real (n_agujeros + 1
por el contorno -- cada panel de Batería 2 es una grilla de agujeros DENTRO
de un contorno rectangular, y el contorno también necesita su propio pierce
para empezar a cortar). Se prueba con y sin el +1 del contorno para confirmar
cuál da un ajuste más consistente entre los 12 paneles (la razón Delay/pierce
casi constante entre paneles es la evidencia de que el conteo es correcto).

ACTUALIZACIÓN 2026-07-23: Constantino confirmó "agujeros + contorno" como la
convención correcta (coincide con la que da el ajuste más ajustado acá) y
`calculate_pierce_count()` en legacy_panel_adapter.py ya cuenta el contorno.
La rama "CON contorno" de este script es ahora la que corresponde a
producción -- gamma=0.7187, redondeado a 0.72 por Constantino (0.18% de
diferencia contra el valor exacto de la regresión).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from analisis_laser_fisico import (
    _BATERIA2_DIR, _PANELES_B2, DESGLOSE_BATERIA2, segmentos_de_corte,
)


def pierce_counts():
    """n_agujeros (sin contorno) por panel, leído de los DXF reales."""
    out = {}
    for nombre in _PANELES_B2:
        key = nombre.split("_L")[0]
        path = _BATERIA2_DIR / f"{nombre}.dxf"
        out[key] = len(segmentos_de_corte(path))
    return out


def regresion_por_origen(xs, ys):
    """gamma = sum(x*y) / sum(x^2) -- minimos cuadrados forzando Delay=0 en
    pierce=0 (no hay motivo fisico para un termino constante independiente
    del numero de perforaciones)."""
    sxy = sum(x * y for x, y in zip(xs, ys))
    sxx = sum(x * x for x in xs)
    return sxy / sxx


def regresion_con_intercepto(xs, ys):
    """OLS clasico (pendiente + ordenada al origen) -- para chequear si hay
    un termino fijo por panel que la regresion por origen esconde."""
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    b = sxy / sxx
    a = my - b * mx
    return b, a


if __name__ == "__main__":
    n_holes = pierce_counts()

    print("=== Delay_s / pierce_count por panel — comparando +1 (contorno) vs sin +1 ===")
    print(f"{'panel':8} {'n_holes':>8} {'delay_s':>10} {'delay/n_holes':>14} {'delay/(n_holes+1)':>18}")
    for key in n_holes:
        nh = n_holes[key]
        d = DESGLOSE_BATERIA2[key]["delay_s"]
        print(f"{key:8} {nh:8d} {d:10.3f} {d/nh:14.4f} {d/(nh+1):18.4f}")

    xs_sin = [n_holes[k] for k in n_holes]
    xs_con = [n_holes[k] + 1 for k in n_holes]
    ys = [DESGLOSE_BATERIA2[k]["delay_s"] for k in n_holes]

    ratios_sin = [d / n for d, n in zip(ys, xs_sin)]
    ratios_con = [d / n for d, n in zip(ys, xs_con)]
    print(f"\nrango delay/n_holes (sin contorno):      {min(ratios_sin):.4f} - {max(ratios_sin):.4f} "
         f"(spread {(max(ratios_sin)-min(ratios_sin))/min(ratios_sin)*100:.1f}%)")
    print(f"rango delay/(n_holes+1) (con contorno):  {min(ratios_con):.4f} - {max(ratios_con):.4f} "
         f"(spread {(max(ratios_con)-min(ratios_con))/min(ratios_con)*100:.1f}%)")

    print("\n=== Regresión por origen (Delay = gamma * pierce_count, sin termino constante) ===")
    g_sin = regresion_por_origen(xs_sin, ys)
    g_con = regresion_por_origen(xs_con, ys)
    print(f"  SIN contorno (pierce=n_holes):        gamma = {g_sin:.4f} s/perforación")
    print(f"  CON contorno (pierce=n_holes+1):      gamma = {g_con:.4f} s/perforación")

    print("\n=== Regresión OLS con ordenada al origen (chequeo de termino fijo) ===")
    b_sin, a_sin = regresion_con_intercepto(xs_sin, ys)
    b_con, a_con = regresion_con_intercepto(xs_con, ys)
    print(f"  SIN contorno: Delay = {b_sin:.4f}*n_holes + {a_sin:.3f}")
    print(f"  CON contorno: Delay = {b_con:.4f}*(n_holes+1) + {a_con:.3f}")

    print("\n=== Error del modelo CON contorno (gamma por origen) contra los 12 paneles reales ===")
    errs = []
    for key in n_holes:
        pred = g_con * (n_holes[key] + 1)
        real = DESGLOSE_BATERIA2[key]["delay_s"]
        e = abs(pred - real) / real * 100
        errs.append(e)
        print(f"  {key:8} pred={pred:9.3f}  real={real:9.3f}  err={e:5.2f}%")
    print(f"  -> error medio={sum(errs)/len(errs):.2f}%  max={max(errs):.2f}%")
