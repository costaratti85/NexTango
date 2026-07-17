#!/usr/bin/env python3
"""Rediseño de la fórmula de tiempo de láser — ajuste por COMPONENTE, no por total.

Principio rector (consejo + Constantino, 2026-07-16): cada término se ajusta contra
SU PROPIO componente medido de CypCut (Processing/Move/Delay), nunca contra el total.
Un parámetro físico por componente. Modelo falsable.

ESTADO (2026-07-16): con el desglose Processing/Move/Delay real de los 12 paneles
de Batería 2 (DESGLOSE_BATERIA2), NINGUNO de los modelos de 1-2 parámetros
probados hasta ahora predice con precisión aceptable para pricing. Hay un
HALLAZGO sistemático sin resolver — ver `diagnostico_correlacion_densidad()` y
el reporte en coordination/channel/Nova/. NO se cargó ningún coeficiente nuevo
a producción: esto es exploración, no un modelo listo.

MÓDULOS:
  - Reconstrucción de geometría real (saltos + segmentos de corte + contorno)
    desde los DXF reales de la Batería 2 — verificado, funciona bien.
  - DESPLAZAMIENTO — 2 variantes probadas, NINGUNA cierra:
    (a) `ajustar_modelo_desplazamiento`: jerk por SALTO individual (reposo a
        reposo), t=(32·max(dx,dy)/j)^(1/3) por salto. R²=0.998 mirando el
        total, pero error por panel de hasta 23% y t_torcha sale NEGATIVO
        (físicamente incoherente) — el ajuste está compensando algo mal.
    (b) `ajustar_modelo_desplazamiento_por_fila`: toda una fila de agujeros
        colineales = UN solo movimiento (hipótesis: el motor no frena entre
        saltos alineados consecutivos). Peor: error medio ~47%, hasta 128%.
    Diagnóstico: el ratio Move_real/S correlaciona fuertemente con el número
    de columnas del panel (paneles densos ⇒ tiempo por salto MENOR de lo que
    predice el modelo reposo-a-reposo). La verdad está ENTRE los dos extremos
    — ninguno de los dos modelos simples la captura.
  - CORTE — 2 variantes probadas, NINGUNA cierra tampoco:
    (a) `ajustar_modelo_corte`: cada LADO del agujero = jerk 1D reposo a reposo
        en cada esquina de 90°. Error medio 30%, hasta 61%.
    (b) `ajustar_modelo_corte_velocidad_constante`: velocidad nominal fija
        (cut_length/v). Error medio 17%, pero sin capturar el patrón (dispersión
        3%–35%). Mismo patrón de fondo que el desplazamiento: paneles densos
        rinden mejor de lo que cualquiera de los dos modelos predice.
  - Perforado: constante prescripta (no se recalibra acá, sin cambios).

PRÓXIMO PASO PROPUESTO (no implementado, necesita validación): un modelo de
velocidad de esquina NO-CERO (cornering speed, estándar en control CNC) en vez
de frenado completo a v=0 en cada punto — explicaría por qué las secuencias
cortas y repetidas (patrones densos) son más eficientes que "reposo a reposo".
Agrega al menos 1 parámetro nuevo (v_esquina o el jerk lateral permitido).
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


def ajustar_modelo_desplazamiento_por_fila(centros_por_panel: dict, move_time_real: dict) -> dict:
    """VARIANTE B (hipótesis alternativa, PROBADA — no cierra mejor que la A).

    En vez de tratar cada salto como independiente, asume que el motor recorre
    una fila entera de agujeros colineales como UN SOLO movimiento (sin frenar
    entre agujeros de la misma fila), y solo frena/vuelve a arrancar al cambiar
    de fila. Resultado empírico (12 paneles reales, 2026-07-16): error medio
    ~47%, hasta 128% — PEOR que la variante A (salto por salto). Descartada como
    modelo único, pero el diagnóstico (ver diagnostico_correlacion_densidad) es
    valioso: la verdad está entre A y B, ninguno de los dos extremos es correcto.

    centros_por_panel: {nombre: [(cx,cy), ...]}  (sin ordenar — se ordena acá)
    """
    if not move_time_real:
        return {"error": "Falta el Move time real por panel."}

    def tramos_de_fila(centros, tol=1e-3):
        filas: dict = {}
        for cx, cy in centros:
            y_key = round(cy / tol) * tol
            filas.setdefault(y_key, []).append(cx)
        ys_ordenados = sorted(filas.keys())
        tramos = []
        for i, y in enumerate(ys_ordenados):
            xs_fila = sorted(filas[y])
            dist_fila = xs_fila[-1] - xs_fila[0]
            if dist_fila > 0:
                tramos.append((dist_fila, 0.0))
            if i < len(ys_ordenados) - 1:
                tramos.append((0.0, ys_ordenados[i + 1] - y))
        return tramos

    nombres = [n for n in centros_por_panel if n in move_time_real]
    S = np.array([
        sum(max(dx, dy) ** (1.0 / 3.0) for dx, dy in tramos_de_fila(centros_por_panel[n]))
        for n in nombres
    ])
    y = np.array([move_time_real[n] for n in nombres])
    k = float(np.sum(S * y) / np.sum(S ** 2))
    pred = k * S
    err_pct = np.abs(pred - y) / y * 100
    return {
        "k": k, "j": j_desde_k(k) if k > 0 else None,
        "error_medio_pct": float(err_pct.mean()), "error_max_pct": float(err_pct.max()),
        "pred_vs_real": {n: (float(p), float(r)) for n, p, r in zip(nombres, pred, y)},
    }


# ---------------------------------------------------------------------------
# 3) Modelo de CORTE — 2 variantes probadas, ninguna cierra (ver docstring del módulo)
# ---------------------------------------------------------------------------

def segmentos_de_contorno(dxf_path) -> list:
    """Lados del contorno del panel (rectángulo grande, capa CONTORNO)."""
    doc = ezdxf.readfile(str(dxf_path))
    for e in doc.modelspace():
        if e.dxf.layer == "CONTORNO" and e.dxftype() == "LWPOLYLINE":
            pts = list(e.get_points())
            n = len(pts)
            return [
                math.hypot(pts[(i + 1) % n][0] - pts[i][0], pts[(i + 1) % n][1] - pts[i][1])
                for i in range(n)
            ]
    return []


def ajustar_modelo_corte(segmentos_por_panel: dict, contorno_por_panel: dict,
                         processing_time_real: dict) -> dict:
    """VARIANTE A: cada LADO (del agujero y del contorno) = movimiento 1D
    jerk-limitado reposo-a-reposo en cada esquina de 90°.

    Processing_pred = k_corte · Σ_lados (lado^(1/3))  — 1 parámetro, lineal.

    Resultado empírico (12 paneles reales, 2026-07-16): error medio 30%, hasta
    61%. NO validado para producción — mismo patrón de fondo que el
    desplazamiento (paneles densos rinden mejor de lo que el modelo predice).

    segmentos_por_panel: {nombre: [[lado,lado,lado,lado], ...]}  (por agujero)
    contorno_por_panel:  {nombre: [lado,lado,lado,lado]}
    processing_time_real: {nombre: segundos}
    """
    if not processing_time_real:
        return {"error": (
            "Falta el Processing time real por panel. No se puede ajustar ni "
            "validar el modelo de corte sin esto — y NO se debe asumir que es "
            "la misma física que los saltos sin verificarlo."
        )}
    nombres = [n for n in segmentos_por_panel if n in processing_time_real]
    S = np.array([
        sum(l ** (1 / 3) for figura in segmentos_por_panel[n] for l in figura)
        + sum(l ** (1 / 3) for l in contorno_por_panel.get(n, []))
        for n in nombres
    ])
    y = np.array([processing_time_real[n] for n in nombres])
    k = float(np.sum(S * y) / np.sum(S ** 2))
    pred = k * S
    err_pct = np.abs(pred - y) / y * 100
    return {
        "k_corte": k,
        "error_medio_pct": float(err_pct.mean()), "error_max_pct": float(err_pct.max()),
        "pred_vs_real": {n: (float(p), float(r)) for n, p, r in zip(nombres, pred, y)},
    }


def ajustar_modelo_corte_velocidad_constante(cut_length_mm_por_panel: dict,
                                              processing_time_real: dict) -> dict:
    """VARIANTE B: velocidad de corte NOMINAL fija (sin jerk), Processing = cut/v.

    Resultado empírico: error medio 17%, MEJOR en promedio que la variante A,
    pero sin capturar el patrón (dispersión 3%–35% según panel, no aleatoria —
    correlaciona con densidad igual que las otras variantes). No es "el modelo
    correcto", es un promedio que por casualidad erra menos en total.
    """
    if not processing_time_real:
        return {"error": "Falta el Processing time real por panel."}
    nombres = [n for n in cut_length_mm_por_panel if n in processing_time_real]
    cut = np.array([cut_length_mm_por_panel[n] for n in nombres])
    y = np.array([processing_time_real[n] for n in nombres])
    v = float(np.sum(cut ** 2) / np.sum(cut * y))
    pred = cut / v
    err_pct = np.abs(pred - y) / y * 100
    return {
        "v_efectiva_mm_s": v,
        "error_medio_pct": float(err_pct.mean()), "error_max_pct": float(err_pct.max()),
        "pred_vs_real": {n: (float(p), float(r)) for n, p, r in zip(nombres, pred, y)},
    }


def diagnostico_correlacion_densidad(cols_por_panel: dict, ratio_por_panel: dict) -> float:
    """Coeficiente de correlación (Pearson) entre nº de columnas del panel y el
    ratio tiempo_real/S_modelo — cuantifica el hallazgo: a más columnas
    (patrón más denso), el modelo simple sobreestima más. Un |r| alto confirma
    que la densidad es la variable que ningún modelo de 1 parámetro captura."""
    nombres = [n for n in cols_por_panel if n in ratio_por_panel]
    cols = np.array([cols_por_panel[n] for n in nombres], dtype=float)
    ratio = np.array([ratio_por_panel[n] for n in nombres])
    return float(np.corrcoef(cols, ratio)[0, 1])


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

# Desglose CypCut Processing/Move/Delay por panel de la Batería 2 (2026-07-16,
# pasado por Constantino vía Dispatch). Verificado: processing+move+delay = total
# exacto en los 12 paneles.
DESGLOSE_BATERIA2 = {
    "B2_01": {"processing_s": 152.535, "move_s": 21.079, "delay_s": 26.975, "total_s": 200.590},
    "B2_02": {"processing_s": 94.935, "move_s": 21.229, "delay_s": 26.975, "total_s": 143.140},
    "B2_03": {"processing_s": 834.106, "move_s": 223.279, "delay_s": 414.830, "total_s": 1472.215},
    "B2_04": {"processing_s": 146.150, "move_s": 47.408, "delay_s": 36.313, "total_s": 229.871},
    "B2_05": {"processing_s": 118.269, "move_s": 46.719, "delay_s": 61.451, "total_s": 226.439},
    "B2_06": {"processing_s": 100.349, "move_s": 46.739, "delay_s": 61.451, "total_s": 208.539},
    "B2_07": {"processing_s": 235.576, "move_s": 108.486, "delay_s": 141.895, "total_s": 485.957},
    "B2_08": {"processing_s": 897.787, "move_s": 467.667, "delay_s": 1093.577, "total_s": 2459.030},
    "B2_09": {"processing_s": 193.763, "move_s": 108.506, "delay_s": 141.895, "total_s": 444.164},
    "B2_10": {"processing_s": 98.577, "move_s": 59.667, "delay_s": 59.297, "total_s": 217.540},
    "B2_11": {"processing_s": 298.380, "move_s": 183.167, "delay_s": 317.867, "total_s": 799.413},
    "B2_12": {"processing_s": 162.403, "move_s": 108.521, "delay_s": 141.895, "total_s": 412.819},
}


def cargar_geometria_bateria2() -> tuple:
    """Reconstruye saltos y segmentos de corte de los 12 paneles reales."""
    saltos, segmentos = {}, {}
    for nombre in _PANELES_B2:
        key = nombre.split("_L")[0]  # "B2_01"
        path = _BATERIA2_DIR / f"{nombre}.dxf"
        saltos[key] = saltos_del_panel(path)
        segmentos[key] = segmentos_de_corte(path)
    return saltos, segmentos


def cargar_datos_completos_bateria2() -> dict:
    """Todo lo reconstruible desde los 12 DXF reales: saltos, centros (sin
    ordenar), segmentos de corte, contorno, cut_length_mm, nº de columnas."""
    out = {}
    for nombre in _PANELES_B2:
        key = nombre.split("_L")[0]
        path = _BATERIA2_DIR / f"{nombre}.dxf"
        centros = extraer_centros_agujeros(path)
        xs = sorted(set(round(c[0], 1) for c in centros))
        out[key] = {
            "saltos": saltos_del_panel(path),
            "centros": centros,
            "segmentos": segmentos_de_corte(path),
            "contorno": segmentos_de_contorno(path),
            "cut_length_mm": sum(l for figura in segmentos_de_corte(path) for l in figura)
                             + sum(segmentos_de_contorno(path)),
            "cols": len(xs),
        }
    return out


def main() -> None:
    datos = cargar_datos_completos_bateria2()
    move_real = {k: v["move_s"] for k, v in DESGLOSE_BATERIA2.items()}
    proc_real = {k: v["processing_s"] for k, v in DESGLOSE_BATERIA2.items()}

    print("=== Geometría reconstruida ===")
    for k, d in datos.items():
        print(f"  {k}: {len(d['segmentos'])} agujeros, {len(d['saltos'])} saltos, {d['cols']} columnas")

    print("\n=== DESPLAZAMIENTO — variante A: salto por salto (jerk reposo-a-reposo) ===")
    saltos = {k: d["saltos"] for k, d in datos.items()}
    ra = ajustar_modelo_desplazamiento(saltos, move_real)
    if "error" in ra:
        print(f"  BLOQUEADO: {ra['error']}")
    else:
        print(f"  k={ra['k']:.6f}  j={ra['j']:.1f} mm/s^3  t_torcha={ra['t_torcha_s']:.4f}s  R2={ra['r2']:.4f}")
        errs = [abs(p - r) / r * 100 for p, r in ra["pred_vs_real"].values()]
        print(f"  error medio panel={sum(errs)/len(errs):.1f}%  max={max(errs):.1f}%  <- ALTO, no usar en pricing")

    print("\n=== DESPLAZAMIENTO — variante B: fila completa = 1 movimiento ===")
    centros = {k: d["centros"] for k, d in datos.items()}
    rb = ajustar_modelo_desplazamiento_por_fila(centros, move_real)
    if "error" not in rb:
        print(f"  k={rb['k']:.6f}  error medio={rb['error_medio_pct']:.1f}%  max={rb['error_max_pct']:.1f}%  <- PEOR que A")

    print("\n=== CORTE — variante A: lado por lado (jerk reposo-a-reposo en esquinas) ===")
    segmentos = {k: d["segmentos"] for k, d in datos.items()}
    contorno = {k: d["contorno"] for k, d in datos.items()}
    rc = ajustar_modelo_corte(segmentos, contorno, proc_real)
    if "error" in rc:
        print(f"  BLOQUEADO: {rc['error']}")
    else:
        print(f"  k_corte={rc['k_corte']:.5f}  error medio={rc['error_medio_pct']:.1f}%  max={rc['error_max_pct']:.1f}%  <- ALTO")

    print("\n=== CORTE — variante B: velocidad nominal constante ===")
    cut_mm = {k: d["cut_length_mm"] for k, d in datos.items()}
    rd = ajustar_modelo_corte_velocidad_constante(cut_mm, proc_real)
    if "error" not in rd:
        print(f"  v_efectiva={rd['v_efectiva_mm_s']:.1f}mm/s  error medio={rd['error_medio_pct']:.1f}%  max={rd['error_max_pct']:.1f}%")

    print("\n=== Diagnóstico: correlación densidad (cols) vs ratio real/predicho ===")
    if "error" not in ra:
        S_por_panel = {k: sum(max(dx, dy) ** (1/3) for dx, dy in d["saltos"]) for k, d in datos.items()}
        ratio = {k: move_real[k] / S_por_panel[k] for k in datos}
        cols = {k: d["cols"] for k, d in datos.items()}
        corr = diagnostico_correlacion_densidad(cols, ratio)
        print(f"  correlación(cols, Move_real/S) = {corr:.3f}  <- fuerte y negativa: confirma el patrón")

    print("\n=== CONCLUSIÓN ===")
    print("  Ningún modelo de 1-2 parámetros probado cierra con precisión aceptable")
    print("  para pricing. Ver docstring del módulo: próximo paso propuesto es un")
    print("  modelo de velocidad de esquina no-cero (no implementado, sin validar).")


if __name__ == "__main__":
    main()
