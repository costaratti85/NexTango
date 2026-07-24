#!/usr/bin/env python3
"""Calibración del modelo físico de tiempo de láser (Panel Decorativo).

MODELO
------
Para un panel, el tiempo de máquina se estima como:

    T = α·cut_mm + β·travel_mm + γ·pierce + δ

donde:
    cut_mm     = largo total de recorrido CORTANDO (perímetro de todas las figuras)
    travel_mm  = largo total de recorrido DESPLAZÁNDOSE en rápido entre agujeros
    pierce     = cantidad de perforaciones (una por figura cerrada)
    α (alpha)  = s/mm cortando          → 1/α = velocidad de corte efectiva (mm/s)
    β (beta)   = s/mm desplazándose     → 1/β = velocidad de rápido efectiva (mm/s)
    γ (gamma)  = s por perforación      → tiempo de cada pierce (gas, ciclo)
    δ (delta)  = overhead fijo por trabajo (s) — posicionamiento inicial, arranque/fin

Estos son exactamente los campos `laser_a_s_per_mm`, `laser_b_s_per_hole`,
`laser_c_s_per_m2`, `laser_d_base_s` del DocType «SI Material Corte».
(Los sufijos `_per_hole`/`_per_m2` de los fieldnames son legacy y NO reflejan el
uso real: β multiplica travel_mm y γ multiplica pierce. Ver labels del DocType.)

⚠ γ (pierce) YA NO SE CALIBRA JUNTO con α/β/δ: es universal —SIN_FLYCUT derivado
por regresión aislada de Delay_s (tools/derivar_pierce_seconds.py, 2026-07-23),
CON_FLYCUT fijado por Constantino— ver PIERCE_SECONDS_* en
legacy_panel_adapter.py. Si corrés este script para un material/espesor nuevo,
NO uses el γ que salga del ajuste conjunto de 4 parámetros: ese γ ajustado
compensaría el error absorbiéndolo en α/β y los corrompería. Usá α y β del
ajuste (y δ si aplica), ignorá γ, y cargalos con set_laser_coefs.py dejando
`laser_c_s_per_m2` en 0.

MÉTODO
------
Regresión lineal por mínimos cuadrados (numpy.linalg.lstsq) sobre un set de
paneles de muestra. De cada panel se conocen sus términos geométricos crudos
(cut_mm, travel_mm, pierce) — que produce nuestro propio motor — y el TIEMPO
ESTIMADO DE CORTE que reporta CypCut. El script resuelve α, β, γ, δ que mejor
reproducen esos tiempos y reporta el error residual para saber si el modelo
ajusta bien.

USO
---
    source .venv/bin/activate      # numpy
    python tools/calibrar_laser.py calibracion_laser_muestras.json
    python tools/calibrar_laser.py muestras.json --sin-delta      # fuerza δ=0 (calibra solo α,β,γ)
    python tools/calibrar_laser.py muestras.json --por-material   # un ajuste por (material, espesor)

FORMATO DE ENTRADA (JSON)
-------------------------
    {
      "muestras": [
        {
          "nombre": "P01_tresbolillo_500x1000_d20",
          "material": "Chapa doble decapada",   # opcional (solo para --por-material)
          "espesor_mm": 0.9,                     # opcional
          "cut_length_mm": 21840.0,              # término crudo (del motor)
          "travel_length_mm": 9500.0,            # término crudo (del motor)
          "pierce_count": 432,                   # término crudo (del motor)
          "t_cypcut_s": 96.4                     # TIEMPO estimado por CypCut (lo mide Constantino)
        },
        ...
      ]
    }
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import numpy as np
except ImportError:
    sys.exit("Falta numpy. Activá el venv: source .venv/bin/activate")


CAMPOS_CRUDOS = ("cut_length_mm", "travel_length_mm", "pierce_count", "t_cypcut_s")


def cargar_muestras(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as f:
        data = json.load(f)
    muestras = data.get("muestras") if isinstance(data, dict) else data
    if not muestras:
        sys.exit(f"No hay 'muestras' en {path}")
    for i, m in enumerate(muestras):
        faltan = [c for c in CAMPOS_CRUDOS if c not in m]
        if faltan:
            sys.exit(f"Muestra #{i} ({m.get('nombre','?')}) sin campos: {faltan}")
    return muestras


def ajustar(muestras: list[dict], con_delta: bool = True) -> dict:
    """Resuelve α,β,γ,(δ) por mínimos cuadrados. Devuelve coeficientes + métricas."""
    cut = np.array([float(m["cut_length_mm"]) for m in muestras])
    travel = np.array([float(m["travel_length_mm"]) for m in muestras])
    pierce = np.array([float(m["pierce_count"]) for m in muestras])
    t_real = np.array([float(m["t_cypcut_s"]) for m in muestras])

    n = len(muestras)
    n_param = 4 if con_delta else 3
    if n < n_param:
        sys.exit(
            f"Se necesitan al menos {n_param} muestras para ajustar "
            f"{n_param} parámetros; hay {n}. Cargá más paneles."
        )

    # Matriz de diseño: columnas [cut, travel, pierce, (1)]
    cols = [cut, travel, pierce]
    if con_delta:
        cols.append(np.ones(n))
    A = np.column_stack(cols)

    coef, _, rank, _ = np.linalg.lstsq(A, t_real, rcond=None)
    alpha, beta, gamma = coef[0], coef[1], coef[2]
    delta = coef[3] if con_delta else 0.0

    # Advertencia de rango deficiente (columnas colineales → coeficientes no confiables)
    rango_deficiente = rank < n_param

    t_pred = A @ coef
    resid = t_pred - t_real
    rmse = float(np.sqrt(np.mean(resid ** 2)))
    mae = float(np.mean(np.abs(resid)))
    ss_res = float(np.sum(resid ** 2))
    ss_tot = float(np.sum((t_real - t_real.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    err_pct = np.where(t_real != 0, np.abs(resid) / t_real * 100.0, 0.0)

    return {
        "alpha": alpha, "beta": beta, "gamma": gamma, "delta": delta,
        "con_delta": con_delta, "n": n, "rank": int(rank),
        "rango_deficiente": rango_deficiente,
        "rmse": rmse, "mae": mae, "r2": r2,
        "max_err_pct": float(err_pct.max()),
        "t_real": t_real, "t_pred": t_pred, "err_pct": err_pct,
        "travel_todo_cero": bool(np.allclose(travel, 0.0)),
    }


def imprimir_reporte(res: dict, muestras: list[dict], etiqueta: str = "") -> None:
    a, b, g, d = res["alpha"], res["beta"], res["gamma"], res["delta"]
    titulo = f"CALIBRACIÓN {etiqueta}".strip()
    print("=" * 68)
    print(titulo)
    print("=" * 68)
    print(f"Muestras: {res['n']}   Parámetros: {'4 (α,β,γ,δ)' if res['con_delta'] else '3 (α,β,γ, δ=0)'}")
    print()
    print("COEFICIENTES:")
    print(f"  α  laser_a_s_per_mm  = {a:.6f} s/mm   " + (f"(v_corte ≈ {1/a:8.1f} mm/s)" if a > 0 else "(≤0 — revisar datos)"))
    print(f"  β  laser_b_s_per_hole = {b:.6f} s/mm   " + (f"(v_rápido ≈ {1/b:8.1f} mm/s)" if b > 0 else "(≤0 o sin travel)"))
    print(f"  γ  laser_c_s_per_m2  = {g:.4f} s/pierce")
    print(f"  δ  laser_d_base_s    = {d:.2f} s (overhead fijo)")
    print()
    print("BONDAD DE AJUSTE:")
    print(f"  R²          = {res['r2']:.4f}   (1.0 = perfecto; >0.95 muy bueno)")
    print(f"  RMSE        = {res['rmse']:.2f} s")
    print(f"  MAE         = {res['mae']:.2f} s")
    print(f"  Error máx.  = {res['max_err_pct']:.1f} %")
    print()
    print("PANEL POR PANEL (real vs predicho):")
    print(f"  {'nombre':<34} {'real_s':>8} {'pred_s':>8} {'err%':>7}")
    for m, tr, tp, ep in zip(muestras, res["t_real"], res["t_pred"], res["err_pct"]):
        print(f"  {str(m.get('nombre','?'))[:34]:<34} {tr:8.1f} {tp:8.1f} {ep:6.1f}%")
    print()

    avisos = []
    if res["rango_deficiente"]:
        avisos.append("RANGO DEFICIENTE: los términos crudos son colineales (paneles poco "
                      "variados). Coeficientes NO confiables — variá más el set.")
    if res["travel_todo_cero"]:
        avisos.append("TRAVEL todo en 0: no se puede estimar β. Usá paneles cuadriculados "
                      "(el motor sí computa su travel) o variá la densidad de agujeros.")
    if any(x < 0 for x in (a, b, g)):
        avisos.append("Algún coeficiente salió NEGATIVO (físicamente imposible): faltan "
                      "muestras o hay ruido en los tiempos. Sumá paneles o revisá t_cypcut.")
    if res["r2"] < 0.9:
        avisos.append(f"R²={res['r2']:.3f} bajo: el modelo lineal no ajusta bien estos datos.")
    for av in avisos:
        print("  ⚠ " + av)
    if not avisos:
        print("  ✓ Ajuste sano. Cargá α,β,γ,δ en el material correspondiente (SI Material Corte).")
    print()


def main() -> None:
    ap = argparse.ArgumentParser(description="Calibra el modelo físico de tiempo de láser.")
    ap.add_argument("muestras_json", type=Path, help="JSON con las muestras (ver docstring).")
    ap.add_argument("--sin-delta", action="store_true", help="Fuerza δ=0 (calibra solo α,β,γ).")
    ap.add_argument("--por-material", action="store_true",
                    help="Un ajuste separado por cada (material, espesor).")
    ap.add_argument("--salida", type=Path, default=None,
                    help="Escribe los coeficientes resultantes a un JSON.")
    args = ap.parse_args()

    muestras = cargar_muestras(args.muestras_json)
    con_delta = not args.sin_delta

    resultados = {}
    if args.por_material:
        grupos: dict = {}
        for m in muestras:
            k = (m.get("material", "?"), m.get("espesor_mm", "?"))
            grupos.setdefault(k, []).append(m)
        for (mat, esp), grupo in grupos.items():
            res = ajustar(grupo, con_delta)
            imprimir_reporte(res, grupo, etiqueta=f"— {mat} {esp} mm")
            resultados[f"{mat}|{esp}"] = res
    else:
        res = ajustar(muestras, con_delta)
        imprimir_reporte(res, muestras, etiqueta="GLOBAL")
        resultados["global"] = res

    if args.salida:
        payload = {
            k: {"alpha": r["alpha"], "beta": r["beta"], "gamma": r["gamma"],
                "delta": r["delta"], "r2": r["r2"], "rmse": r["rmse"], "n": r["n"]}
            for k, r in resultados.items()
        }
        args.salida.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Coeficientes escritos en {args.salida}")


if __name__ == "__main__":
    main()
