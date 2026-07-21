#!/usr/bin/env python3
"""ETAPA 3 — genera los 15 DXF del experimento de validación v2 (MSG_167/168),
aprobado por Constantino: figuras abiertas con arcos/líneas NATIVOS (nada de
segmentos aproximados) + para Bloque 2/3, líneas de travel de REFERENCIA en
una capa aparte que muestran la secuencia + punto de entrada/salida exactos
que Constantino tiene que reproducir en CypCut.

Convención de capas:
  - "CORTE": la geometría real a cortar (lo único que CypCut debe procesar).
  - "REFERENCIA_NO_CORTAR": líneas de viaje + marcadores de entrada/salida +
    números de secuencia — SOLO para que Constantino vea el recorrido. Se
    deja apagada (off) y congelada (frozen) en el DXF, con un nombre y color
    (magenta) inequívocos. No hay garantía de que CypCut respete el estado
    off/frozen de una capa DXF (no lo pudimos confirmar) — por eso el LEEME
    instruye explícitamente a BORRAR esa capa antes de mandar a cortar, no
    solo confiar en que quede oculta.

No incluye las predicciones del simulador en ningún archivo entregado a
Constantino (mismo criterio que la vez pasada: medición a ciegas).
"""
import math
import sys
from pathlib import Path

import ezdxf

OUT_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
OUT_DIR.mkdir(parents=True, exist_ok=True)

LAYER_CORTE = "CORTE"
LAYER_REF = "REFERENCIA_NO_CORTAR"


def _doc_base():
    doc = ezdxf.new()
    doc.layers.add(LAYER_CORTE, color=7)
    ref = doc.layers.add(LAYER_REF, color=6)  # magenta
    ref.off()
    ref.freeze()
    ref.lock()
    return doc


# ---------------------------------------------------------------------------
# Bloque 1a — radios (arco abierto, barrido 90 grados)
# ---------------------------------------------------------------------------

def _hoja_bloque1(nombre_dxf: str, descripcion: str) -> str:
    return f"""INSTRUCCIONES — {nombre_dxf}
Bloque 1: CORTE puro (figura abierta y aislada)

Qué es: {descripcion}

Cómo cortarla: no importa por qué punta empieza ni en qué sentido la recorrés — el tiempo de
corte de esta figura no depende de eso (es una figura abierta y sola en la chapa, sin
ninguna otra al lado). Cortala como te resulte más cómodo.

Capas: toda la geometría está en la capa "CORTE". Este archivo NO tiene capa de referencia
(no hace falta — es una sola figura, no hay secuencia que mostrar).

Qué anotar de CypCut: el "Processing time" (no hace falta el total ni el Move — esta figura
sola no tiene desplazamiento que medir).
"""


def gen_radio(radio_mm: float) -> str:
    doc = _doc_base()
    msp = doc.modelspace()
    msp.add_arc(center=(0, 0), radius=radio_mm, start_angle=0, end_angle=90,
               dxfattribs={"layer": LAYER_CORTE})
    nombre = f"radio_{int(round(radio_mm)):02d}mm.dxf" if radio_mm < 100 else f"radio_{int(round(radio_mm))}mm.dxf"
    doc.saveas(str(OUT_DIR / nombre))
    arco_mm = radio_mm * math.pi / 2
    desc = (f"Arco abierto de radio {radio_mm:.0f}mm, barrido de 90° (longitud de arco "
           f"{arco_mm:.1f}mm). Centro en (0,0), de (radio,0) a (0,radio).")
    (OUT_DIR / f"INSTRUCCIONES_{nombre.replace('.dxf', '.txt')}").write_text(
        _hoja_bloque1(nombre, desc), encoding="utf-8")
    return nombre


# ---------------------------------------------------------------------------
# Bloque 1b — ángulos (polilínea abierta en V, 2 tramos rectos de 50mm)
# ---------------------------------------------------------------------------

