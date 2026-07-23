#!/usr/bin/env python3
"""Verificación empírica del fix de centrado (queue.json PUNTO_CENTRADO_AL_GUARDAR_PATRONES).

El centrado-al-GUARDAR ya existe en producción (composer.py::_center_msp_on_origin,
commit b5a8bc3, deployado) — este script no cambia código, solo mide el estado
ACTUAL: Philo llena la chapa con sangrado en los 4 lados (el bug reportado), y
subte/Aconcagua/Cosmos (que dependen de estar bien centrados en su archivo,
ahora que load_pattern ya no centra al abrir) siguen tileando sin bandas vacías.

Corre el motor real (LegacyPanelAdapter, pattern_type="dxf", cut_partial_figures
igual que producción) sobre los DXF reales bajados del server, y mide el bbox de
la geometría resultante contra el tamaño de chapa + margen.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] /
                     "apps" / "sistema_industrial" / "sistema_industrial"))

import math

import ezdxf

from presets.legacy_panel_adapter import LegacyPanelAdapter, LegacyPanelRunRequest


def _arc_bbox(cx, cy, r, a0_deg, a1_deg):
    """Bbox real de un ARCO (respeta el barrido start/end) -- NO centro±radio,
    que sobreestima brutalmente arcos de radio grande y barrido chico (muy
    comunes en vectorización: curvas suaves aproximadas con radios enormes)."""
    a0 = math.radians(a0_deg % 360)
    a1 = math.radians(a1_deg % 360)
    if a1 <= a0:
        a1 += 2 * math.pi
    pts = [(cx + r * math.cos(a0), cy + r * math.sin(a0)),
          (cx + r * math.cos(a1), cy + r * math.sin(a1))]
    for k in range(4):
        ang = k * math.pi / 2
        while ang < a0:
            ang += 2 * math.pi
        if a0 <= ang <= a1:
            pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), max(xs), min(ys), max(ys)

DXF_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
OUT_DIR = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp/verif_centrado_out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

CASOS = [
    # nombre, archivo, step_x, step_y, width_mm, height_mm
    ("Philo",     "Philo_OffX360_OffY623_v3.dxf",     360.0, 623.0, 550.0, 1500.0),
    ("subte",     "subte_Offx84_Offy84_v3.dxf",        84.0,  84.0, 550.0, 1500.0),
    ("Aconcagua", "Aconcagua_OFF_XY_85_v3.dxf",        85.0,  85.0, 550.0, 1500.0),
    ("Cosmos",    "Cosmos_OffXY_500_v3.dxf",          500.0, 500.0, 550.0, 1500.0),
]

MARGIN = 20.0


def bbox_de_dxf(path):
    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()
    xs, ys = [], []
    for e in msp:
        t = e.dxftype()
        if t == "LINE":
            xs += [e.dxf.start.x, e.dxf.end.x]
            ys += [e.dxf.start.y, e.dxf.end.y]
        elif t == "ARC":
            cx, cy, r = e.dxf.center.x, e.dxf.center.y, e.dxf.radius
            x0, x1, y0, y1 = _arc_bbox(cx, cy, r, e.dxf.start_angle, e.dxf.end_angle)
            xs += [x0, x1]; ys += [y0, y1]
        elif t == "CIRCLE":
            cx, cy, r = e.dxf.center.x, e.dxf.center.y, e.dxf.radius
            xs += [cx - r, cx + r]
            ys += [cy - r, cy + r]
        elif t == "LWPOLYLINE":
            pts = list(e.get_points())
            xs += [p[0] for p in pts]
            ys += [p[1] for p in pts]
        elif t == "SPLINE":
            for cp in e.control_points:
                xs.append(cp[0]); ys.append(cp[1])
    if not xs:
        return None
    return min(xs), max(xs), min(ys), max(ys)


def verificar(nombre, archivo, step_x, step_y, width_mm, height_mm):
    src = DXF_DIR / archivo
    if not src.exists():
        print(f"{nombre}: FALTA {src}")
        return None
    out_dxf = OUT_DIR / f"panel_{nombre}.dxf"
    req = LegacyPanelRunRequest(
        preset_code=f"verif_{nombre}",
        preset_name=f"verif_{nombre}",
        material="generic",
        thickness_mm=2.0,
        width_mm=width_mm,
        height_mm=height_mm,
        quantity=1,
        output_dxf_path=out_dxf,
        pattern_type="dxf",
        pattern_dxf_path=src,
        step_x_mm=step_x,
        step_y_mm=step_y,
        margin_mm=MARGIN,
        cut_partial_figures=True,
    )
    result = LegacyPanelAdapter().run(req)
    total_geom = sum(r.get("geometry_item_count", 0) for r in result.calculated_resources)

    bbox = bbox_de_dxf(out_dxf)
    if bbox is None:
        print(f"{nombre}: SIN GEOMETRÍA generada (0 items) -- FALLA")
        return {"ok": False, "nombre": nombre}

    x0, x1, y0, y1 = bbox
    # sangrado esperado: la geometría debe llegar hasta cerca del margen en los 4 lados
    # (panel centrado en (width/2, height/2), margen MARGIN)
    izq = x0 - MARGIN
    der = (width_mm - MARGIN) - x1
    abajo = y0 - MARGIN
    arriba = (height_mm - MARGIN) - y1
    print(f"{nombre:10s} geom_items={total_geom:4d}  bbox=({x0:.1f},{y0:.1f})-({x1:.1f},{y1:.1f})  "
          f"huecos respecto al margen: izq={izq:6.1f} der={der:6.1f} abajo={abajo:6.1f} arriba={arriba:6.1f}")
    return {"ok": True, "nombre": nombre, "geom_items": total_geom,
            "huecos": {"izq": izq, "der": der, "abajo": abajo, "arriba": arriba}}


if __name__ == "__main__":
    print(f"=== Verificación de tileo (chapa 550x1500, margen {MARGIN}, cut_partial_figures=True) ===")
    resultados = []
    for caso in CASOS:
        r = verificar(*caso)
        if r:
            resultados.append(r)
    print()
    print("Un 'hueco' grande (>> tamaño de un tile) del lado que sea = franja sin llenar (el bug).")
