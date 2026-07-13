#!/usr/bin/env python3
"""Genera una batería de calibración láser con RATIOS travel/cut VARIADOS.

Motivo: la batería original P01–P14 tenía cut y travel casi perfectamente
correlacionados (r=0.997, todos con travel/cut ≈ 1.1) porque el paso entre
agujeros escalaba junto con el tamaño del agujero. Con esos datos, mínimos
cuadrados no puede separar α (corte) de β (desplazamiento).

Esta batería varía el tamaño de agujero (L) y el paso (p) de forma
INDEPENDIENTE, para cubrir un rango amplio de travel/cut (de agujeros grandes y
juntos → poco travel, a chicos y separados → mucho travel). Así los coeficientes
se pueden separar.

Cada panel se genera con la MISMA función del sistema que produce los paneles de
producción (`_write_cuadriculado_square_to_doc`), de modo que los términos crudos
(cut/travel/pierce) y las capas de zona (flycut) son idénticos a lo real.

Uso:
    source .venv/bin/activate
    python tools/generar_bateria_calibracion.py [dir_salida]

Salida:
    <dir>/B2_XX_*.dxf         — un DXF por panel (Constantino mide su tiempo en CypCut)
    <dir>/bateria2_muestras.json — plantilla para calibrar_laser.py (t_cypcut_s a completar)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "sistema_industrial"))

try:
    import ezdxf  # noqa: F401
    import numpy as np
    from sistema_industrial.presets.legacy_panel_adapter import _write_cuadriculado_square_to_doc
except ImportError as e:
    sys.exit(f"Falta dependencia ({e}). Activá el venv: source .venv/bin/activate")

MARGIN_MM = 10.0

# (hole_size_mm, step_mm, sheet_w, sheet_h) — diseñados para un rango amplio de travel/cut.
# L grande + p chico → ratio bajo (mucho corte).  L chico + p grande → ratio alto (mucho travel).
# Optimizados por barrido para minimizar la correlación cut~travel: r=0.75, VIF=2.3
# (vs r=0.997, VIF=151 de P01–P14). Rango travel/cut ≈ 0.37–3.1.
SPECS = [
    (60, 70, 500, 500),      # grande y junto → ratio bajo (mucho corte)
    (30, 70, 500, 500),
    (20, 40, 1000, 1000),    # denso grande
    (30, 140, 1000, 1000),
    (12, 70, 1000, 500),
    (8, 70, 1000, 500),
    (12, 70, 1000, 1000),
    (5, 25, 1000, 1000),     # muy denso chico (extremo)
    (8, 70, 1000, 1000),
    (5, 100, 1000, 1000),
    (5, 45, 1000, 1000),
    (5, 70, 1000, 1000),     # chico y separado → ratio alto (mucho travel)
]


def generar(dir_out: Path) -> list[dict]:
    dir_out.mkdir(parents=True, exist_ok=True)
    muestras = []
    for i, (L, p, W, H) in enumerate(SPECS, 1):
        doc = ezdxf.new()
        msp = doc.modelspace()
        r = _write_cuadriculado_square_to_doc(
            doc, msp, hole_size_mm=L, step_x_mm=p, step_y_mm=p,
            sheet_width_mm=W, sheet_height_mm=H, margin_mm=MARGIN_MM,
        )
        nombre = f"B2_{i:02d}_L{L}_p{p}_{W}x{H}"
        doc.saveas(dir_out / f"{nombre}.dxf")
        muestras.append({
            "nombre": nombre,
            "material": "Chapa N°14", "espesor_mm": 2.0,
            "hole_size_mm": L, "step_mm": p, "sheet_mm": f"{W}x{H}",
            "cut_length_mm": round(r["cut_length_mm"], 2),
            "travel_length_mm": round(r["travel_length_mm"], 2),
            "pierce_count": r["pierce_count"],
            "t_cypcut_s": 0.0,  # ← Constantino completa con el Total de CypCut
        })
    return muestras


def generar_combinado(dir_out: Path, gap_mm: float = 200.0, max_row_w_mm: float = 4000.0) -> list[dict]:
    """Genera UN solo DXF con los 12 paneles lado a lado (para seleccionar cada
    uno en CypCut y medir su tiempo). Devuelve el mapa de posiciones.

    Cada panel lleva una etiqueta de texto con su nombre en la capa 'ETIQUETAS'
    (no cortar), y se registra su posición (esquina inferior-izquierda) para
    identificarlo sin ambigüedad.
    """
    dir_out.mkdir(parents=True, exist_ok=True)
    doc = ezdxf.new()
    msp = doc.modelspace()
    if "ETIQUETAS" not in doc.layers:
        doc.layers.add("ETIQUETAS")

    mapa = []
    ox = oy = 0.0
    row_h = 0.0
    for i, (L, p, W, H) in enumerate(SPECS, 1):
        if ox > 0 and ox + W > max_row_w_mm:      # salto de fila
            ox = 0.0
            oy += row_h + gap_mm
            row_h = 0.0
        r = _write_cuadriculado_square_to_doc(
            doc, msp, hole_size_mm=L, step_x_mm=p, step_y_mm=p,
            sheet_width_mm=W, sheet_height_mm=H, margin_mm=MARGIN_MM,
            offset_x=ox, offset_y=oy,
        )
        nombre = f"B2_{i:02d}_L{L}_p{p}_{W}x{H}"
        msp.add_text(
            f"B2_{i:02d}", height=40,
            dxfattribs={"layer": "ETIQUETAS"},
        ).set_placement((ox + 10, oy + H + 20))
        mapa.append({
            "nombre": nombre, "orden": i,
            "pos_x_mm": round(ox, 1), "pos_y_mm": round(oy, 1),
            "sheet_mm": f"{W}x{H}",
            "cut_length_mm": round(r["cut_length_mm"], 2),
            "travel_length_mm": round(r["travel_length_mm"], 2),
            "pierce_count": r["pierce_count"],
            "t_cypcut_s": 0.0,
        })
        ox += W + gap_mm
        row_h = max(row_h, H)

    doc.saveas(dir_out / "bateria2_combinada.dxf")
    return mapa


def diagnostico(muestras: list[dict]) -> None:
    cut = np.array([m["cut_length_mm"] for m in muestras])
    travel = np.array([m["travel_length_mm"] for m in muestras])
    pierce = np.array([float(m["pierce_count"]) for m in muestras])
    ratio = travel / cut
    X = np.column_stack([cut, travel, pierce, np.ones(len(cut))])
    Xn = X / np.linalg.norm(X, axis=0)
    print(f"\n{'panel':<24}{'cut':>9}{'travel':>9}{'pierce':>8}{'tr/cut':>8}")
    for m, rr in zip(muestras, ratio):
        print(f"  {m['nombre']:<22}{m['cut_length_mm']:>9.0f}{m['travel_length_mm']:>9.0f}"
              f"{m['pierce_count']:>8}{rr:>8.2f}")
    print(f"\n  n={len(muestras)}   travel/cut ∈ [{ratio.min():.2f}, {ratio.max():.2f}]")
    print(f"  correlación cut~travel = {np.corrcoef(cut, travel)[0,1]:.4f}  (era 0.997 en P01–P14)")
    print(f"  nº de condición matriz de diseño = {np.linalg.cond(Xn):.1f}  (más bajo = mejor separación)")


def main() -> None:
    dir_out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("calibracion_bateria2")
    muestras = generar(dir_out)
    (dir_out / "bateria2_muestras.json").write_text(
        json.dumps({"_meta": "Batería 2 (ratios variados). Completá t_cypcut_s con el Total de CypCut de cada DXF.",
                    "muestras": muestras}, indent=2, ensure_ascii=False), encoding="utf-8")
    # DXF combinado (todos los paneles en un archivo) + mapa de posiciones
    mapa = generar_combinado(dir_out)
    (dir_out / "bateria2_combinada_mapa.json").write_text(
        json.dumps({"_meta": "Mapa del DXF combinado. En CypCut seleccioná cada panel y anotá su Total time. "
                             "Identificá cada uno por su etiqueta B2_XX, su posición (pos_x/pos_y) o su Piercing Count.",
                    "paneles": mapa}, indent=2, ensure_ascii=False), encoding="utf-8")
    diagnostico(muestras)
    print("\nDXF COMBINADO: bateria2_combinada.dxf (12 paneles con etiqueta B2_XX)")
    print(f"\n✓ {len(muestras)} DXF individuales + combinado + JSONs en {dir_out}/")


if __name__ == "__main__":
    main()
