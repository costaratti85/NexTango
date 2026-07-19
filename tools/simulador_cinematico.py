#!/usr/bin/env python3
"""Simulador de movimiento — ETAPA 2: motor cinemático TRAPEZOIDAL + Junction Deviation.

Principio (Constantino, 2026-07-17): empezar SIMPLE — aceleración constante (como GRBL real,
confirmado contra su código fuente: no usa jerk), no S-curve. Se agrega jerk solo si la
calibración no llega al ~13-15% de error (benchmark realista para láser, según la
investigación bibliográfica — no <5%, eso es de fresado de alta precisión).

MODELO:
  - Cada TRAMO (línea o arco, de la Etapa 1) se recorre con un perfil trapezoidal: acelera a
    a_max constante, crucero si el tramo es largo, decelera a a_max constante — entre una
    velocidad de entrada v_in y una de salida v_out, sin exceder v_max (la menor entre la
    velocidad de tabla del material y, si es arco, la limitada por curvatura √(a_max·radio)).
  - v_in / v_out de cada tramo salen de la velocidad de ESQUINA en cada vértice
    (Junction Deviation, según el ÁNGULO real del vértice — ver
    velocidad_esquina_junction_deviation, derivada y verificada geométricamente en el
    brainstorm anterior, coincide con el código real de GRBL y el blog original de Sonny Jeon).
  - LOOK-AHEAD (reverse + forward pass, como GRBL): a diferencia de GRBL (que planea sobre
    un buffer LIMITADO en tiempo real), acá conocemos TODO el camino de antemano — el
    look-ahead se aplica de una sola pasada sobre la secuencia completa de tramos, sin
    restricción de buffer.
  - CORTE: la velocidad es ESCALAR a lo largo de la trayectoria (como el "feedrate" de
    cualquier CNC — Junction Deviation es una restricción de magnitud de velocidad, no una
    restricción por eje).
  - DESPLAZAMIENTO (travel, saltos): por pedido explícito, se modela POR EJE — cada salto
    recto se descompone en un sub-problema 1D por eje (X e Y), cada uno con su propia
    velocidad proyectada de entrada/salida/techo, y el tiempo real del salto es el máximo
    entre los dos ejes (el más lento manda) — coherente con que los motores XY son
    independientes.

⚠️ RIESGO YA MARCADO, sin cambios: el orden de recorrido ENTRE figuras (saltos) sigue siendo
un supuesto sin validar contra CypCut (boustrophedon — ver analisis_laser_fisico.py). Este
módulo no lo resuelve, solo consume la secuencia de ángulos/distancias que le llegue.
"""
from __future__ import annotations

import math

try:
    import numpy as np
except ImportError as e:
    raise SystemExit(f"Falta numpy ({e}). Activá el venv: source .venv/bin/activate")


# ---------------------------------------------------------------------------------------------------------------------
# 1) Velocidad de esquina — Junction Deviation (ya derivada/verificada, trasladada a código)
# ---------------------------------------------------------------------------------------------------------------------

V_INFINITO = 1e12  # "sin límite" (ángulo ~0°, sigue derecho)


def velocidad_esquina_junction_deviation(angulo_giro_grados: float, delta_mm: float, a_max: float) -> float:
    """Velocidad máxima de esquina (magnitud, mm/s) para un vértice con ángulo de giro dado.

    angulo_giro_grados: 0° = sigue derecho (sin límite), 180° = revierte (v=0).
    delta_mm: "junction deviation" — parámetro de ajuste, NO una medida física real de la
      máquina (aclarado por Sonny Jeon en su blog original — ver investigación bibliográfica).
    a_max: aceleración máxima permitida (centrípeta) — mm/s².

    R = δ·sin(φ)/(1−sin(φ)), φ=(180°−α)/2 ; v = √(a_max·R). Verificado geométricamente:
    α=0→R=∞ (sin freno); α=180°→R=0 (frena a full).
    """
    alpha = math.radians(angulo_giro_grados)
    phi = (math.pi - alpha) / 2.0
    s = math.sin(phi)
    if s >= 1.0 - 1e-12:
        return V_INFINITO
    if s <= 1e-12:
        return 0.0
    R = delta_mm * s / (1.0 - s)
    return math.sqrt(a_max * R)


