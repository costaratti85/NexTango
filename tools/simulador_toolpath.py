#!/usr/bin/env python3
"""Simulador de movimiento — ETAPA 1: parser de toolpath genérico.

Descompone CUALQUIER DXF (LINE, ARC, CIRCLE, LWPOLYLINE — las SPLINE ya vienen convertidas
a estos tipos antes de llegar al motor, ver dxf_validator.py) en el recorrido real, tramo
por tramo, con los ángulos reales de cada vértice. Sirve igual para una grilla de agujeros
que para una silueta orgánica (Corazón, Gotas) — la geometría entra por el recorrido, no
por un escalar.

⚠️ SUPUESTOS DE ORDEN DE RECORRIDO (el riesgo que ya mordió antes — documentado a propósito,
no asumido en silencio):

1. DENTRO de una figura cerrada (ej. el contorno de un agujero, o de un Corazón): las
   entidades se encadenan por CONTINUIDAD GEOMÉTRICA (el punto final de una coincide con el
   inicial de la siguiente, dentro de tolerancia). Esto es casi objetivo — un contorno bien
   formado solo tiene una forma de conectarse por continuidad — PERO el PUNTO DE
   INICIO/CIERRE (dónde el láser "prende" y "apaga" el haz) y el SENTIDO de recorrido
   (horario/antihorario) SÍ son una elección arbitraria de este parser: toma la primera
   entidad tal como aparece en el archivo DXF como punto de partida. No hay forma de
   confirmar esto contra CypCut sin telemetría real de la máquina.

2. ENTRE figuras distintas (agujero a agujero, salto de "rápido"): este módulo NO decide el
   orden — lo calcula quien arme la secuencia de saltos aguas arriba (ver
   analisis_laser_fisico.py::ordenar_boustrophedon, ya usado y ya documentado como supuesto
   no verificado). Acá solo se resuelve el recorrido DENTRO de cada figura.

USO:
    from simulador_toolpath import parsear_figuras
    figuras = parsear_figuras("panel.dxf")
    # figuras: lista de {"tramos": [Tramo, ...], "angulos_vertice": [grados, ...], "cerrada": bool}
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

try:
    import ezdxf
except ImportError as e:
    raise SystemExit(f"Falta ezdxf ({e}). Activá el venv: source .venv/bin/activate")


TOL_PUNTO_MM = 1e-3  # tolerancia para considerar dos puntos "el mismo" al encadenar


# ---------------------------------------------------------------------------------------------
# 1) Estructura de un TRAMO (segmento recto o arco)
# ---------------------------------------------------------------------------------------------------

@dataclass
class Tramo:
    tipo: str                  # "linea" | "arco"
    longitud_mm: float
    p_inicio: tuple             # (x, y)
    p_fin: tuple                # (x, y)
    dir_entrada: tuple          # vector unitario (dx, dy), tangente en p_inicio, sentido de avance
    dir_salida: tuple           # vector unitario (dx, dy), tangente en p_fin, sentido de avance
    radio_mm: float | None = None   # solo arcos
    centro: tuple | None = None     # solo arcos


# ---------------------------------------------------------------------------------------------------
# 2) Normalización de entidades DXF crudas -> dict común
# ---------------------------------------------------------------------------------------------------------------------

def _normalizar_line(e) -> dict:
    return {"tipo": "linea", "p_inicio": (e.dxf.start.x, e.dxf.start.y),
            "p_fin": (e.dxf.end.x, e.dxf.end.y)}


def _normalizar_arc(e) -> dict:
    cx, cy = e.dxf.center.x, e.dxf.center.y
    r = e.dxf.radius
    a0 = math.radians(e.dxf.start_angle)
    a1 = math.radians(e.dxf.end_angle)
    if a1 <= a0:
        a1 += 2 * math.pi
    return {
        "tipo": "arco", "centro": (cx, cy), "radio_mm": r,
        "angulo_inicio_rad": a0, "angulo_fin_rad": a1,
        "p_inicio": (cx + r * math.cos(a0), cy + r * math.sin(a0)),
        "p_fin": (cx + r * math.cos(a1), cy + r * math.sin(a1)),
    }


def _normalizar_circle(e) -> dict:
    cx, cy = e.dxf.center.x, e.dxf.center.y
    r = e.dxf.radius
    return {
        "tipo": "arco", "centro": (cx, cy), "radio_mm": r,
        "angulo_inicio_rad": 0.0, "angulo_fin_rad": 2 * math.pi,
        "p_inicio": (cx + r, cy), "p_fin": (cx + r, cy),  # cerrado sobre sí mismo
        "es_circulo_completo": True,
    }


def _bulge_a_arco(p0: tuple, p1: tuple, bulge: float) -> dict:
    """Convierte un segmento de LWPOLYLINE con bulge≠0 en un arco.

    bulge = tan(theta/4), donde theta es el ángulo subtendido por el arco
    (positivo = CCW, negativo = CW). Fórmula estándar DXF.
    """
    theta = 4.0 * math.atan(bulge)
    chord = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    if abs(math.sin(theta / 2.0)) < 1e-12 or chord < 1e-9:
        # bulge degenerado -> tratar como línea
        return {"tipo": "linea", "p_inicio": p0, "p_fin": p1}
    r = chord / (2.0 * math.sin(theta / 2.0))
    r = abs(r)
    # punto medio de la cuerda
    mx, my = (p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0
    # dirección perpendicular a la cuerda, hacia el centro
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    # apotema (distancia del centro a la cuerda); signo según bulge
    sagita = chord / 2.0 * bulge  # aprox valida para |bulge| chico y grande usando theta real abajo
    apotema = math.sqrt(max(r * r - (chord / 2.0) ** 2, 0.0))
    signo = 1.0 if bulge > 0 else -1.0
    # normal a la cuerda, rotada 90° en la dirección correspondiente
    nx, ny = -uy, ux
    cx, cy = mx + signo * apotema * nx, my + signo * apotema * ny
    a0 = math.atan2(p0[1] - cy, p0[0] - cx)
    a1 = math.atan2(p1[1] - cy, p1[0] - cx)
    if bulge > 0 and a1 <= a0:
        a1 += 2 * math.pi
    if bulge < 0 and a1 >= a0:
        a1 -= 2 * math.pi
    return {
        "tipo": "arco", "centro": (cx, cy), "radio_mm": r,
        "angulo_inicio_rad": a0, "angulo_fin_rad": a1,
        "p_inicio": p0, "p_fin": p1,
    }


def _normalizar_lwpolyline(e) -> list:
    """Devuelve una lista de entidades normalizadas, una por cada lado de la polyline
    (línea si bulge=0, arco si bulge≠0)."""
    pts = list(e.get_points())  # (x, y, start_width, end_width, bulge)
    out = []
    n = len(pts)
    rango = range(n) if e.closed else range(n - 1)
    for i in rango:
        p0 = (pts[i][0], pts[i][1])
        p1 = (pts[(i + 1) % n][0], pts[(i + 1) % n][1])
        bulge = pts[i][4]
        if abs(bulge) < 1e-9:
            out.append({"tipo": "linea", "p_inicio": p0, "p_fin": p1})
        else:
            out.append(_bulge_a_arco(p0, p1, bulge))
    return out


def extraer_entidades(dxf_path, layer: str | None = None) -> list:
    """Lee un DXF y devuelve una lista de entidades normalizadas (dicts), SIN ordenar
    ni agrupar en figuras. Soporta LINE, ARC, CIRCLE, LWPOLYLINE (con bulge)."""
    doc = ezdxf.readfile(str(dxf_path))
    out = []
    for e in doc.modelspace():
        if layer is not None and e.dxf.layer != layer:
            continue
        t = e.dxftype()
        if t == "LINE":
            out.append(_normalizar_line(e))
        elif t == "ARC":
            out.append(_normalizar_arc(e))
        elif t == "CIRCLE":
            out.append(_normalizar_circle(e))
        elif t == "LWPOLYLINE":
            out.extend(_normalizar_lwpolyline(e))
        # otros tipos (TEXT, DIMENSION, etc.) se ignoran silenciosamente — no son toolpath
    return out


# ---------------------------------------------------------------------------------------------------------------------
# 3) Agrupar entidades en FIGURAS (componentes conexas por punto compartido)
# ---------------------------------------------------------------------------------------------------------------------

def _puntos_iguales(a: tuple, b: tuple, tol: float = TOL_PUNTO_MM) -> bool:
    return math.hypot(a[0] - b[0], a[1] - b[1]) < tol


class _UnionFind:
    def __init__(self, n):
        self.padre = list(range(n))

    def find(self, x):
        while self.padre[x] != x:
            self.padre[x] = self.padre[self.padre[x]]
            x = self.padre[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.padre[ra] = rb


def agrupar_en_figuras(entidades: list) -> list:
    """Agrupa entidades en componentes conexas por punto extremo compartido
    (dos entidades pertenecen a la misma figura si comparten un extremo dentro de
    tolerancia). Devuelve lista de listas de índices en `entidades`."""
    n = len(entidades)
    uf = _UnionFind(n)
    for i in range(n):
        for j in range(i + 1, n):
            pi = (entidades[i]["p_inicio"], entidades[i]["p_fin"])
            pj = (entidades[j]["p_inicio"], entidades[j]["p_fin"])
            if any(_puntos_iguales(a, b) for a in pi for b in pj):
                uf.union(i, j)
    grupos: dict = {}
    for i in range(n):
        r = uf.find(i)
        grupos.setdefault(r, []).append(i)
    return list(grupos.values())


# ---------------------------------------------------------------------------------------------------------------------
# 4) Encadenar una figura (ordenar sus entidades por continuidad geométrica)
# ---------------------------------------------------------------------------------------------------------------------------

def encadenar_figura(entidades_grupo: list) -> tuple:
    """Ordena las entidades de UNA figura en una cadena continua.

    Punto de partida: la PRIMERA entidad tal como aparece en el DXF (elección
    arbitraria, documentada — ver docstring del módulo). Devuelve
    (lista_ordenada_orientada, cerrada: bool). Cada entidad en la lista de salida
    ya viene orientada en el sentido de recorrido (si había que "voltearla" para
    encajar, p_inicio/p_fin — y para arcos, los ángulos — se intercambian).
    """
    restantes = list(entidades_grupo)
    cadena = [restantes.pop(0)]
    while restantes:
        punto_actual = cadena[-1]["p_fin"]
        encontrado = None
        for idx, cand in enumerate(restantes):
            if _puntos_iguales(cand["p_inicio"], punto_actual):
                encontrado = (idx, cand, False)
                break
            if _puntos_iguales(cand["p_fin"], punto_actual):
                encontrado = (idx, cand, True)
                break
        if encontrado is None:
            break  # cadena abierta / no se pudo seguir conectando
        idx, cand, volteada = encontrado
        if volteada:
            cand = _voltear_entidad(cand)
        cadena.append(cand)
        restantes.pop(idx)
    cerrada = len(restantes) == 0 and _puntos_iguales(cadena[0]["p_inicio"], cadena[-1]["p_fin"])
    return cadena, cerrada


def _voltear_entidad(e: dict) -> dict:
    """Invierte el sentido de recorrido de una entidad (para encadenarla en la
    dirección que hace falta)."""
    e2 = dict(e)
    e2["p_inicio"], e2["p_fin"] = e["p_fin"], e["p_inicio"]
    if e["tipo"] == "arco":
        e2["angulo_inicio_rad"], e2["angulo_fin_rad"] = e["angulo_fin_rad"], e["angulo_inicio_rad"]
    return e2


# ---------------------------------------------------------------------------------------------------
# 5) Entidad normalizada + orientada -> Tramo (con tangentes de entrada/salida)
# ---------------------------------------------------------------------------------------------------------------------

def _tangente_arco(centro: tuple, angulo_rad: float, sentido_ccw: bool) -> tuple:
    """Vector unitario tangente a un arco en el ángulo dado, en el sentido de recorrido."""
    tx, ty = -math.sin(angulo_rad), math.cos(angulo_rad)
    if not sentido_ccw:
        tx, ty = -tx, -ty
    return (tx, ty)


def entidad_a_tramo(e: dict) -> Tramo:
    if e["tipo"] == "linea":
        dx, dy = e["p_fin"][0] - e["p_inicio"][0], e["p_fin"][1] - e["p_inicio"][1]
        long = math.hypot(dx, dy)
        d = (dx / long, dy / long) if long > 0 else (0.0, 0.0)
        return Tramo("linea", long, e["p_inicio"], e["p_fin"], d, d)

    # arco
    a0, a1 = e["angulo_inicio_rad"], e["angulo_fin_rad"]
    ccw = a1 >= a0
    long = abs(a1 - a0) * e["radio_mm"]
    dir_entrada = _tangente_arco(e["centro"], a0, ccw)
    dir_salida = _tangente_arco(e["centro"], a1, ccw)
    return Tramo("arco", long, e["p_inicio"], e["p_fin"], dir_entrada, dir_salida,
                 radio_mm=e["radio_mm"], centro=e["centro"])


# ---------------------------------------------------------------------------------------------------------------------------------
# 6) Ángulo de giro entre dos tramos consecutivos (para Junction Deviation, Etapa 3)
# ---------------------------------------------------------------------------------------------------------------------

def angulo_de_giro_grados(tramo_a: Tramo, tramo_b: Tramo) -> float:
    """Ángulo entre la dirección de salida de A y la de entrada de B.
    0° = sigue derecho (mismo sentido); 180° = revierte 180°."""
    ax, ay = tramo_a.dir_salida
    bx, by = tramo_b.dir_entrada
    cos_ang = max(-1.0, min(1.0, ax * bx + ay * by))
    return math.degrees(math.acos(cos_ang))


# ---------------------------------------------------------------------------------------------------------------------------------
# 7) Orquestación de nivel superior
# ---------------------------------------------------------------------------------------------------------------------

def parsear_figuras(dxf_path, layer: str | None = None) -> list:
    """Parsea un DXF completo: agrupa en figuras, encadena cada una, la convierte
    a tramos, y calcula los ángulos de vértice DENTRO de cada figura (incluido el
    de cierre si la figura es cerrada).

    Devuelve: [{"tramos": [Tramo, ...], "angulos_vertice_grados": [float, ...],
                "cerrada": bool}, ...]
    """
    entidades = extraer_entidades(dxf_path, layer=layer)
    grupos_idx = agrupar_en_figuras(entidades)

    figuras = []
    for idxs in grupos_idx:
        grupo = [entidades[i] for i in idxs]
        cadena, cerrada = encadenar_figura(grupo)
        tramos = [entidad_a_tramo(e) for e in cadena]

        angulos = []
        for i in range(len(tramos) - 1):
            angulos.append(angulo_de_giro_grados(tramos[i], tramos[i + 1]))
        if cerrada and len(tramos) > 1:
            angulos.append(angulo_de_giro_grados(tramos[-1], tramos[0]))

        figuras.append({"tramos": tramos, "angulos_vertice_grados": angulos, "cerrada": cerrada})
    return figuras


def main() -> None:
    import sys
    if len(sys.argv) < 2:
        print("Uso: python simulador_toolpath.py <archivo.dxf> [capa]")
        return
    path = sys.argv[1]
    layer = sys.argv[2] if len(sys.argv) > 2 else None
    figuras = parsear_figuras(path, layer=layer)
    print(f"=== {path} ===")
    print(f"figuras encontradas: {len(figuras)}")
    for i, f in enumerate(figuras):
        tipos = [t.tipo for t in f["tramos"]]
        n_lineas = tipos.count("linea")
        n_arcos = tipos.count("arco")
        long_total = sum(t.longitud_mm for t in f["tramos"])
        ang = f["angulos_vertice_grados"]
        ang_str = f"min={min(ang):.1f}° max={max(ang):.1f}°" if ang else "(sin vértices)"
        print(f"  figura {i}: {len(f['tramos'])} tramos ({n_lineas} líneas, {n_arcos} arcos), "
              f"long={long_total:.1f}mm, cerrada={f['cerrada']}, ángulos {ang_str}")


if __name__ == "__main__":
    main()
