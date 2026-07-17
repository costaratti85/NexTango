#!/usr/bin/env python3
"""Rediseño de la fórmula de tiempo de láser — ajuste por COMPONENTE, no por total.

Principio rector (consejo + Constantino, 2026-07-16): cada término se ajusta contra
SU PROPIO componente medido de CypCut (Processing/Move/Delay), nunca contra el total.
Un parámetro físico por componente. Modelo falsable.

MÓDULOS:
  - Reconstrucción de geometría real (saltos + segmentos de corte) desde los DXF
    reales de la Batería 2 — no depende de datos externos, ya está implementado
    y verificado abajo.
  - Modelo de DESPLAZAMIENTO: jerk-limitado por eje, t = (32·d/j)^(1/3) por debajo
    de la distancia crítica; tiempo total del salto = max(t_x, t_y) (ejes
    independientes, se mueven simultáneos). Linealizable: t = k·max(dx,dy)^(1/3)
    con k=(32/j)^(1/3) — permite ajuste lineal auditable de k (y j = 32/k³).
  - Modelo de CORTE: pendiente de datos reales de Processing time — NO se asume
    que es el mismo problema físico que los saltos (ver docstring de
    ajustar_modelo_corte más abajo).
  - Perforado: constante prescripta (no se recalibra acá).

BLOQUEO ACTUAL: el ajuste de k/j y la validación de TODO este módulo necesitan el
desglose Processing/Move/Delay por panel de los 12 paneles de la Batería 2 (CypCut
lo reporta, no lo tengo cargado — solo tengo el Total agregado en
calibracion_bateria2_REAL.json). Sin eso, `ajustar_modelo_desplazamiento` y
`ajustar_modelo_corte` no tienen contra qué ajustar. Ver DESGLOSE_BATERIA2 abajo
(placeholder vacío, completar cuando llegue el dato).
"""
from __future__ import annotations

import math
from pathlib import Path

try:
    import ezdxf
    import numpy as np
except ImportError as e:
    raise SystemExit(f"Falta dependencia ({e}). Activá el venv: source .venv/bin/activate")


# ---------------------------------------------------------------------------
# 1) Reconstrucción de geometría real desde los DXF de la Batería 2
# ---------------------------------------------------------------------------

def extraer_centros_agujeros(dxf_path) -> list:
    """Lee un DXF de cuadriculado (los de Batería 2) y devuelve los centros
    (cx, cy) de cada agujero, en el orden en que aparecen en el archivo."""
    doc = ezdxf.readfile(str(dxf_path))
    centros = []
    for e in doc.modelspace():
        if e.dxf.layer == "CONTORNO" or e.dxftype() != "LWPOLYLINE":
            continue
        pts = list(e.get_points())
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        centros.append((cx, cy))
    return centros


def ordenar_boustrophedon(centros: list, tol: float = 1e-3) -> list:
    """Ordena los centros en recorrido serpenteante (boustrophedon): agrupa por
    fila (Y), dentro de cada fila ordena por X, alternando la dirección fila a
    fila (izq→der, der→izq, ...) — minimiza el desplazamiento total, es la
    estrategia estándar de nesting/corte. Filas ordenadas de menor a mayor Y.

    SUPUESTO NO VERIFICADO: no tenemos telemetría del recorrido real de CypCut;
    esto es la hipótesis más físicamente razonable (y la que ya asume
    implícitamente compute_travel_length_mm en producción, aunque con una
    secuencia distinta — ver nota en el módulo). Si CypCut usa otro orden, el
    análisis por-salto de este módulo no aplica tal cual.
    """
    filas: dict = {}
    for cx, cy in centros:
        y_key = round(cy / tol) * tol
        filas.setdefault(y_key, []).append((cx, cy))
    ordenado = []
    for i, y_key in enumerate(sorted(filas.keys())):
        fila = sorted(filas[y_key], key=lambda p: p[0])
        if i % 2 == 1:
            fila = fila[::-1]
        ordenado.extend(fila)
    return ordenado


def saltos_del_panel(dxf_path) -> list:
    """Devuelve la lista de saltos (dx, dy) — valor absoluto — entre agujeros
    consecutivos del recorrido boustrophedon reconstruido."""
    centros = ordenar_boustrophedon(extraer_centros_agujeros(dxf_path))
    saltos = []
    for (x0, y0), (x1, y1) in zip(centros, centros[1:]):
        saltos.append((abs(x1 - x0), abs(y1 - y0)))
    return saltos


