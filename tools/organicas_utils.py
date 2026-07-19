#!/usr/bin/env python3
"""Utilidad compartida para probar el simulador contra las siluetas orgánicas
reales (Corazón, Cosmos) que vienen con SPLINE — tipo que
simulador_toolpath.extraer_entidades no soporta directamente (ver su
docstring: "las SPLINE ya vienen convertidas... ver dxf_validator.py", pero
dxf_validator.py solo VALIDA, no convierte — no hay conversor en producción
todavía). Reusa el mismo método que ya usa el código de producción para
renderizar thumbnails (ezdxf flattening), no depende de tkinter."""
from pathlib import Path

import ezdxf


def convertir_splines_a_lineas(dxf_path, out_path, tol_mm: float = 0.05) -> Path:
    """Copia un DXF reemplazando cada SPLINE por su aproximación poligonal
    (flattening) y dejando LINE/ARC/CIRCLE/LWPOLYLINE intactos."""
    doc = ezdxf.readfile(str(dxf_path))
    msp = doc.modelspace()
    splines = [e for e in msp if e.dxftype() == "SPLINE"]
    otras = [e for e in msp if e.dxftype() != "SPLINE"]

    nuevo = ezdxf.new()
    nmsp = nuevo.modelspace()
    for e in otras:
        t = e.dxftype()
        if t == "LINE":
            nmsp.add_line(e.dxf.start, e.dxf.end, dxfattribs={"layer": e.dxf.layer})
        elif t == "ARC":
            nmsp.add_arc(e.dxf.center, e.dxf.radius, e.dxf.start_angle, e.dxf.end_angle,
                        dxfattribs={"layer": e.dxf.layer})
        elif t == "CIRCLE":
            nmsp.add_circle(e.dxf.center, e.dxf.radius, dxfattribs={"layer": e.dxf.layer})
        elif t == "LWPOLYLINE":
            nmsp.add_lwpolyline(list(e.get_points()), close=e.closed,
                               dxfattribs={"layer": e.dxf.layer})
    for s in splines:
        pts = list(s.flattening(tol_mm))
        for p0, p1 in zip(pts, pts[1:]):
            nmsp.add_line((p0.x, p0.y), (p1.x, p1.y), dxfattribs={"layer": s.dxf.layer})

    out_path = Path(out_path)
    nuevo.saveas(str(out_path))
    return out_path
