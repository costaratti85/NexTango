#!/usr/bin/env python3
"""ETAPA 3 — predicción del simulador calibrado contra las 3 siluetas
orgánicas reales (Corazón, Gotas, Cosmos) — la validación clave que pidió
Constantino: si el modelo (calibrado SOLO contra Batería 2, que es toda
cuadriculado de 90°) predice bien una geometría que NUNCA vio en la
calibración (ángulos variados, círculos completos), es una señal fuerte de
que el modelo capturó la física real y no solo el ruido de Batería 2.

Esto imprime la PREDICCIÓN. Comparar contra el tiempo real medido por CypCut
lo tiene que hacer Constantino (no lo tenemos todavía) — ver el reporte.

SUPUESTO marcado explícitamente: el orden de recorrido ENTRE figuras (viaje
de "rápido" de una al centroide de la siguiente) para Corazón/Gotas se
aproxima con el mismo criterio boustrophedon (fila por fila, alternando
sentido) que ya se usa para Batería 2 — no hay forma de confirmarlo sin
telemetría real de CypCut para ESTA geometría en particular (no son una
grilla regular como Batería 2). Cosmos también, aunque al ser un patrón muy
regular de círculos es más probable que boustrophedon aplique bien.
"""
import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from analisis_laser_fisico import ordenar_boustrophedon
from organicas_utils import convertir_splines_a_lineas
from simulador_toolpath import parsear_figuras
from simulador_cinematico import tiempo_corte_figura, tiempo_desplazamiento_saltos

# Parámetros calibrados en ETAPA 3 contra Batería 2 (ver MSG a Nova) — cada
# uno contra SU componente medido por separado.
V_TABLA, A_MAX_CUT, DELTA_CUT = 74.0, 625.0, 0.2
V_RAPIDO, A_MAX_TRAV, DELTA_TRAV = 129.5, 750.0, 0.005


def _centroide(tramos):
    xs = [p[0] for t in tramos for p in (t.p_inicio, t.p_fin)]
    ys = [p[1] for t in tramos for p in (t.p_inicio, t.p_fin)]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def _angulo_entre_vectores_grados(v1, v2) -> float:
    n1, n2 = math.hypot(*v1), math.hypot(*v2)
    if n1 == 0 or n2 == 0:
        return 0.0
    ux1, uy1 = v1[0] / n1, v1[1] / n1
    ux2, uy2 = v2[0] / n2, v2[1] / n2
    cos_ang = max(-1.0, min(1.0, ux1 * ux2 + uy1 * uy2))
    return math.degrees(math.acos(cos_ang))


def predecir(dxf_path, tiene_splines: bool):
    t0 = time.time()
    if tiene_splines:
        conv_path = Path(str(dxf_path) + ".conv.dxf")
        convertir_splines_a_lineas(dxf_path, conv_path)
        dxf_path = conv_path
    figuras = parsear_figuras(dxf_path)
    t_parseo = time.time() - t0

    t_corte = 0.0
    centroides = []
    todos_angulos = []
    for f in figuras:
        t_corte += tiempo_corte_figura(f["tramos"], f["angulos_vertice_grados"], f["cerrada"],
                                       V_TABLA, DELTA_CUT, A_MAX_CUT)
        centroides.append(_centroide(f["tramos"]))
        todos_angulos.extend(f["angulos_vertice_grados"])

    centros_orden = ordenar_boustrophedon(centroides)
    vectores = [(x1 - x0, y1 - y0) for (x0, y0), (x1, y1) in zip(centros_orden, centros_orden[1:])]
    saltos_abs = [(abs(dx), abs(dy)) for dx, dy in vectores]
    angulos_travel = [_angulo_entre_vectores_grados(vectores[i], vectores[i + 1])
                      for i in range(len(vectores) - 1)]
    t_travel = tiempo_desplazamiento_saltos(saltos_abs, angulos_travel, V_RAPIDO, DELTA_TRAV, A_MAX_TRAV)

    return {
        "n_figuras": len(figuras),
        "angulo_min": min(todos_angulos) if todos_angulos else None,
        "angulo_max": max(todos_angulos) if todos_angulos else None,
        "t_corte_pred_s": t_corte,
        "t_travel_pred_s": t_travel,
        "t_parseo_s": t_parseo,
    }


if __name__ == "__main__":
    base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    casos = [
        ("Corazon.dxf", True),
        ("Gotas.dxf", False),
        ("Cosmos_OffXY_500.dxf", False),
    ]
    for nombre, tiene_splines in casos:
        path = base / nombre
        if not path.exists():
            print(f"{nombre}: NO ENCONTRADO en {base}, salteado")
            continue
        r = predecir(path, tiene_splines)
        print(f"\n=== {nombre} ===")
        print(f"  figuras: {r['n_figuras']}  ángulos: {r['angulo_min']:.2f}°–{r['angulo_max']:.2f}°"
              if r['angulo_min'] is not None else f"  figuras: {r['n_figuras']} (sin vértices, ej. círculos)")
        print(f"  CORTE predicho:  {r['t_corte_pred_s']:.2f} s")
        print(f"  TRAVEL predicho: {r['t_travel_pred_s']:.2f} s  (orden boustrophedon, SUPUESTO no verificado)")
        print(f"  TOTAL predicho:  {r['t_corte_pred_s'] + r['t_travel_pred_s']:.2f} s")
        print(f"  (parseo: {r['t_parseo_s']:.1f}s)")