def segmentos_de_corte(dxf_path) -> list:
    """Devuelve, por cada agujero (cuadrado), la lista de 4 longitudes de lado
    (todas = hole_size, con las 4 esquinas a 90°). Para hexágonos habría 6 lados
    con esquinas a 120° — no implementado (Batería 2 es toda cuadriculado square)."""
    doc = ezdxf.readfile(str(dxf_path))
    segmentos = []
    for e in doc.modelspace():
        if e.dxf.layer == "CONTORNO" or e.dxftype() != "LWPOLYLINE":
            continue
        pts = list(e.get_points())
        lados = []
        n = len(pts)
        for i in range(n):
            x0, y0 = pts[i][0], pts[i][1]
            x1, y1 = pts[(i + 1) % n][0], pts[(i + 1) % n][1]
            lados.append(math.hypot(x1 - x0, y1 - y0))
        segmentos.append(lados)
    return segmentos


# ---------------------------------------------------------------------------
# 2) Modelo de DESPLAZAMIENTO — jerk-limitado por eje
# ---------------------------------------------------------------------------

def tiempo_salto_jerk(dx: float, dy: float, j: float) -> float:
    """Tiempo de un salto (dx, dy) con jerk-limitado POR EJE, régimen puro-jerk
    (sin tope de velocidad/aceleración — válido solo por debajo de la distancia
    crítica, ver distancia_critica_jerk). t_eje = (32·d/j)^(1/3); el salto 2D
    tarda lo que tarda el eje más lento: max(t_x, t_y) — NO la hipotenusa,
    porque cada eje es un motor independiente moviéndose en simultáneo.
    """
    tx = (32.0 * dx / j) ** (1.0 / 3.0) if dx > 0 else 0.0
    ty = (32.0 * dy / j) ** (1.0 / 3.0) if dy > 0 else 0.0
    return max(tx, ty)


def distancia_critica_jerk(v_max: float, j: float) -> float:
    """Distancia hasta la que el perfil puro-jerk (sin tope de velocidad) es
    válido: la velocidad pico de ese perfil (v_peak = j·(T/4)² con T=(32d/j)^(1/3))
    alcanza v_max. Por encima de esta distancia, el salto entra en régimen
    jerk→aceleración constante→crucero (no implementado — ver bloqueo del módulo:
    hace falta v_max, que no tenemos, más que el mal etiquetado "40000" que
    Constantino identificó como jerk, no aceleración)."""
    return v_max ** 3 / (2.0 * j)


def k_desde_j(j: float) -> float:
    """t = (32d/j)^(1/3) = k·d^(1/3) con k=(32/j)^(1/3). Linealiza el ajuste."""
    return (32.0 / j) ** (1.0 / 3.0)


def j_desde_k(k: float) -> float:
    return 32.0 / (k ** 3)


