"""
bend_engine.py — Motor de cálculo de plegado (réplica del modelo Cybelec)
=========================================================================

Reimplementación abierta y verificable de los cálculos que hace un control
numérico de plegadora tipo Cybelec DNC/ModEva, aprendidos de los manuales de
referencia 2D (es), CYCAD y los documentos "bumped radius forming" del CD ADIRA.

Cubre las cuatro magnitudes que pide el control para cada pliegue:

  1. Longitud desarrollada (blank) .......... norma DIN 6935 + factor K por material
  2. Posición Y (penetración / ángulo) ...... geometría de plegado al aire + retorno elástico
  3. Posición X (tope trasero) .............. cotas - descuentos de fibra neutra
  4. Fuerza de plegado (tonelaje) ........... fórmula de plegado al aire

Unidades: mm, grados, N/mm² (MPa), toneladas.

Convención de ángulo:
  alpha = ángulo INTERIOR de la pieza terminada (90° = escuadra).
  beta  = ángulo de plegado = 180 - alpha (cuánto se dobla la chapa).
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field


# --------------------------------------------------------------------------
# 1. LONGITUD DESARROLLADA — DIN 6935
# --------------------------------------------------------------------------

def din6935_k(ri: float, s: float) -> float:
    """Factor de corrección k (posición de la fibra neutra) según DIN 6935.

        k = 0.65 + 0.5 * log10(ri/s)      para ri/s < 5
        k = 1.0                            para ri/s >= 5

    k va de ~0.5 (radios cerrados, fibra neutra hacia adentro) a 1.0.
    (Equivale a un k-factor de ingeniería = k/2, porque DIN lo refiere a s/2.)
    """
    if s <= 0:
        raise ValueError("espesor s debe ser > 0")
    ratio = ri / s
    if ratio >= 5.0:
        return 1.0
    k = 0.65 + 0.5 * math.log10(ratio)
    return max(0.0, min(1.0, k))


def din6935_v(beta_deg: float, ri: float, s: float) -> float:
    """Valor de compensación v (DIN 6935) para UN pliegue.

    Las cotas a, b de las alas se miden hasta el vértice exterior (mold line).
    El desarrollo total es:  L = sum(alas medidas al vértice) + sum(v)
    v es típicamente NEGATIVO (es el "descuento de plegado").

        beta  0..90°  : v = pi*beta/180 * (ri + k*s/2) - 2*(ri+s)*tan(beta/2)
        beta 90..165° : v = pi*beta/180 * (ri + k*s/2) - 2*(ri+s)*tan(beta/2)
        beta 165..180°: v = 0   (pliegue casi recto, sin deformación)

    (En DIN ambas franjas usan la misma forma; difieren en la práctica por
    cómo se acota la chapa. Mantenemos la fórmula geométrica única.)
    """
    if beta_deg <= 0:
        return 0.0
    if beta_deg >= 165.0:
        return 0.0
    k = din6935_k(ri, s)
    beta = math.radians(beta_deg)
    arco = (math.pi * beta_deg / 180.0) * (ri + k * s / 2.0)
    cuerda = 2.0 * (ri + s) * math.tan(beta / 2.0)
    return arco - cuerda


def desarrollo(alas, angulos_interiores, ri, s, k_material=1.0):
    """Longitud desarrollada total de una pieza.

    alas               : lista de longitudes de ala (al vértice exterior) [mm]
    angulos_interiores : lista de ángulos interiores de cada pliegue [°]
                         len = len(alas) - 1
    ri, s              : radio interno, espesor [mm]
    k_material         : factor empírico extra por material (la tabla "K" de
                         Cybelec, 0..9). 1.0 = norma DIN pura.
    """
    if len(angulos_interiores) != len(alas) - 1:
        raise ValueError("debe haber len(alas)-1 ángulos")
    L = sum(alas)
    detalle = []
    for alpha in angulos_interiores:
        beta = 180.0 - alpha
        v = din6935_v(beta, ri, s) * k_material
        L += v
        detalle.append({"alpha": alpha, "beta": beta, "v": round(v, 3)})
    return {"desarrollo": round(L, 3), "suma_alas": round(sum(alas), 3),
            "pliegues": detalle}


# --------------------------------------------------------------------------
# 2. POSICIÓN Y — penetración (plegado al aire) + retorno elástico
# --------------------------------------------------------------------------

def radio_interno_natural(V: float, s: float, factor: float = 0.16) -> float:
    """Radio interno que resulta naturalmente en plegado al aire.
    Regla práctica: ri ≈ V * factor  (factor ~0.16, es decir V/6 a V/8)."""
    return V * factor


def penetracion_Y(alpha_deg: float, V: float) -> float:
    """Profundidad de penetración de la punta del punzón por debajo de la
    línea de los hombros de la matriz, para formar el ángulo interior alpha
    en plegado AL AIRE (geometría pura, sin espesor ni radio):

        d = (V/2) * tan(beta/2)   con beta = 180 - alpha

    Para alpha=90 → d = V/2.   Es el corazón de la relación profundidad↔ángulo.
    """
    beta = 180.0 - alpha_deg
    return (V / 2.0) * math.tan(math.radians(beta / 2.0))


def sensibilidad_PMB(alpha_deg: float, V: float) -> float:
    """mm de profundidad necesarios para variar el ángulo 1° (|dd/dα|).
    Es la zona 'SENSIBILIDAD PMB' del manual: si < 0.05 mm/° conviene V mayor."""
    beta = 180.0 - alpha_deg
    # d = (V/2)*tan(beta/2);  dd/dalpha = (V/2)*(-1/2)*sec^2(beta/2)*(pi/180)
    sec2 = 1.0 / math.cos(math.radians(beta / 2.0)) ** 2
    return abs((V / 2.0) * 0.5 * sec2 * math.pi / 180.0)


# Tabla de compensación de retorno elástico (springback) — equivalente a la
# tabla "COMPENSACIÓN ELASTICIDAD" de Cybelec. Grados a SOBRE-plegar según
# material y franja de ángulo interior. Valores de ejemplo (ajustables en taller).
SPRINGBACK = {
    "ACERO":   [(76, 90, 2.5), (0, 76, 1.5), (90, 180, 1.0)],
    "INOX":    [(76, 90, 4.0), (0, 76, 2.5), (90, 180, 1.5)],
    "ALUMINIO":[(76, 90, 1.5), (0, 76, 1.0), (90, 180, 0.5)],
}


def springback_deg(material: str, alpha_deg: float) -> float:
    tabla = SPRINGBACK.get(material.upper())
    if not tabla:
        return 0.0
    for lo, hi, val in tabla:
        if lo <= alpha_deg < hi:
            return val
    return 0.0


def objetivo_Y(alpha_deg, V, material, ref_util=0.0, s=0.0):
    """Profundidad Y de consigna (PMB) para obtener alpha tras el retorno
    elástico. Se sobre-pliega: se forma a (alpha - springback)."""
    sb = springback_deg(material, alpha_deg)
    alpha_form = alpha_deg - sb
    d_geom = penetracion_Y(alpha_form, V)
    # El eje Y físico se referencia al útil; aquí devolvemos la penetración
    # geométrica (a sumar a la referencia del par punzón/matriz, ref_util).
    return {"alpha_objetivo": alpha_deg, "springback": sb,
            "alpha_a_formar": round(alpha_form, 2),
            "penetracion_mm": round(d_geom, 3),
            "Y_consigna_mm": round(ref_util + d_geom, 3),
            "sensibilidad_mm_por_grado": round(sensibilidad_PMB(alpha_form, V), 4)}


# --------------------------------------------------------------------------
# 3. POSICIÓN X — tope trasero
# --------------------------------------------------------------------------

def posiciones_X(alas, angulos_interiores, ri, s, k_material=1.0):
    """Cota del tope trasero para cada pliegue, plegando en orden 1..n desde
    un extremo. X = distancia desde la línea de plegado al borde apoyado.

    Modelo: se posiciona el borde libre contra el tope; para el pliegue i,
    X = (suma de alas detrás de la línea de plegado) corregida por el medio
    descuento de fibra neutra del propio pliegue.
    """
    n = len(angulos_interiores)
    res = []
    # plegamos desde el extremo del ala[0]; el material "detrás" del pliegue i
    # es la suma de alas 0..i menos las correcciones acumuladas.
    acumulado = 0.0
    for i in range(n):
        alpha = angulos_interiores[i]
        beta = 180.0 - alpha
        v = din6935_v(beta, ri, s) * k_material
        # cota cruda hasta el vértice de este pliegue
        cota = sum(alas[:i + 1])
        # la fibra neutra recorta medio descuento por delante de la línea
        x = cota + acumulado + v / 2.0
        acumulado += v
        res.append({"pliegue": i + 1, "alpha": alpha, "X_tope_mm": round(x, 3)})
    return res


# --------------------------------------------------------------------------
# 4. FUERZA DE PLEGADO — tonelaje (plegado al aire)
# --------------------------------------------------------------------------

def tonelaje(L_mm, s, Rm, V, coef=1.33):
    """Fuerza de plegado al aire.

        F[toneladas] = coef * Rm * L * s^2 / (V * 9810)

    coef ~1.33 (estándar). Cybelec usa un coeficiente propio (1.75 por defecto
    para aire en la tabla MATERIAL). Rm en N/mm², L y s y V en mm.
    """
    F_kN = coef * Rm * (L_mm / 1000.0) * (s ** 2) / V  # kN
    return {"fuerza_kN": round(F_kN, 1), "fuerza_ton": round(F_kN / 9.81, 2),
            "V_recomendada_mm": round(8 * s, 1)}


# --------------------------------------------------------------------------
# DEMO / autovalidación
# --------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 68)
    print("DEMO motor de plegado — pieza tipo U (3 alas, 2 pliegues a 90°)")
    print("=" * 68)
    alas = [50.0, 80.0, 50.0]
    ang = [90.0, 90.0]
    s = 2.0
    V = 16.0
    ri = radio_interno_natural(V, s)
    Rm = 400.0  # acero S235 aprox
    print(f"espesor={s}  V={V}  ri_natural={ri:.2f}  Rm={Rm}")
    print()
    d = desarrollo(alas, ang, ri, s)
    print("1) DESARROLLO:")
    for p in d["pliegues"]:
        print(f"   pliegue alpha={p['alpha']}° beta={p['beta']}° v(descuento)={p['v']} mm")
    print(f"   suma alas={d['suma_alas']}  ->  blank desarrollado = {d['desarrollo']} mm")
    print()
    print("2) POSICIÓN Y (penetración) con retorno elástico (ACERO):")
    for a in ang:
        y = objetivo_Y(a, V, "ACERO")
        print(f"   alpha={a}° -> sobreplegar {y['springback']}° -> penetración "
              f"{y['penetracion_mm']} mm  (sensib {y['sensibilidad_mm_por_grado']} mm/°)")
    print()
    print("3) POSICIÓN X (tope trasero):")
    for x in posiciones_X(alas, ang, ri, s):
        print(f"   pliegue {x['pliegue']} alpha={x['alpha']}° -> X = {x['X_tope_mm']} mm")
    print()
    print("4) TONELAJE (sobre 1 m de plegado):")
    t = tonelaje(1000.0, s, Rm, V)
    print(f"   F = {t['fuerza_ton']} ton/m  ({t['fuerza_kN']} kN)  "
          f"V recomendada para s={s}: {t['V_recomendada_mm']} mm")
    print()
    print("--- chequeos geométricos ---")
    print(f"penetración 90° con V=16  -> {penetracion_Y(90,16):.3f}  (debe ser V/2 = 8.0)")
    print(f"k DIN para ri/s=1         -> {din6935_k(2,2):.3f}  (debe ~0.65)")
    print(f"k DIN para ri/s>=5        -> {din6935_k(10,2):.3f}  (debe 1.0)")