def gen_angulo(turn_deg: float) -> str:
    doc = _doc_base()
    msp = doc.modelspace()
    L = 50.0
    p_start = (-L, 0.0)
    vertice = (0.0, 0.0)
    rad = math.radians(turn_deg)
    p_end = (L * math.cos(rad), L * math.sin(rad))
    msp.add_line(p_start, vertice, dxfattribs={"layer": LAYER_CORTE})
    msp.add_line(vertice, p_end, dxfattribs={"layer": LAYER_CORTE})
    nombre = f"angulo_{int(round(turn_deg)):03d}deg.dxf"
    doc.saveas(str(OUT_DIR / nombre))
    desc = (f"Polilínea abierta en 'V': 2 tramos rectos de {L:.0f}mm cada uno, con un "
           f"ángulo de giro de {turn_deg:.0f}° en el vértice central (0°=recto sin doblar, "
           f"180°=se pliega sobre sí misma).")
    (OUT_DIR / f"INSTRUCCIONES_{nombre.replace('.dxf', '.txt')}").write_text(
        _hoja_bloque1(nombre, desc), encoding="utf-8")
    return nombre


# ---------------------------------------------------------------------------
# Bloque 1c — rectas de control
# ---------------------------------------------------------------------------

def gen_recta(largo_mm: float) -> str:
    doc = _doc_base()
    msp = doc.modelspace()
    msp.add_line((0, 0), (largo_mm, 0), dxfattribs={"layer": LAYER_CORTE})
    nombre = f"recta_{int(round(largo_mm)):03d}mm.dxf"
    doc.saveas(str(OUT_DIR / nombre))
    desc = f"Línea recta simple de {largo_mm:.0f}mm, sin vértices ni curvas (control)."
    (OUT_DIR / f"INSTRUCCIONES_{nombre.replace('.dxf', '.txt')}").write_text(
        _hoja_bloque1(nombre, desc), encoding="utf-8")
    return nombre


# ---------------------------------------------------------------------------
# Bloque 2/3 — segmentos verticales + capa de referencia con la secuencia
# ---------------------------------------------------------------------------