def ajustar_modelo_desplazamiento(saltos_por_panel: dict, move_time_real: dict) -> dict:
    """Ajusta k (y t_torcha) por mínimos cuadrados LINEAL contra el Move time
    real de CypCut por panel.

    Como t_jerk(d,j) = k·d^(1/3) (k constante), el tiempo total de un panel es:
        Move_pred(panel) = k · Σ_saltos max(dx,dy)^(1/3)  [+ t_torcha · N_saltos]
    — lineal en (k, t_torcha): 2 incógnitas, un dato por panel. Mínimos cuadrados
    con 2 columnas (S_panel = Σ max(dx,dy)^(1/3), N_saltos) — auditable igual que
    la calibración de α/β/δ anterior (sistema de ecuaciones explícito).

    saltos_por_panel: {nombre: [(dx,dy), ...]}
    move_time_real:   {nombre: segundos}  ← FALTA (bloqueo del módulo)

    Retorna: {"k":.., "j":.., "t_torcha":.., "r2":.., "pred_vs_real": {...}}
    o {"error": "..."} si move_time_real está vacío.
    """
    if not move_time_real:
        return {"error": (
            "Falta el Move time real por panel (CypCut lo reporta desglosado; "
            "solo tengo el Total agregado). No se puede ajustar ni validar sin esto."
        )}

    nombres = [n for n in saltos_por_panel if n in move_time_real]
    S = np.array([
        sum(max(dx, dy) ** (1.0 / 3.0) for dx, dy in saltos_por_panel[n])
        for n in nombres
    ])
    N = np.array([len(saltos_por_panel[n]) for n in nombres])
    y = np.array([move_time_real[n] for n in nombres])

    X = np.column_stack([S, N])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    k, t_torcha = coef
    pred = X @ coef
    ss_res = float(np.sum((pred - y) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")

    return {
        "k": float(k),
        "j": j_desde_k(k) if k > 0 else None,
        "t_torcha_s": float(t_torcha),
        "r2": r2,
        "pred_vs_real": {n: (float(p), float(r)) for n, p, r in zip(nombres, pred, y)},
    }


# ---------------------------------------------------------------------------
# 3) Modelo de CORTE — pendiente de validación empírica
# ---------------------------------------------------------------------------

def ajustar_modelo_corte(segmentos_por_panel: dict, processing_time_real: dict) -> dict:
    """PENDIENTE — bloqueado por falta de Processing time real por panel.

    NO asumir que el corte usa la misma física que los saltos (reposo→reposo)
    sin validarlo: el corte es movimiento CONTINUO con desaceleración en cada
    esquina (90° en cuadrados, 120° en hexágonos), no necesariamente frenando a
    velocidad cero — depende del look-ahead del controlador. La hipótesis más
    simple (reusar el mismo j de los saltos, tratando cada lado del cuadrado
    como un salto reposo→reposo) es un punto de partida, NO un hecho — hay que
    validarla panel por panel contra el Processing time real antes de confiar
    en ella. Sin ese dato, esta función no puede ejecutar ningún ajuste.
    """
    if not processing_time_real:
        return {"error": (
            "Falta el Processing time real por panel. No se puede ajustar ni "
            "validar el modelo de corte sin esto — y NO se debe asumir que es "
            "la misma física que los saltos sin verificarlo."
        )}
    raise NotImplementedError("Implementar cuando llegue processing_time_real.")


# ---------------------------------------------------------------------------
# 4) Datos — geometría reconstruida (listo) + desglose CypCut (FALTA)
# ---------------------------------------------------------------------------

_BATERIA2_DIR = Path(__file__).resolve().parent / "calibracion_bateria2"
_PANELES_B2 = [
    "B2_01_L60_p70_500x500", "B2_02_L30_p70_500x500", "B2_03_L20_p40_1000x1000",
    "B2_04_L30_p140_1000x1000", "B2_05_L12_p70_1000x500", "B2_06_L8_p70_1000x500",
    "B2_07_L12_p70_1000x1000", "B2_08_L5_p25_1000x1000", "B2_09_L8_p70_1000x1000",
    "B2_10_L5_p100_1000x1000", "B2_11_L5_p45_1000x1000", "B2_12_L5_p70_1000x1000",
]

# Desglose CypCut Processing/Move/Delay por panel de la Batería 2 — FALTA.
# Solo tenemos el Total agregado (calibracion_bateria2_REAL.json). Completar
# {"B2_01": {"processing_s": .., "move_s": .., "delay_s": ..}, ...} cuando
# Constantino/Dispatch lo pasen, y correr ajustar_modelo_desplazamiento /
# ajustar_modelo_corte con esos valores.
DESGLOSE_BATERIA2: dict = {}


def cargar_geometria_bateria2() -> tuple:
    """Reconstruye saltos y segmentos de corte de los 12 paneles reales."""
    saltos, segmentos = {}, {}
    for nombre in _PANELES_B2:
        key = nombre.split("_L")[0]  # "B2_01"
        path = _BATERIA2_DIR / f"{nombre}.dxf"
        saltos[key] = saltos_del_panel(path)
        segmentos[key] = segmentos_de_corte(path)
    return saltos, segmentos


def main() -> None:
    saltos, segmentos = cargar_geometria_bateria2()
    print("=== Geometría reconstruida (saltos + segmentos de corte) ===")
    for k in saltos:
        n_saltos = len(saltos[k])
        n_pierce = len(segmentos[k])
        print(f"  {k}: {n_pierce} agujeros, {n_saltos} saltos reconstruidos")

    print("\n=== Ajuste de desplazamiento (jerk) ===")
    r = ajustar_modelo_desplazamiento(saltos, DESGLOSE_BATERIA2)
    if "error" in r:
        print(f"  BLOQUEADO: {r['error']}")
    else:
        print(f"  k={r['k']:.6f}  j={r['j']:.1f} mm/s^3  t_torcha={r['t_torcha_s']:.3f}s  R2={r['r2']:.4f}")


if __name__ == "__main__":
    main()