# ---------------------------------------------------------------------------------------------------------------------------------------
# 2) Perfil trapezoidal (aceleración constante) — tiempo de un tramo 1D
# ---------------------------------------------------------------------------------------------------------------------

def perfil_trapezoidal_tiempo(d: float, v_in: float, v_out: float, v_max: float, a_max: float) -> tuple:
    """Tiempo mínimo para recorrer distancia d (mm), con aceleración constante ±a_max,
    entre velocidad de entrada v_in y de salida v_out, sin exceder v_max.

    Devuelve (tiempo_s, v_pico_alcanzado).

    NOTA IMPORTANTE (encontrada al verificar): esta función asume v_in/v_out ya
    "saneadas" por el look-ahead — es decir, que existe un perfil físicamente
    coherente para cubrir d sin violar a_max. Si se la llama con v_in
    artificialmente alta para un d muy corto (sin pasar por el look-ahead antes),
    puede devolver un v_pico > max(v_in, v_out) — matemáticamente es la solución de
    tiempo mínimo del problema, pero indica que v_in no venía saneada. En este
    módulo, look_ahead() se encarga de que eso no ocurra en la práctica.
    """
    if d <= 0:
        return 0.0, min(v_in, v_out)

    v_pico_sq = a_max * d + (v_in ** 2 + v_out ** 2) / 2.0
    v_pico = math.sqrt(max(v_pico_sq, 0.0))

    if v_pico <= v_max:
        t_acc = max((v_pico - v_in) / a_max, 0.0)
        t_dec = max((v_pico - v_out) / a_max, 0.0)
        return t_acc + t_dec, v_pico

    d_acc = max(v_max ** 2 - v_in ** 2, 0.0) / (2.0 * a_max)
    d_dec = max(v_max ** 2 - v_out ** 2, 0.0) / (2.0 * a_max)
    d_crucero = max(d - d_acc - d_dec, 0.0)
    t_acc = max(v_max - v_in, 0.0) / a_max
    t_dec = max(v_max - v_out, 0.0) / a_max
    t_cru = d_crucero / v_max if v_max > 0 else 0.0
    return t_acc + t_dec + t_cru, v_max


# ---------------------------------------------------------------------------------------------------------------------------
# 3) Look-ahead: reverse pass + forward pass sobre TODA la secuencia (sin buffer limitado)
# ---------------------------------------------------------------------------------------------------------------------

def look_ahead(distancias: list, v_techo: list, v_esquina: list, a_max: float) -> list:
    """Calcula (v_entrada, v_salida) saneadas para cada tramo de una secuencia.

    distancias:  [d_0, d_1, ..., d_{n-1}]         longitud de cada tramo (mm)
    v_techo:     [vt_0, ..., vt_{n-1}]             velocidad techo de CADA tramo
                 (menor entre tabla de material y límite de curvatura si es arco)
    v_esquina:   [ve_01, ve_12, ..., ve_{n-2,n-1}] velocidad de esquina en cada unión
                 ENTRE tramos consecutivos (longitud n-1) — de
                 velocidad_esquina_junction_deviation(). El primer y último tramo
                 arrancan/terminan en reposo (v=0) — el camino completo empieza y
                 termina detenido.
    a_max: aceleración máxima (mm/s²), misma para todo el recorrido.

    Devuelve: [(v_in_0, v_out_0), (v_in_1, v_out_1), ...] — n pares.

    Réplica de la lógica reverse/forward pass de GRBL (confirmada contra su código
    fuente real), simplificada porque acá conocemos TODO el camino de antemano — no
    hay restricción de tamaño de buffer como en el hardware embebido real.
    """
    n = len(distancias)
    if n == 0:
        return []
    if n == 1:
        return [(0.0, 0.0)]

    # límites de entrada por "techo" propio y por la esquina compartida con el vecino
    max_entrada = [0.0] * n
    max_entrada[0] = 0.0  # arranca en reposo
    for i in range(1, n):
        max_entrada[i] = min(v_techo[i], v_esquina[i - 1])
    max_salida = [0.0] * n
    for i in range(n - 1):
        max_salida[i] = min(v_techo[i], v_esquina[i])
    max_salida[n - 1] = 0.0  # termina en reposo

    # REVERSE PASS: de atrás para adelante, capar la entrada por lo que se puede
    # decelerar a tiempo dado el límite de salida ya fijado del tramo siguiente
    entrada = list(max_entrada)
    salida = list(max_salida)
    salida[n - 1] = 0.0
    for i in range(n - 1, -1, -1):
        limite_por_salida = math.sqrt(salida[i] ** 2 + 2 * a_max * distancias[i])
        entrada[i] = min(entrada[i], limite_por_salida)
        if i > 0:
            # la salida del tramo anterior es la entrada de este (misma unión)
            salida[i - 1] = min(salida[i - 1], entrada[i])

    # FORWARD PASS: de adelante para atrás, si acelerando desde la entrada ya
    # fijada no se alcanza la salida propuesta, hay que bajarla
    entrada[0] = 0.0
    for i in range(n):
        limite_por_entrada = math.sqrt(entrada[i] ** 2 + 2 * a_max * distancias[i])
        salida[i] = min(salida[i], limite_por_entrada)
        if i < n - 1:
            entrada[i + 1] = min(entrada[i + 1], salida[i])

    return list(zip(entrada, salida))