def gen_travel(nombre: str, xs: list, alto_mm: float) -> dict:
    """xs: posiciones X de las figuras (2 o 4, según el archivo). Cada figura
    es un segmento vertical centrado en y=0, de `alto_mm` de alto. Entrada =
    punto de ABAJO, salida = punto de ARRIBA (convención fija, igual en
    todas). Devuelve los puntos de entrada/salida reales para la hoja de
    instrucciones."""
    doc = _doc_base()
    msp = doc.modelspace()
    h = alto_mm / 2.0
    puntos = []
    for x in xs:
        entrada = (x, -h)
        salida = (x, h)
        msp.add_line(entrada, salida, dxfattribs={"layer": LAYER_CORTE})
        puntos.append({"entrada": entrada, "salida": salida})

    # capa de referencia: líneas de viaje (salida de i -> entrada de i+1),
    # marcador de entrada (círculo chico) y de salida (X chica), número de
    # secuencia como texto
    for i, p in enumerate(puntos):
        ex, ey = p["entrada"]
        sx, sy = p["salida"]
        msp.add_circle((ex, ey), radius=1.5, dxfattribs={"layer": LAYER_REF})
        msp.add_line((sx - 1.5, sy - 1.5), (sx + 1.5, sy + 1.5), dxfattribs={"layer": LAYER_REF})
        msp.add_line((sx - 1.5, sy + 1.5), (sx + 1.5, sy - 1.5), dxfattribs={"layer": LAYER_REF})
        msp.add_text(str(i + 1), height=3.0, dxfattribs={"layer": LAYER_REF}).set_placement(
            (ex - 1.5, ey - 6.0))
        if i > 0:
            prev_salida = puntos[i - 1]["salida"]
            msp.add_line(prev_salida, p["entrada"], dxfattribs={"layer": LAYER_REF})

    doc.saveas(str(OUT_DIR / nombre))

    pasos = "\n".join(
        f"  {i + 1}. Figura {i + 1} (x={x:g}) — entrar por ABAJO {p['entrada']}, "
        f"salir por ARRIBA {p['salida']}"
        for i, (x, p) in enumerate(zip(xs, puntos))
    )
    ancho_total = xs[-1] - xs[0]
    nota_chapa = (
        f"\nOJO CON EL TAMAÑO DE CHAPA: este archivo necesita ~{ancho_total:.0f}mm de ancho "
        f"libre para el salto — confirmá que la chapa/mesa de corte disponible alcanza antes "
        f"de mandarlo. Si no alcanza, avisá en vez de recortar la distancia (necesitamos esta "
        f"distancia específica para el experimento).\n"
        if ancho_total >= 900 else ""
    )
    hoja = f"""INSTRUCCIONES — {nombre}
Bloque 2/3: DESPLAZAMIENTO y TAMAÑO (acá la entrada/salida SÍ importa)

Qué es: {len(xs)} segmentos verticales de {alto_mm:.0f}mm de alto, en fila horizontal,
separados {xs[1]-xs[0]:g}mm entre sí (mismo alto Y en los {len(xs)}).
{nota_chapa}
CAPAS — MUY IMPORTANTE:
  - "CORTE": los {len(xs)} segmentos verticales — esto es lo único que hay que cortar.
  - "REFERENCIA_NO_CORTAR": las líneas finas + círculos + X + números que muestran el
    recorrido (para que veas el orden y los puntos de entrada/salida). Esta capa está
    apagada y congelada en el archivo, PERO no tenemos forma de garantizar que CypCut
    respete ese estado — antes de mandar a cortar, BORRÁ esta capa a mano (o confirmá
    visualmente que quedó oculta y no se procesa). Es solo una guía visual, no se corta.

SECUENCIA A REPRODUCIR EN CypCut (mirá la capa de referencia para verlo dibujado):
{pasos}

  El recorrido entre figuras (línea fina en la capa de referencia) va de la SALIDA de una
  figura a la ENTRADA de la siguiente, en ese orden.

Qué anotar de CypCut: el desglose completo — "Processing time", "Move time" y "Delay time"
por separado (no solo el total).
"""
    (OUT_DIR / f"INSTRUCCIONES_{nombre.replace('.dxf', '.txt')}").write_text(hoja, encoding="utf-8")
    return {"nombre": nombre, "puntos": puntos}


if __name__ == "__main__":
    generados = []
    for r in [5, 15, 40, 100]:
        generados.append(gen_radio(r))
    for a in [15, 45, 90, 135, 165]:
        generados.append(gen_angulo(a))
    for l in [20, 80, 250]:
        generados.append(gen_recta(l))

    info_travel = []
    info_travel.append(gen_travel("travel_cerca.dxf", [0, 20, 40, 60], 10.0))
    info_travel.append(gen_travel("travel_lejos.dxf", [0, 200, 400, 600], 10.0))
    info_travel.append(gen_travel("tamano_grande.dxf", [0, 20, 40, 60], 40.0))

    # Ronda 2 (MSG_171): 1 solo salto largo por archivo, para caracterizar si
    # hay meseta de velocidad de crucero o si la máquina sigue acelerando
    # mucho más allá de los 600mm de travel_lejos. Nominal de fábrica:
    # 1650mm/s -- con a_max_travel~385mm/s² (ya bien determinado por
    # travel_cerca/tamano_grande, INSENSIBLE a este debate) necesitaría
    # ~3535mm para llegar a esa velocidad -- estas 2 distancias alcanzan para
    # distinguir con claridad "meseta cerca de ~199mm/s" de "sigue subiendo
    # hacia el nominal" (ver el cálculo en MSG_171).
    info_travel.append(gen_travel("travel_muylejos_1.dxf", [0, 1000], 10.0))
    info_travel.append(gen_travel("travel_muylejos_2.dxf", [0, 3000], 10.0))

    print("Generados en", OUT_DIR)
    for g in generados:
        print(" ", g)
    for it in info_travel:
        print(" ", it["nombre"], "->", it["puntos"])