def look_ahead_ciclico(distancias: list, v_techo: list, v_esquina: list, a_max: float,
                       repeticiones: int = 3) -> list:
    """Como look_ahead, pero para una secuencia CERRADA (cíclica): el último
    tramo empalma con el primero por la esquina de cierre, sin pasar por reposo.

    v_esquina acá tiene longitud n (una por CADA unión, incluida la de cierre
    entre el último tramo y el primero — a diferencia de look_ahead lineal,
    donde es n-1 porque los extremos no empalman).

    MOTIVO DEL BUG QUE ESTO CORRIGE: look_ahead() lineal fuerza reposo (v=0) en
    el primer y último tramo de la secuencia — correcto para un desplazamiento
    que arranca/termina detenido, pero FALSO para un contorno cerrado (un
    agujero), donde la costura (punto de inicio/cierre del corte) no implica
    ninguna parada real de la máquina. Verificado: sin esta corrección, cada
    agujero de Batería 2 salía con >100% de error (una frenada completa espuria
    en cada costura); con la corrección, el error baja al rango esperado.

    Técnica: "desenrollar" el ciclo repitiéndolo `repeticiones` veces seguidas
    (con reposo solo en los extremos verdaderos del array 3x más largo) y
    devolver los pares de la copia del MEDIO — para entonces el efecto de los
    extremos artificiales ya se disipó (cada esquina cicla localmente, no hay
    arrastre de largo alcance porque a_max es alto respecto de las distancias
    típicas). 3 repeticiones alcanzan en la práctica (verificado con casos
    sintéticos: converge ya en la 2da copia).
    """
    n = len(distancias)
    if n == 0:
        return []
    # NO hay atajo para n==1: una figura cerrada de UN solo tramo (ej. un
    # círculo completo) SÍ tiene una unión real consigo misma (v_esquina[0]) —
    # el desenrollado general de abajo la resuelve correctamente (a diferencia
    # de look_ahead() lineal, donde n==1 SÍ es genuinamente reposo-a-reposo).

    d_larga = distancias * repeticiones
    vt_larga = v_techo * repeticiones
    # v_esquina cíclico (n valores) -> entre copias consecutivas, la unión N-1
    # repite la MISMA esquina de cierre real; se arma la lista lineal de
    # longitud n*repeticiones - 1 rotando v_esquina en cada empalme.
    ve_larga = []
    for _ in range(repeticiones):
        ve_larga.extend(v_esquina)
    ve_larga = ve_larga[:-1]  # el look_ahead lineal espera n_total - 1 esquinas

    pares_largos = look_ahead(d_larga, vt_larga, ve_larga, a_max)
    medio_ini = n * (repeticiones // 2)
    return pares_largos[medio_ini:medio_ini + n]


# ---------------------------------------------------------------------------------------------------------------------------------------------------
# 4) CORTE — velocidad escalar a lo largo de la trayectoria (como el feedrate de un CNC)
# ---------------------------------------------------------------------------------------------------------------------

def tiempo_corte_figura(tramos: list, angulos_vertice_grados: list, cerrada: bool,
                        v_tabla_mm_s: float, delta_mm: float, a_max: float) -> float:
    """Tiempo de cortar UNA figura (los tramos ya vienen de Etapa 1, con sus
    ángulos de vértice reales). v_techo por tramo = min(v_tabla, √(a_max·radio) si es
    arco). Aplica look-ahead sobre toda la figura — cíclico si es cerrada (ver
    look_ahead_ciclico), lineal con reposo en los extremos si es abierta."""
    n = len(tramos)
    if n == 0:
        return 0.0
    distancias = [t.longitud_mm for t in tramos]
    v_techo = [
        min(v_tabla_mm_s, math.sqrt(a_max * t.radio_mm)) if t.tipo == "arco" else v_tabla_mm_s
        for t in tramos
    ]

    if cerrada and n == 1:
        # figura cerrada de UN solo tramo (ej. un círculo completo): la unión
        # consigo misma es perfectamente tangente (0° de giro real) -> sin
        # freno alguno, cruza a v_techo todo el recorrido. parsear_figuras no
        # emite un ángulo de cierre para n==1 (lista vacía), así que se
        # construye acá explícitamente en vez de asumir reposo.
        v_esquina = [velocidad_esquina_junction_deviation(0.0, delta_mm, a_max)]
        pares = look_ahead_ciclico(distancias, v_techo, v_esquina, a_max)
    elif cerrada and len(angulos_vertice_grados) == n:
        # cerrada: n esquinas (incluida la de cierre entre el último tramo y el
        # primero, que en parsear_figuras queda al final de la lista)
        v_esquina = [velocidad_esquina_junction_deviation(a, delta_mm, a_max)
                    for a in angulos_vertice_grados]
        pares = look_ahead_ciclico(distancias, v_techo, v_esquina, a_max)
    else:
        # abierta: n-1 esquinas (entre tramos consecutivos), reposo real en
        # ambos extremos (arranca y termina detenida)
        v_esquina = [velocidad_esquina_junction_deviation(a, delta_mm, a_max)
                    for a in angulos_vertice_grados[:max(n - 1, 0)]]
        pares = look_ahead(distancias, v_techo, v_esquina, a_max)

    total = 0.0
    for d, (v_in, v_out), vt in zip(distancias, pares, v_techo):
        t, _ = perfil_trapezoidal_tiempo(d, v_in, v_out, vt, a_max)
        total += t
    return total


# ---------------------------------------------------------------------------------------------------------------------------------------------------------
# 5) DESPLAZAMIENTO (travel) — POR EJE, en diagonal manda el eje más lento
# ---------------------------------------------------------------------------------------------------------------------

def tiempo_desplazamiento_saltos(saltos_dx_dy: list, angulos_giro_grados: list,
                                 v_rapido_mm_s: float, delta_mm: float, a_max: float) -> float:
    """Tiempo total de una secuencia de saltos rectos (dx, dy) — como el
    desplazamiento entre agujeros. Cada salto se descompone POR EJE: primero se
    calcula la velocidad ESCALAR de esquina/techo a lo largo de la secuencia (igual
    que en el corte), y luego esa velocidad escalar se proyecta sobre cada eje
    (según la dirección del salto) para resolver el perfil trapezoidal 1D de cada
    eje por separado — el tiempo del salto es el máximo entre los dos ejes.
    """
    n = len(saltos_dx_dy)
    if n == 0:
        return 0.0
    distancias = [math.hypot(dx, dy) for dx, dy in saltos_dx_dy]
    v_techo = [v_rapido_mm_s] * n
    v_esquina = [
        velocidad_esquina_junction_deviation(ang, delta_mm, a_max)
        for ang in angulos_giro_grados[:n - 1]
    ]
    pares_escalares = look_ahead(distancias, v_techo, v_esquina, a_max)

    total = 0.0
    for (dx, dy), d, (v_in, v_out) in zip(saltos_dx_dy, distancias, pares_escalares):
        if d <= 0:
            continue
        ux, uy = abs(dx) / d, abs(dy) / d  # fracción de la magnitud proyectada en cada eje
        t_x, _ = perfil_trapezoidal_tiempo(abs(dx), v_in * ux, v_out * ux, v_rapido_mm_s * ux, a_max)
        t_y, _ = perfil_trapezoidal_tiempo(abs(dy), v_in * uy, v_out * uy, v_rapido_mm_s * uy, a_max)
        total += max(t_x, t_y)
    return total
