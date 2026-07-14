"""Local sales UI for decorative panels — gallery edition.

This is a temporary internal interface until the Frappe UI is ready. It uses
Python's standard HTTP server and calls the legacy panel service unchanged.

Gallery workflow:
  1. Step 1 — Select pattern from gallery (Tresbolillo or DXF from library)
  2. Step 2 — Select outline (Rectangle only in V1; others are "Coming soon")
  3. Step 3 — Fill parameters (dimensions, margin, distribution, material, etc.)
  4. Add to batch list
  5. Generate DXF for all batches
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from contextlib import redirect_stdout
from dataclasses import dataclass
from email.parser import BytesParser
from email.policy import default as email_policy
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import StringIO
from importlib import import_module
from pathlib import Path
from urllib.parse import parse_qs, urlparse


logger = logging.getLogger(__name__)


def _browse_dxf_file() -> str:
    """Open a native file dialog via subprocess to avoid tkinter threading crashes.

    tkinter must run in the main thread. Since the HTTP server handles requests
    in worker threads, calling Tk() directly causes Tcl_AsyncDelete crashes on
    Python 3.14. Running a fresh subprocess sidesteps this completely.
    """
    try:
        import subprocess, sys
        script = (
            "import tkinter as tk; from tkinter import filedialog; "
            "root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True); "
            "path = filedialog.askopenfilename("
            "title='Seleccionar archivo DXF', "
            "filetypes=[('DXF', '*.dxf'), ('Todos', '*.*')]); "
            "print(path or '')"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True, text=True, timeout=120
        )
        return result.stdout.strip()
    except Exception:
        return ""

from sistema_industrial.presets.legacy_panel_adapter import (
    _write_cuadriculado_square_to_doc,
    _write_tresbolillo_hex_to_doc,
    add_pattern_to_library,
    calculate_consumed_resources,
    calculate_cut_length_mm,
    calculate_pierce_count,
    calculate_sheet_area_m2,
    delete_pattern_from_library,
    find_legacy_panel_dir,
    get_pattern_library_patterns,
    validate_dxf_entities,
)
from sistema_industrial.presets.panel_service import (
    LegacyPanelService,
    LegacyPanelServiceInput,
    LegacyPanelServiceResult,
    _build_cut_piece_payload,
    _build_quotation_payload,
    write_panel_service_outputs,
)
from sistema_industrial.pricing_sync.price_cache import PriceCache


DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[4] / "outputs" / "panel_sales_demo"
DEFAULT_PRICE_FILE = Path(__file__).resolve().parents[4] / "fixtures" / "prices" / "tango_price_list_sample.json"
STATIC_DIR = Path(__file__).resolve().parents[1] / "static"
THUMBNAIL_DIR = STATIC_DIR / "pattern_thumbnails"
MATERIAL_TABLE_FILE = Path(__file__).resolve().parents[4] / "Programas_hechos" / "Panel Decorativo" / "material_table.json"
DAILY_PRICES_FILE = Path(__file__).resolve().parents[4] / "Programas_hechos" / "Panel Decorativo" / "daily_prices.json"
TOOLS_DIR = Path(__file__).resolve().parents[4] / "tools"
PRESUPUESTOS_DIR = Path(__file__).resolve().parents[4] / "Programas_hechos" / "Panel Decorativo" / "presupuestos"
PRESUPUESTO_COUNTER_FILE = Path(__file__).resolve().parents[4] / "Programas_hechos" / "Panel Decorativo" / "presupuesto_counter.json"
LAST_GENERATE_FILE = Path(__file__).resolve().parents[4] / "Programas_hechos" / "Panel Decorativo" / "last_generate.json"
PLEGADOS_DIR = Path(__file__).resolve().parents[4] / "Programas_hechos" / "Plegados"
PLEGADOS_PEDIDOS_DIR = PLEGADOS_DIR / "pedidos"
PLEGADOS_PERFILES_HTML = Path(__file__).resolve().parents[4] / "research" / "cybelec" / "plegado_app" / "index.html"
CORTES_DIR = Path(__file__).resolve().parents[4] / "Programas_hechos" / "Cortes"
LISTA_CORTE_FILE = CORTES_DIR / "lista_corte.json"


# ---------------------------------------------------------------------------
# DXF spline conversion helpers (no tkinter)
# ---------------------------------------------------------------------------

def _import_spline_converter():
    """Import conversion functions from tools/dxf_spline_to_arcs.py without tkinter.

    The tools module imports tkinter at the top level, which crashes in
    headless contexts.  We patch sys.modules to stub out tkinter before the
    import so the conversion functions are available regardless.
    """
    import types
    import sys as _sys

    # Build minimal tkinter stubs so the module-level import doesn't crash.
    # The tool file does: import tkinter as tk; from tkinter.ttk import Progressbar
    _stubs_defs: dict[str, dict] = {
        "tkinter": {
            "DoubleVar": type("DoubleVar", (), {}),
            "StringVar": type("StringVar", (), {}),
            "Tk": type("Tk", (), {}),
            "Label": type("Label", (), {}),
            "Button": type("Button", (), {}),
            "Entry": type("Entry", (), {}),
            "Spinbox": type("Spinbox", (), {}),
            "Text": type("Text", (), {}),
            "Scrollbar": type("Scrollbar", (), {}),
            "LabelFrame": type("LabelFrame", (), {}),
            "END": "end",
            "LEFT": "left",
            "RIGHT": "right",
            "X": "x",
            "Y": "y",
            "BOTH": "both",
            "HORIZONTAL": "horizontal",
            "DISABLED": "disabled",
            "NORMAL": "normal",
        },
        "tkinter.ttk": {
            "Progressbar": type("Progressbar", (), {}),
        },
        "tkinter.filedialog": {},
        "tkinter.messagebox": {},
    }
    _originals = {}
    for _name, _attrs in _stubs_defs.items():
        if _name not in _sys.modules:
            _mod = types.ModuleType(_name)
            for _k, _v in _attrs.items():
                setattr(_mod, _k, _v)
            _sys.modules[_name] = _mod
            _originals[_name] = None
        else:
            _originals[_name] = _sys.modules[_name]

    tools_path = str(TOOLS_DIR)
    inserted = tools_path not in _sys.path
    if inserted:
        _sys.path.insert(0, tools_path)
    try:
        # Force reload if already cached with tkinter stubs in place
        import importlib
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "_dxf_spline_to_arcs",
            str(TOOLS_DIR / "dxf_spline_to_arcs.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
    finally:
        if inserted:
            try:
                _sys.path.remove(tools_path)
            except ValueError:
                pass
        # Restore originals (remove stubs we added)
        for _name, _orig in _originals.items():
            if _orig is None:
                _sys.modules.pop(_name, None)
            else:
                _sys.modules[_name] = _orig

    return mod


def convert_dxf_splines_clean(dxf_path: str, output_path: str, tolerance: float = 0.1) -> dict:
    """Convert splines/lwpolylines to arcs and produce a clean DXF.

    "Clean" means only LINE and ARC entities in layer ARCOS_CONVERTIDOS — the
    original SPLINE/LWPOLYLINE entities are NOT copied to the output.

    Returns a dict with keys: converted_count, arc_count, line_count.
    """
    try:
        import ezdxf
    except ImportError as exc:
        raise RuntimeError("ezdxf no está instalado — ejecutar: pip install ezdxf") from exc

    converter = _import_spline_converter()

    dxf_path = str(dxf_path)
    output_path = str(output_path)

    # Read source document
    try:
        with open(dxf_path, "r", encoding="utf-8", errors="ignore") as f:
            src_doc = ezdxf.read(f)
    except Exception:
        with open(dxf_path, "r", encoding="latin-1") as f:
            src_doc = ezdxf.read(f)

    # Create a fresh document to avoid carrying over unwanted entities
    out_doc = ezdxf.new(dxfversion="R2010")
    out_msp = out_doc.modelspace()

    # Create ARCOS_CONVERTIDOS layer in red
    layer = out_doc.layers.new("ARCOS_CONVERTIDOS")
    layer.color = 1  # AutoCAD red

    target_layer = "ARCOS_CONVERTIDOS"
    src_msp = src_doc.modelspace()

    # Collect entities to convert
    splines = [e for e in src_msp if e.dxftype() == "SPLINE"]
    lwpolylines_with_bulge = []
    for e in src_msp:
        if e.dxftype() == "LWPOLYLINE":
            try:
                has_arc = any(
                    len(v) > 4 and v[4] != 0
                    for v in e.vertices()
                )
            except Exception:
                has_arc = False
            if has_arc:
                lwpolylines_with_bulge.append(e)

    # Also copy through other entities (LINE, ARC, CIRCLE) unchanged
    for e in src_msp:
        et = e.dxftype()
        if et in ("LINE", "ARC", "CIRCLE"):
            try:
                copy = out_msp.add_entity(e.copy())  # type: ignore[arg-type]
            except Exception:
                pass

    converted_count = 0
    arc_count = 0
    line_count = 0

    for spline in splines:
        arcs, lines = converter.discretize_and_convert_spline(
            spline, out_msp, target_layer, fit_tol=tolerance
        )
        if arcs or lines:
            converted_count += 1
            arc_count += len(arcs)
            line_count += len(lines)

    for poly in lwpolylines_with_bulge:
        arcs, lines = converter.process_lwpolyline(poly, out_msp, target_layer)
        if arcs or lines:
            converted_count += 1
            arc_count += len(arcs)
            line_count += len(lines)

    out_doc.saveas(output_path)
    return {
        "converted_count": converted_count,
        "arc_count": arc_count,
        "line_count": line_count,
    }


def _fit_circle_kasa(pts: list) -> tuple | None:
    """Kasa least-squares circle fit. Returns (cx, cy, r, max_error) or None."""
    n = len(pts)
    sx = sy = sxx = syy = sxy = sx3 = sy3 = sxxy = sxyy = 0.0
    for x, y in pts:
        sx += x; sy += y
        sxx += x * x; syy += y * y; sxy += x * y
        sx3 += x ** 3; sy3 += y ** 3
        sxxy += x * x * y; sxyy += x * y * y
    A = 2.0 * (sx * sx - n * sxx)
    B = 2.0 * (sx * sy - n * sxy)
    C = 2.0 * (sy * sy - n * syy)
    D = sx * sxx - n * sx3 + sx * syy - n * sxyy
    E = sy * sxx - n * sxxy + sy * syy - n * sy3
    det = A * C - B * B
    if abs(det) < 1e-10:
        return None
    cx = (D * C - B * E) / det
    cy = (A * E - B * D) / det
    import math as _math
    r = _math.sqrt(sum((x - cx) ** 2 + (y - cy) ** 2 for x, y in pts) / n)
    max_err = max(abs(_math.sqrt((x - cx) ** 2 + (y - cy) ** 2) - r) for x, y in pts)
    return cx, cy, r, max_err


def _try_poly_as_circle(entity, tol_mm: float, r_min: float, r_max: float) -> tuple | None:
    """Return (cx, cy, r) if LWPOLYLINE entity fits a circle within tolerance, else None."""
    try:
        if not entity.closed:
            return None
        pts = [(v[0], v[1]) for v in entity.vertices()]
    except Exception:
        return None
    if len(pts) < 6:
        return None
    res = _fit_circle_kasa(pts)
    if res is None:
        return None
    cx, cy, r, max_err = res
    if max_err > tol_mm or r < r_min or r > r_max:
        return None
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    w = max(xs) - min(xs); h = max(ys) - min(ys)
    if min(w, h) < 0.5 * max(w, h):
        return None
    return cx, cy, r


def convert_dxf_poly_to_circles(
    dxf_path: str, output_path: str,
    tol_mm: float = 0.5, r_min: float = 1.0, r_max: float = 200.0,
) -> int:
    """Replace circular LWPOLYLINE entities with CIRCLE in a DXF file.

    Overwrites output_path with the converted document.
    Returns the number of entities converted.
    """
    try:
        import ezdxf as _ezdxf
    except ImportError as exc:
        raise RuntimeError("ezdxf no está instalado — ejecutar: pip install ezdxf") from exc

    try:
        with open(dxf_path, "r", encoding="utf-8", errors="ignore") as f:
            doc = _ezdxf.read(f)
    except Exception:
        with open(dxf_path, "r", encoding="latin-1") as f:
            doc = _ezdxf.read(f)

    msp = doc.modelspace()
    candidates = [e for e in msp if e.dxftype() == "LWPOLYLINE"]
    converted = 0
    to_delete = []
    for entity in candidates:
        result = _try_poly_as_circle(entity, tol_mm, r_min, r_max)
        if result is None:
            continue
        cx, cy, r = result
        layer = entity.dxf.layer if entity.dxf.hasattr("layer") else "0"
        circle = msp.add_circle(center=(cx, cy, 0), radius=r)
        circle.dxf.layer = layer
        to_delete.append(entity)
        converted += 1
    for entity in to_delete:
        msp.delete_entity(entity)
    doc.saveas(output_path)
    return converted


def _dxf_to_svg(dxf_path: str, mode: str = "original") -> str:
    """Render a DXF file to an inline SVG string for browser preview.

    mode='original'  — render all entities (splines discretised as polylines)
    mode='converted' — render all LINE/ARC entities from ARCOS_CONVERTIDOS layer
    """
    import math as _math

    try:
        import ezdxf
    except ImportError:
        return '<svg xmlns="http://www.w3.org/2000/svg"><text y="20" fill="red">ezdxf no disponible</text></svg>'

    try:
        try:
            with open(dxf_path, "r", encoding="utf-8", errors="ignore") as f:
                doc = ezdxf.read(f)
        except Exception:
            with open(dxf_path, "r", encoding="latin-1") as f:
                doc = ezdxf.read(f)
    except Exception as exc:
        return f'<svg xmlns="http://www.w3.org/2000/svg"><text y="20" fill="red">Error: {escape(str(exc))}</text></svg>'

    msp = doc.modelspace()

    # Collect (x, y) segments as list of polyline point-lists
    segments: list[list[tuple[float, float]]] = []

    def _add_line(x1, y1, x2, y2):
        segments.append([(x1, y1), (x2, y2)])

    def _add_arc_pts(cx, cy, r, a_start_deg, a_end_deg):
        """Discretise an arc into polyline points (CCW, AutoCAD convention)."""
        if r <= 0:
            return
        a0 = a_start_deg % 360
        a1 = a_end_deg % 360
        if a1 <= a0:
            a1 += 360
        span = a1 - a0
        n = max(8, int(span / 5))  # one point per 5°
        pts = []
        for i in range(n + 1):
            angle = _math.radians(a0 + span * i / n)
            pts.append((cx + r * _math.cos(angle), cy + r * _math.sin(angle)))
        if pts:
            segments.append(pts)

    for entity in msp:
        et = entity.dxftype()

        if mode == "converted":
            # Only draw ARCOS_CONVERTIDOS layer entities
            try:
                layer_name = entity.dxf.layer
            except Exception:
                layer_name = ""
            if layer_name != "ARCOS_CONVERTIDOS":
                # In converted output allow also non-restricted originals (LINE, ARC, CIRCLE)
                # that are NOT in ARCOS_CONVERTIDOS (they have no original layer issue)
                # — actually we only want ARCOS_CONVERTIDOS
                continue

        try:
            if et == "LINE":
                s = entity.dxf.start
                e2 = entity.dxf.end
                _add_line(s.x, s.y, e2.x, e2.y)
            elif et == "ARC":
                c = entity.dxf.center
                _add_arc_pts(c.x, c.y, entity.dxf.radius,
                             entity.dxf.start_angle, entity.dxf.end_angle)
            elif et == "CIRCLE":
                c = entity.dxf.center
                _add_arc_pts(c.x, c.y, entity.dxf.radius, 0, 360)
            elif et == "SPLINE":
                pts = []
                try:
                    pts = list(entity.flattening(0.1))
                except Exception:
                    try:
                        pts = list(entity.vertices())
                    except Exception:
                        pass
                if pts:
                    segments.append([(p.x, p.y) for p in pts])
            elif et == "LWPOLYLINE":
                raw = list(entity.vertices())
                if raw:
                    pts2d = []
                    for v in raw:
                        if isinstance(v, tuple):
                            pts2d.append((float(v[0]), float(v[1])))
                        else:
                            try:
                                pts2d.append((float(v.x), float(v.y)))
                            except Exception:
                                pass
                    if pts2d:
                        if entity.closed and pts2d:
                            pts2d.append(pts2d[0])
                        segments.append(pts2d)
        except Exception:
            pass

    if not segments:
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 60">'
            '<text x="10" y="35" fill="#888" font-size="12">Sin geometria para mostrar</text>'
            "</svg>"
        )

    # Compute bounding box
    all_x = [p[0] for seg in segments for p in seg]
    all_y = [p[1] for seg in segments for p in seg]
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    w = max_x - min_x or 1.0
    h = max_y - min_y or 1.0

    pad = max(w, h) * 0.05
    vb_x = min_x - pad
    vb_y = min_y - pad
    vb_w = w + 2 * pad
    vb_h = h + 2 * pad

    stroke_color = "#cc0000" if mode == "converted" else "#555555"
    stroke_w = max(vb_w, vb_h) * 0.003

    # Build SVG paths — flip Y axis (DXF Y up, SVG Y down)
    paths = []
    for seg in segments:
        if len(seg) < 2:
            continue
        def _sy(y):
            return vb_y + vb_h - (y - vb_y)

        coords = " ".join(
            f"{'M' if i == 0 else 'L'}{p[0]},{_sy(p[1])}"
            for i, p in enumerate(seg)
        )
        paths.append(f'<path d="{coords}" fill="none" stroke="{stroke_color}" stroke-width="{stroke_w:.4f}" stroke-linecap="round" stroke-linejoin="round"/>')

    paths_str = "\n".join(paths)

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{vb_x:.4f} {vb_y:.4f} {vb_w:.4f} {vb_h:.4f}" '
        f'preserveAspectRatio="xMidYMid meet" '
        f'style="width:100%;height:100%">'
        f'{paths_str}'
        f"</svg>"
    )


def _dxf_entities_json(dxf_path: str) -> list[dict]:
    """Extract LINE and ARC entities from a DXF file as a list of dicts.

    Reads entities from the ARCOS_CONVERTIDOS layer if present, otherwise
    from all layers.  Each dict has a unique 'id' key assigned at read time.

    Returns a list of:
        {"type": "line", "x1": ..., "y1": ..., "x2": ..., "y2": ..., "id": "eN"}
        {"type": "arc", "cx": ..., "cy": ..., "radius": ...,
         "startAngle": ..., "endAngle": ..., "id": "eN"}
    """
    try:
        import ezdxf
    except ImportError:
        raise RuntimeError("ezdxf no instalado")

    try:
        try:
            with open(dxf_path, "r", encoding="utf-8", errors="ignore") as f:
                doc = ezdxf.read(f)
        except Exception:
            with open(dxf_path, "r", encoding="latin-1") as f:
                doc = ezdxf.read(f)
    except Exception as exc:
        raise RuntimeError(f"No se pudo leer el DXF: {exc}") from exc

    msp = doc.modelspace()

    # Determine whether ARCOS_CONVERTIDOS layer exists in this file
    has_converted_layer = any(
        e.dxf.layer == "ARCOS_CONVERTIDOS"
        for e in msp
        if hasattr(e.dxf, "layer")
    )

    entities: list[dict] = []
    idx = 0
    for entity in msp:
        et = entity.dxftype()
        if has_converted_layer:
            try:
                layer_name = entity.dxf.layer
            except Exception:
                continue
            if layer_name != "ARCOS_CONVERTIDOS":
                continue
        try:
            if et == "LINE":
                s = entity.dxf.start
                e2 = entity.dxf.end
                entities.append({
                    "type": "line",
                    "x1": float(s.x), "y1": float(s.y),
                    "x2": float(e2.x), "y2": float(e2.y),
                    "id": f"e{idx}",
                })
                idx += 1
            elif et == "ARC":
                c = entity.dxf.center
                entities.append({
                    "type": "arc",
                    "cx": float(c.x), "cy": float(c.y),
                    "radius": float(entity.dxf.radius),
                    "startAngle": float(entity.dxf.start_angle),
                    "endAngle": float(entity.dxf.end_angle),
                    "id": f"e{idx}",
                })
                idx += 1
        except Exception:
            pass

    return entities


def _entities_to_dxf(entities: list[dict], out_path: str) -> None:
    """Write a list of entity dicts to a DXF file using ezdxf."""
    try:
        import ezdxf
    except ImportError:
        raise RuntimeError("ezdxf no instalado")

    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()
    layer = doc.layers.new("ARCOS_CONVERTIDOS")
    layer.color = 1  # AutoCAD red
    for e in entities:
        try:
            if e["type"] == "line":
                msp.add_line(
                    (float(e["x1"]), float(e["y1"])),
                    (float(e["x2"]), float(e["y2"])),
                    dxfattribs={"layer": "ARCOS_CONVERTIDOS"},
                )
            elif e["type"] == "arc":
                msp.add_arc(
                    center=(float(e["cx"]), float(e["cy"])),
                    radius=float(e["radius"]),
                    start_angle=float(e["startAngle"]),
                    end_angle=float(e["endAngle"]),
                    dxfattribs={"layer": "ARCOS_CONVERTIDOS"},
                )
        except Exception:
            pass
    doc.saveas(out_path)


# ---------------------------------------------------------------------------
# MaterialTable — stores physical conversion factors per material+espesor
# ---------------------------------------------------------------------------

class MaterialTable:
    """Manages the material conversion factor table stored as a JSON list.

    Each entry is a dict with keys:
        material, espesor_mm, densidad_kg_m2, velocidad_corte_mm_s,
        tiempo_perforacion_s, consumible_por_perforacion
    """

    REQUIRED_KEYS = (
        "material",
        "espesor_mm",
        "densidad_kg_m2",
        "velocidad_corte_mm_s",
        "tiempo_perforacion_s",
        "consumible_por_perforacion",
    )

    def __init__(self, file_path: "Path | None" = None):
        self._path = file_path if file_path is not None else MATERIAL_TABLE_FILE
        self._entries: list[dict] = []
        self.load()

    def load(self) -> None:
        if not self._path.exists():
            self._entries = []
            return
        with self._path.open("r", encoding="utf-8") as f:
            self._entries = json.load(f)

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(self._entries, f, indent=2, ensure_ascii=False)

    def list(self) -> list[dict]:
        return list(self._entries)

    def add(self, entry: dict) -> None:
        for key in self.REQUIRED_KEYS:
            if key not in entry:
                raise ValueError(f"Campo requerido ausente: {key}")
        # Normalise numeric fields; calibre is optional (string, default "-")
        normalised = {
            "material": str(entry["material"]).strip(),
            "familia": str(entry.get("familia", "")).strip(),
            "calibre": str(entry.get("calibre", "-")).strip() or "-",
            "espesor_mm": float(entry["espesor_mm"]),
            "densidad_kg_m2": float(entry["densidad_kg_m2"]),
            "velocidad_corte_mm_s": float(entry["velocidad_corte_mm_s"]),
            "tiempo_perforacion_s": float(entry["tiempo_perforacion_s"]),
            "consumible_por_perforacion": float(entry["consumible_por_perforacion"]),
        }
        if not normalised["material"]:
            raise ValueError("El campo 'material' no puede estar vacio")
        if normalised["espesor_mm"] <= 0:
            raise ValueError("espesor_mm debe ser mayor a cero")
        # Replace if same material+espesor already exists, otherwise append
        for i, existing in enumerate(self._entries):
            if (
                existing["material"] == normalised["material"]
                and float(existing["espesor_mm"]) == normalised["espesor_mm"]
            ):
                self._entries[i] = normalised
                self.save()
                return
        self._entries.append(normalised)
        self.save()

    def delete(self, material: str, espesor_mm: float) -> None:
        before = len(self._entries)
        self._entries = [
            e for e in self._entries
            if not (e["material"] == material and float(e["espesor_mm"]) == espesor_mm)
        ]
        if len(self._entries) == before:
            raise KeyError(f"No encontrado: {material} {espesor_mm} mm")
        self.save()


# ---------------------------------------------------------------------------
# Daily-prices loader
# ---------------------------------------------------------------------------

def _load_daily_prices() -> tuple[dict, bool]:
    """Load daily_prices.json.

    Returns (prices_dict, prices_missing).
    prices_missing=True when the file does not exist or all relevant prices are 0/None.
    """
    if not DAILY_PRICES_FILE.exists():
        return {}, True
    try:
        with DAILY_PRICES_FILE.open("r", encoding="utf-8") as f:
            prices = json.load(f)
    except Exception:
        return {}, True

    # Migrar claves viejas si existen
    if "precio_kg_acero_negro" in prices and "precio_kg_doble_decapada" not in prices:
        prices["precio_kg_doble_decapada"] = prices.pop("precio_kg_acero_negro")
    if "precio_kg_inoxidable" in prices and "precio_kg_inoxidable_304" not in prices:
        prices["precio_kg_inoxidable_304"] = prices.pop("precio_kg_inoxidable")

    # precio_segundo NO va acá: es fuente única desde SI Precios Globales
    # (ver _precio_segundo_laser). Estas son las claves de precio por kg / plegado.
    relevant_keys = (
        "precio_kg_doble_decapada",
        "precio_kg_galvanizado",
        "precio_kg_inoxidable_430",
        "precio_kg_inoxidable_304",
        "precio_doblez_plegadora",
    )
    all_zero = all(
        not prices.get(k) or float(prices.get(k) or 0) == 0
        for k in relevant_keys
    )
    return prices, all_zero


# ---------------------------------------------------------------------------
# Cost calculation
# ---------------------------------------------------------------------------

def _precio_segundo_laser(daily_prices: dict) -> float:
    """Precio por segundo de máquina — FUENTE DE VERDAD ÚNICA.

    El precio por segundo vive en el doctype «SI Precios Globales»
    (campo `precio_segundo_laser`), que es el mismo que usan los doctypes
    SI Presupuesto Panel y SI Pedido Plegado. Así el precio sale idéntico por
    cualquier camino de cálculo.

    Fallback al dict de precios (`precio_segundo_laser`, o el legacy
    `precio_segundo_maquina`) solo cuando frappe no está disponible — p.ej.
    tests o la app standalone legacy sin base de datos.
    """
    try:
        import frappe
        pg = frappe.get_single("SI Precios Globales")
        val = float(pg.precio_segundo_laser or 0)
        if val > 0:
            return val
    except Exception:
        pass
    return float(
        daily_prices.get("precio_segundo_laser")
        or daily_prices.get("precio_segundo_maquina")
        or 0
    )


def calculate_cost(consumed_resources: dict, material_name: str, daily_prices: dict) -> dict:
    """Calculate cost for a batch given consumed_resources and daily prices.

    consumed_resources: {"material_kg": X, "machine_seconds": Y, "pierce_count": Z}
    material_name: e.g. "Galvanizado" | "Acero negro" | "Inoxidable 304"
    daily_prices: dict de precios de material (por kg). El precio por segundo NO
        sale de acá: es único y viene de SI Precios Globales (ver _precio_segundo_laser).
    Returns: {"costo_material": X, "costo_maquina": Y, "costo_total": Z}
    """
    precio_segundo = _precio_segundo_laser(daily_prices)

    mat = material_name.lower()
    if "galvanizado" in mat:
        precio_kg = float(daily_prices.get("precio_kg_galvanizado") or 0)
    elif "430" in mat:
        precio_kg = float(daily_prices.get("precio_kg_inoxidable_430") or 0)
    elif "304" in mat or "inoxidable" in mat:
        precio_kg = float(daily_prices.get("precio_kg_inoxidable_304") or 0)
    else:
        # "Chapa doble decapada" y cualquier otro acero
        precio_kg = float(daily_prices.get("precio_kg_doble_decapada") or 0)

    costo_material = (consumed_resources.get("material_kg") or 0) * precio_kg
    costo_maquina = (consumed_resources.get("machine_seconds") or 0) * precio_segundo
    costo_total = costo_material + costo_maquina

    return {
        "costo_material": round(costo_material, 2),
        "costo_maquina": round(costo_maquina, 2),
        "costo_total": round(costo_total, 2),
    }


# ---------------------------------------------------------------------------
# Presupuesto counter & persistence
# ---------------------------------------------------------------------------

def _next_presupuesto_number() -> int:
    """Return the next autoincremental presupuesto number and persist it."""
    PRESUPUESTO_COUNTER_FILE.parent.mkdir(parents=True, exist_ok=True)
    if PRESUPUESTO_COUNTER_FILE.exists():
        try:
            with PRESUPUESTO_COUNTER_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
            last = int(data.get("last", 0))
        except Exception:
            last = 0
    else:
        last = 0
    new_num = last + 1
    with PRESUPUESTO_COUNTER_FILE.open("w", encoding="utf-8") as f:
        json.dump({"last": new_num}, f)
    return new_num


def _save_presupuesto(presupuesto: dict) -> Path:
    """Save a presupuesto dict as PRES_NNNN.json and return the path."""
    PRESUPUESTOS_DIR.mkdir(parents=True, exist_ok=True)
    numero = presupuesto["numero"]
    filename = f"PRES_{numero:04d}.json"
    path = PRESUPUESTOS_DIR / filename
    with path.open("w", encoding="utf-8") as f:
        json.dump(presupuesto, f, indent=2, ensure_ascii=False)
    return path


def _auto_save_presupuesto(prev_pres_numero: str | None = None) -> str | None:
    """Auto-save/update presupuesto right after DXF generation.

    Returns the pres_numero string (e.g. "0042") or None on failure.
    Stores pres_numero in last_generate.json so the result page can link to it.
    """
    try:
        if not LAST_GENERATE_FILE.exists():
            return None
        gen = json.loads(LAST_GENERATE_FILE.read_text(encoding="utf-8"))
        lineas = gen.get("lineas", [])
        all_batches = gen.get("batches", [])
        daily_prices = gen.get("daily_prices", {})
        dxf_path_str = gen.get("dxf_path", "")
        fecha_str = gen.get("fecha", "")
        total = round(
            sum(float((ln.get("cost") or {}).get("costo_total", 0)) for ln in lineas), 2
        )

        # Check for pres_numero: _run_all_batches clears it, so prefer prev_pres_numero
        existing = prev_pres_numero or gen.get("pres_numero")
        if existing:
            pfile = PRESUPUESTOS_DIR / f"PRES_{existing}.json"
            if pfile.exists():
                pres = json.loads(pfile.read_text(encoding="utf-8"))
                pres["lineas"] = lineas
                pres["batches"] = all_batches
                pres["dxf_path"] = dxf_path_str
                pres["total"] = total
                pres["precios_aplicados"] = daily_prices
                _save_presupuesto(pres)
                pres_numero = existing
            else:
                existing = None
        if not existing:
            numero = _next_presupuesto_number()
            pres = {
                "numero": numero,
                "fecha": fecha_str,
                "customer": gen.get("customer", ""),
                "job_name": gen.get("job_name", ""),
                "cliente": "",
                "dxf_path": dxf_path_str,
                "lineas": lineas,
                "batches": all_batches,
                "total": total,
                "precios_aplicados": daily_prices,
            }
            _save_presupuesto(pres)
            pres_numero = f"{numero:04d}"

        # Persist pres_numero so render_form can build the direct link
        gen["pres_numero"] = pres_numero
        with LAST_GENERATE_FILE.open("w", encoding="utf-8") as f:
            json.dump(gen, f, indent=2, ensure_ascii=False)
        return pres_numero
    except Exception as exc:
        logger.warning("Auto-save presupuesto failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SalesRunResult:
    service_result: object
    manifest_path: Path
    output_dir: Path


# ---------------------------------------------------------------------------
# Thumbnail generation
# ---------------------------------------------------------------------------

def _render_dxf_thumbnail(file_path: str, out_path: "Path", size_px: int = 300) -> "Path | None":
    """Render a DXF file directly to PNG without going through the legacy engine.

    Reads LINE/ARC/CIRCLE/SPLINE entities directly, scales to fit, and saves.
    Returns out_path on success or None on failure.
    """
    import math as _math
    try:
        import ezdxf as _ezdxf
        import matplotlib.pyplot as _plt
    except ImportError:
        return None
    try:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                doc = _ezdxf.read(f)
        except Exception:
            with open(file_path, "r", encoding="latin-1") as f:
                doc = _ezdxf.read(f)
        msp = doc.modelspace()

        fig, ax = _plt.subplots(figsize=(size_px / 100, size_px / 100), dpi=100)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_facecolor("white")
        fig.patch.set_facecolor("white")
        color = "#1a1a2e"

        def _arc_pts(cx, cy, r, a0_deg, a1_deg):
            a0 = a0_deg % 360
            a1 = a1_deg % 360
            if a1 <= a0:
                a1 += 360
            span = a1 - a0
            n = max(6, int(span / 5))
            return [
                (cx + r * _math.cos(_math.radians(a0 + span * i / n)),
                 cy + r * _math.sin(_math.radians(a0 + span * i / n)))
                for i in range(n + 1)
            ]

        for e in msp:
            et = e.dxftype()
            try:
                if et == "LINE":
                    s, end = e.dxf.start, e.dxf.end
                    ax.plot([s.x, end.x], [s.y, end.y], color=color, linewidth=0.5)
                elif et == "ARC":
                    c = e.dxf.center
                    pts = _arc_pts(c.x, c.y, e.dxf.radius,
                                   e.dxf.start_angle, e.dxf.end_angle)
                    ax.plot([p[0] for p in pts], [p[1] for p in pts],
                            color=color, linewidth=0.5)
                elif et == "CIRCLE":
                    c = e.dxf.center
                    pts = _arc_pts(c.x, c.y, e.dxf.radius, 0, 360)
                    ax.plot([p[0] for p in pts], [p[1] for p in pts],
                            color=color, linewidth=0.5)
                elif et == "SPLINE":
                    raw = list(e.flattening(0.5))
                    if len(raw) >= 2:
                        ax.plot([p.x for p in raw], [p.y for p in raw],
                                color=color, linewidth=0.5)
            except Exception:
                pass

        ax.autoscale()
        _plt.tight_layout(pad=0)
        fig.savefig(str(out_path), dpi=100, bbox_inches="tight",
                    facecolor="white", edgecolor="none")
        _plt.close(fig)
        return out_path
    except Exception as exc:
        logger.warning("Direct DXF thumbnail failed for %s: %s", file_path, exc)
        try:
            import matplotlib.pyplot as _plt2
            _plt2.close("all")
        except Exception:
            pass
        return None


def _render_panel_thumbnail(
    file_path: str,
    step_x: float,
    step_y: float,
    out_path: "Path",
    size_px: int = 300,
) -> "Path | None":
    """Render a 300×300mm panel thumbnail using the legacy tiling motor.

    Uses cut mode (cut_partial_figures=True) with a 15mm margin so that even
    patterns whose bbox is incorrectly computed by the motor (arc bbox bug) will
    still produce a tiled result — cut mode never rejects a tile based on bbox.
    Returns out_path on success, None on failure (caller should fall back to
    _render_dxf_thumbnail).
    """
    try:
        import matplotlib.pyplot as _plt
    except ImportError:
        return None

    try:
        import math as _math
        legacy_dir = find_legacy_panel_dir()
        legacy_path = str(legacy_dir)
        prev_cwd = Path.cwd()
        inserted = legacy_path not in sys.path
        if inserted:
            sys.path.insert(0, legacy_path)
        os.chdir(legacy_dir)

        try:
            settings_module = import_module("config.settings")
            layout_module = import_module("layout.cad_result_layout")
            legacy_main = import_module("main")

            settings = settings_module.Settings()
            settings.pattern_type = "dxf"
            settings.input_file = str(file_path)
            settings.step_x = step_x
            settings.step_y = step_y
            settings.sheet_sizes = [(300.0, 300.0, 1)]
            settings.margin = 15.0
            settings.cut_partial_figures = True

            stdout_buf = StringIO()
            with redirect_stdout(stdout_buf):
                result_items = legacy_main.create_cad_result_items_from_batch(settings)
                arranged_items = layout_module.arrange_cad_result_items(result_items)

            if not result_items:
                # Motor produced nothing (e.g. DXF has only splines/unsupported entities).
                # Signal caller to fall back to _render_dxf_thumbnail.
                return None
        finally:
            os.chdir(prev_cwd)
            if inserted:
                try:
                    sys.path.remove(legacy_path)
                except ValueError:
                    pass

        fig, ax = _plt.subplots(figsize=(size_px / 100, size_px / 100), dpi=100)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_facecolor("white")
        fig.patch.set_facecolor("white")
        color = "#1a1a2e"

        def _draw(geom):
            if hasattr(geom, "points"):
                pts = list(geom.points)
                if len(pts) >= 2:
                    ax.plot([p[0] for p in pts], [p[1] for p in pts],
                            color=color, linewidth=0.5)
            elif hasattr(geom, "entities"):
                for e in geom.entities:
                    _draw(e)
            elif hasattr(geom, "cx") and hasattr(geom, "radius"):
                span = (geom.end_angle - geom.start_angle) % 360
                if span == 0 or span >= 359.9:
                    n, total = 64, 2 * _math.pi
                else:
                    rad_span = _math.radians(span)
                    n = max(8, int(rad_span / (2 * _math.pi) * 64))
                    total = rad_span
                a0 = _math.radians(geom.start_angle)
                angles = [a0 + total * i / n for i in range(n + 1)]
                ax.plot(
                    [geom.cx + _math.cos(a) * geom.radius for a in angles],
                    [geom.cy + _math.sin(a) * geom.radius for a in angles],
                    color=color, linewidth=0.5,
                )
            elif hasattr(geom, "x1") and hasattr(geom, "x2"):
                ax.plot([geom.x1, geom.x2], [geom.y1, geom.y2],
                        color=color, linewidth=0.5)

        for item in arranged_items:
            _draw(item)

        ax.autoscale()
        _plt.tight_layout(pad=0)
        fig.savefig(str(out_path), dpi=100, bbox_inches="tight",
                    facecolor="white", edgecolor="none")
        _plt.close(fig)
        return out_path

    except Exception as exc:
        logger.warning("Panel thumbnail (motor) failed for %s: %s", file_path, exc)
        try:
            import matplotlib.pyplot as _plt2
            _plt2.close("all")
        except Exception:
            pass
        return None


def generate_pattern_thumbnail(pattern_name: str, pattern_data: dict) -> "Path | None":
    """Generate a 300x300px PNG thumbnail for a library pattern.

    For DXF patterns: renders a 300×300mm tiled panel (15mm margin, cut mode)
    using the legacy motor, falling back to the raw DXF render if the motor
    fails.  For Tresbolillo: uses the legacy engine directly.
    Returns the Path of the saved PNG, or None if generation fails.
    """
    try:
        import matplotlib  # noqa: F401
        import matplotlib.pyplot as plt
    except ImportError:
        logger.warning("matplotlib not available — skipping thumbnail for %s", pattern_name)
        return None

    THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^A-Za-z0-9_\-]", "_", pattern_name)
    out_path = THUMBNAIL_DIR / f"{safe_name}.png"

    pattern_type = pattern_data.get("type", "dxf")

    if pattern_type not in ("tresbolillo",) and pattern_name.lower() != "tresbolillo":
        file_path = pattern_data.get("file_path", "")
        if not file_path or not Path(file_path).exists():
            return None
        step_x = float(pattern_data.get("step_x", 84.0))
        step_y = float(pattern_data.get("step_y", 84.0))
        result = _render_panel_thumbnail(file_path, step_x, step_y, out_path)
        if result:
            return result
        # Fallback: render DXF directly without tiling
        return _render_dxf_thumbnail(file_path, out_path)

    try:
        legacy_dir = find_legacy_panel_dir()
        legacy_path = str(legacy_dir)
        prev_cwd = Path.cwd()
        inserted = legacy_path not in sys.path
        if inserted:
            sys.path.insert(0, legacy_path)
        os.chdir(legacy_dir)

        try:
            settings_module = import_module("config.settings")
            layout_module = import_module("layout.cad_result_layout")
            legacy_main = import_module("main")

            settings = settings_module.Settings()
            settings.sheet_sizes = [(300.0, 300.0, 1)]
            settings.margin = 20.0
            settings.cut_partial_figures = True

            # Only tresbolillo reaches this point — DXF patterns return early above
            settings.pattern_type = "tresbolillo"
            settings.pattern_name = "Tresbolillo"
            settings.hole_diameter = 10.0
            settings.hole_distance = 20.0

            stdout = StringIO()
            with redirect_stdout(stdout):
                result_items = legacy_main.create_cad_result_items_from_batch(settings)
                arranged_items = layout_module.arrange_cad_result_items(result_items)
        finally:
            os.chdir(prev_cwd)
            if inserted:
                try:
                    sys.path.remove(legacy_path)
                except ValueError:
                    pass

        # Render geometry to PNG
        import math as _math
        fig, ax = plt.subplots(figsize=(3, 3), dpi=100)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_facecolor("white")
        fig.patch.set_facecolor("white")

        color = "#1a1a2e"

        def _draw(geom):
            if hasattr(geom, "points"):
                # Polyline
                pts = list(geom.points)
                if len(pts) >= 2:
                    ax.plot([p[0] for p in pts], [p[1] for p in pts],
                            color=color, linewidth=0.5)
            elif hasattr(geom, "entities"):
                # Piece — recurse
                for e in geom.entities:
                    _draw(e)
            elif hasattr(geom, "cx") and hasattr(geom, "radius"):
                # ArcSegment
                span = (geom.end_angle - geom.start_angle) % 360
                a0 = _math.radians(geom.start_angle)
                if span == 0 or span >= 359.9:
                    n, total = 64, 2 * _math.pi
                else:
                    rad_span = _math.radians(span)
                    n = max(8, int(rad_span / (2 * _math.pi) * 64))
                    total = rad_span
                angles = [a0 + total * i / n for i in range(n + 1)]
                ax.plot(
                    [geom.cx + _math.cos(a) * geom.radius for a in angles],
                    [geom.cy + _math.sin(a) * geom.radius for a in angles],
                    color=color, linewidth=0.5,
                )
            elif hasattr(geom, "x1") and hasattr(geom, "x2"):
                # LineSegment
                ax.plot([geom.x1, geom.x2], [geom.y1, geom.y2],
                        color=color, linewidth=0.5)

        # arranged_items is flat: [TextLabel, Piece/Polyline, ..., TextLabel, ...]
        for item in arranged_items:
            _draw(item)

        ax.autoscale()
        plt.tight_layout(pad=0)
        fig.savefig(str(out_path), dpi=100, bbox_inches="tight",
                    facecolor="white", edgecolor="none")
        plt.close(fig)
        return out_path

    except Exception as exc:
        logger.warning("Thumbnail generation failed for %s: %s", pattern_name, exc)
        try:
            import matplotlib.pyplot as plt
            plt.close("all")
        except Exception:
            pass
        return None


def _thumbnail_url(pattern_name: str) -> "str | None":
    """Return the URL path for a pattern thumbnail, or None if not generated."""
    safe_name = re.sub(r"[^A-Za-z0-9_\-]", "_", pattern_name)
    path = THUMBNAIL_DIR / f"{safe_name}.png"
    if path.exists():
        return f"/static/pattern_thumbnails/{safe_name}.png"
    return None


def _ensure_all_thumbnails() -> None:
    """On server start: generate thumbnails for any pattern that lacks one."""
    try:
        patterns = get_pattern_library_patterns()
    except Exception:
        return
    for name, data in patterns.items():
        safe_name = re.sub(r"[^A-Za-z0-9_\-]", "_", name)
        path = THUMBNAIL_DIR / f"{safe_name}.png"
        if not path.exists():
            generate_pattern_thumbnail(name, data)
    # Also ensure Tresbolillo thumbnail exists
    tres_path = THUMBNAIL_DIR / "Tresbolillo.png"
    if not tres_path.exists():
        generate_pattern_thumbnail("Tresbolillo", {"type": "tresbolillo"})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _first(form: dict[str, list[str]], key: str, default: str = "") -> str:
    values = form.get(key)
    if not values:
        return default
    return values[0].strip()


def _positive_float(value: str, field_label: str) -> float:
    try:
        parsed = float(value.replace(",", "."))
    except ValueError as exc:
        raise ValueError(f"{field_label} debe ser un numero") from exc
    if parsed <= 0:
        raise ValueError(f"{field_label} debe ser mayor a cero")
    return parsed


def _nonneg_float(value: str, field_label: str) -> float:
    try:
        parsed = float(value.replace(",", "."))
    except ValueError as exc:
        raise ValueError(f"{field_label} debe ser un numero") from exc
    if parsed < 0:
        raise ValueError(f"{field_label} no puede ser negativo")
    return parsed


def _positive_int(value: str, field_label: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{field_label} debe ser un numero entero") from exc
    if parsed <= 0:
        raise ValueError(f"{field_label} debe ser mayor a cero")
    return parsed


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", value.strip()).strip("-")
    return cleaned.upper() or "PANEL"


def _parse_sheet_sizes(text: str) -> list[tuple[float, float, int]]:
    """Parse lines like '2 de 1000x1500' or '300x200' into (w, h, qty) tuples."""
    result = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        # Try "N de WxH"
        m = re.match(r"^(\d+)\s+de\s+(\d+(?:[.,]\d+)?)\s*[xX]\s*(\d+(?:[.,]\d+)?)$", line)
        if m:
            qty = int(m.group(1))
            w = float(m.group(2).replace(",", "."))
            h = float(m.group(3).replace(",", "."))
            result.append((w, h, qty))
            continue
        # Try "WxH" (qty=1)
        m = re.match(r"^(\d+(?:[.,]\d+)?)\s*[xX]\s*(\d+(?:[.,]\d+)?)$", line)
        if m:
            w = float(m.group(1).replace(",", "."))
            h = float(m.group(2).replace(",", "."))
            result.append((w, h, 1))
            continue
        raise ValueError(
            f"Formato de pieza invalido: '{line}'. Usar '2 de 300x200' o '300x200'."
        )
    if not result:
        raise ValueError("Lista de piezas vacia. Ingresar al menos una pieza.")
    return result


def _panel_mode_to_preset_code(panel_mode: str) -> str:
    if panel_mode == "dxf_pattern_grid":
        return "PANEL_DECORATIVO_LEGACY_DXF_PATTERN"
    if panel_mode == "none":
        return "PANEL_DECORATIVO_LEGACY_SIN_PERFORAR"
    if panel_mode == "cuadriculado":
        return "PANEL_DECORATIVO_LEGACY_CUADRICULADO"
    return "PANEL_DECORATIVO_LEGACY_TRESBOLILLO"


# ---------------------------------------------------------------------------
# Build input from form (single batch + header) — used for tests
# ---------------------------------------------------------------------------

def build_sales_input(form: dict[str, list[str]]) -> LegacyPanelServiceInput:
    """Build a LegacyPanelServiceInput from a flat HTML form dict (legacy single-batch path)."""
    customer = _first(form, "customer_reference", "CLIENTE-DEMO")
    job_name = _first(form, "job_name", "Panel decorativo")
    panel_mode = _first(form, "panel_mode", "tresbolillo")
    if panel_mode not in ("tresbolillo", "dxf_pattern_grid", "none", "cuadriculado"):
        panel_mode = "tresbolillo"

    material = _first(form, "material", "chapa")
    thickness_mm = _positive_float(_first(form, "thickness_mm", "3"), "Espesor")
    margin_mm = _nonneg_float(_first(form, "margin_mm", "20"), "Margen")
    observations = _first(form, "observations", "")
    order_id = f"VENTA-{_slug(customer)}-{_slug(job_name)}"

    cut_partial_raw = _first(form, "cut_partial_figures", "true")
    cut_partial_figures = cut_partial_raw.lower() not in ("false", "0", "no", "centrado")

    # Piece list parsing
    pieces_raw = _first(form, "sheet_sizes_text", "")
    if pieces_raw:
        sheet_sizes = _parse_sheet_sizes(pieces_raw)
    else:
        width_mm = _positive_float(_first(form, "width_mm", "300"), "Ancho")
        height_mm = _positive_float(_first(form, "height_mm", "200"), "Alto")
        quantity = _positive_int(_first(form, "quantity", "1"), "Cantidad")
        sheet_sizes = [(width_mm, height_mm, quantity)]

    first_w, first_h, first_qty = sheet_sizes[0]

    offset_x_mm = None
    offset_y_mm = None

    if panel_mode == "dxf_pattern_grid":
        path_value = (
            _first(form, "dxf_pattern_file_path")
            or _first(form, "dxf_pattern_path")
            or _first(form, "pattern_dxf_path")
        )
        if not path_value:
            raise ValueError("Archivo DXF patron requerido para Patron DXF repetido")
        pattern_path = Path(path_value)
        step_x_mm = _positive_float(_first(form, "offset_x_mm", _first(form, "step_x_mm", "84")), "Offset X")
        step_y_mm = _positive_float(_first(form, "offset_y_mm", _first(form, "step_y_mm", "84")), "Offset Y")
        preset_name = _first(form, "preset_name", "Patron DXF repetido")
        pattern_type = "dxf"
        hole_diameter_mm = 0.0
        hole_distance_mm = 0.0
    elif panel_mode == "none":
        pattern_path = None
        step_x_mm = None
        step_y_mm = None
        preset_name = _first(form, "preset_name", "Sin perforar")
        pattern_type = "none"
        hole_diameter_mm = 0.0
        hole_distance_mm = 0.0
    elif panel_mode == "cuadriculado":
        pattern_path = None
        hole_diameter_mm = 0.0
        hole_distance_mm = 0.0
        preset_name = _first(form, "preset_name", "Cuadriculado")
        pattern_type = "cuadriculado"
        offset_x_mm = _positive_float(_first(form, "offset_x_mm", _first(form, "step_x_mm", "30")), "Offset X")
        offset_y_mm = _positive_float(_first(form, "offset_y_mm", _first(form, "step_y_mm", "30")), "Offset Y")
        step_x_mm = None
        step_y_mm = None
    else:
        pattern_path = None
        step_x_mm = None
        step_y_mm = None
        preset_name = _first(form, "preset_name", "Tresbolillo circular")
        pattern_type = "tresbolillo"
        hole_diameter_mm = _positive_float(_first(form, "hole_diameter_mm", "20"), "Diametro")
        hole_distance_mm = _positive_float(_first(form, "hole_distance_mm", "60"), "Distancia")

    return LegacyPanelServiceInput(
        panel_mode=panel_mode,
        preset_code=_panel_mode_to_preset_code(panel_mode),
        preset_name=preset_name,
        material=material,
        thickness_mm=thickness_mm,
        width_mm=first_w,
        height_mm=first_h,
        quantity=first_qty,
        customer_code=customer,
        order_id=order_id,
        job_name=job_name,
        observations=observations,
        pattern_type=pattern_type,
        cut_partial_figures=cut_partial_figures,
        margin_mm=margin_mm,
        hole_diameter_mm=hole_diameter_mm,
        hole_distance_mm=hole_distance_mm,
        offset_x_mm=offset_x_mm,
        offset_y_mm=offset_y_mm,
        pattern_dxf_path=pattern_path,
        step_x_mm=step_x_mm,
        step_y_mm=step_y_mm,
        sheet_sizes=list(sheet_sizes) if len(sheet_sizes) > 1 else None,
    )


# ---------------------------------------------------------------------------
# Run flow (single service input) -- used by tests
# ---------------------------------------------------------------------------

def run_sales_flow(
    data: LegacyPanelServiceInput,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    price_file: Path = DEFAULT_PRICE_FILE,
) -> SalesRunResult:
    price_cache = PriceCache.load(price_file) if price_file.exists() else None
    service = LegacyPanelService(price_cache=price_cache)
    result = service.run(data, output_dir)
    manifest_path = write_panel_service_outputs(result, output_dir)
    return SalesRunResult(result, manifest_path, output_dir)


# ---------------------------------------------------------------------------
# Multi-batch run
# ---------------------------------------------------------------------------

def _run_all_batches(
    batches: list[dict],
    customer: str,
    job_name: str,
    observations: str,
    output_dir: Path,
    price_file: Path,
) -> SalesRunResult:
    """Run all batches through the engine and produce a single merged DXF output."""
    all_batches = batches

    price_cache = PriceCache.load(price_file) if price_file.exists() else None
    order_id = f"VENTA-{_slug(customer)}-{_slug(job_name)}"

    legacy_dir = find_legacy_panel_dir()
    legacy_path = str(legacy_dir)
    prev_cwd = Path.cwd()
    inserted = legacy_path not in sys.path
    if inserted:
        sys.path.insert(0, legacy_path)
    os.chdir(legacy_dir)

    try:
        legacy_main = import_module("main")
        settings_module = import_module("config.settings")
        layout_module = import_module("layout.cad_result_layout")
        exporter_module = import_module("dxf.mixed_exporter")

        all_result_items = []
        # cuad+square batches are handled separately (LWPOLYLINE + zone groups).
        # Each entry: {"batch": ..., "geo": {pierce_count, cut_length_mm, ...}}
        cuad_sq_batches_geo: list[dict] = []
        # tresbolillo+hexágono: el motor standalone no tiene hexágono → se difiere
        # al generador del adapter (_write_tresbolillo_hex_to_doc), igual que cuad+square.
        hex_batches_geo: list[dict] = []

        for batch in all_batches:
            settings = settings_module.Settings()
            panel_mode = batch["panel_mode"]
            hole_shape = batch.get("hole_shape", "circle")

            settings.pattern_name = batch["preset_name"]
            settings.material = batch["material"]
            settings.thickness = float(batch["thickness_mm"])
            settings.margin = float(batch["margin_mm"])
            settings.cut_partial_figures = bool(batch["cut_partial_figures"])
            settings.sheet_sizes = [
                (float(w), float(h), int(q))
                for w, h, q in batch["sheet_sizes"]
            ]

            if panel_mode == "cuadriculado" and hole_shape == "square":
                # Defer to post-legacy DXF step — record batch, skip legacy engine
                cuad_sq_batches_geo.append({"batch": batch, "geo": None})
                continue

            if panel_mode == "tresbolillo" and hole_shape == "hexagon":
                # El standalone no tiene hexágono → diferir al generador del adapter
                hex_batches_geo.append({"batch": batch, "geo": None})
                continue

            if panel_mode == "none":
                max_dim = max(
                    max(w for w, h, _ in settings.sheet_sizes),
                    max(h for w, h, _ in settings.sheet_sizes),
                )
                settings.pattern_type = "tresbolillo"
                settings.cut_partial_figures = False
                settings.hole_diameter = max_dim * 2
                settings.hole_distance = max_dim * 4
            elif panel_mode == "tresbolillo":
                settings.pattern_type = "tresbolillo"
                settings.hole_diameter = float(batch["hole_diameter_mm"])
                settings.hole_distance = float(batch["hole_distance_mm"])
            elif panel_mode == "cuadriculado":
                # cuadriculado + circle (square already handled above)
                settings.pattern_type = "cuadriculado"
                settings.hole_shape = hole_shape
                settings.hole_size = float(batch.get("hole_size_mm", 20))
                settings.step_x = float(batch["offset_x_mm"])
                settings.step_y = float(batch["offset_y_mm"])
            else:  # dxf_pattern_grid
                settings.pattern_type = "dxf"
                settings.input_file = batch["pattern_dxf_path"]
                settings.step_x = float(batch["step_x_mm"])
                settings.step_y = float(batch["step_y_mm"])

            stdout = StringIO()
            with redirect_stdout(stdout):
                batch_items = legacy_main.create_cad_result_items_from_batch(settings)
            all_result_items.extend(batch_items)

        # Sort by thickness ASC, then quantity DESC before layout so the DXF
        # groups panels in a predictable order regardless of submission sequence.
        all_result_items.sort(key=lambda it: (it.thickness, -it.quantity))
        output_dir.mkdir(parents=True, exist_ok=True)
        dxf_path = output_dir / f"{order_id}_legacy_panel.dxf"
        dxf_path.unlink(missing_ok=True)

        if all_result_items:
            arranged = layout_module.arrange_cad_result_items(all_result_items)
            exporter_module.MixedDXFExporter().save(arranged, str(dxf_path))

        # Append cuadriculado+square panels into the combined DXF.
        # All batches (legacy + cuad+square + tresbolillo hex) end up in the same .dxf.
        if cuad_sq_batches_geo or hex_batches_geo:
            import ezdxf as _ezdxf
            if dxf_path.exists():
                combined_doc = _ezdxf.readfile(str(dxf_path))
            else:
                combined_doc = _ezdxf.new("R2010")
            combined_msp = combined_doc.modelspace()

            # Place deferred panels to the right of any legacy content
            next_x = sum(float(it.occupied_width) + 200.0 for it in all_result_items)
            for entry in cuad_sq_batches_geo:
                b = entry["batch"]
                sw, sh, _sq = [(float(w), float(h), int(q)) for w, h, q in b["sheet_sizes"]][0]
                geo = _write_cuadriculado_square_to_doc(
                    combined_doc, combined_msp,
                    hole_size_mm=float(b.get("hole_size_mm", 20)),
                    step_x_mm=float(b["offset_x_mm"]),
                    step_y_mm=float(b["offset_y_mm"]),
                    sheet_width_mm=sw,
                    sheet_height_mm=sh,
                    margin_mm=float(b["margin_mm"]),
                    offset_x=next_x,
                    offset_y=0.0,
                )
                entry["geo"] = geo
                next_x += sw + 200.0

            for entry in hex_batches_geo:
                b = entry["batch"]
                sw, sh, _sq = [(float(w), float(h), int(q)) for w, h, q in b["sheet_sizes"]][0]
                geo = _write_tresbolillo_hex_to_doc(
                    combined_doc, combined_msp,
                    hole_diameter_mm=float(b["hole_diameter_mm"]),
                    hole_distance_mm=float(b["hole_distance_mm"]),
                    sheet_width_mm=sw,
                    sheet_height_mm=sh,
                    margin_mm=float(b["margin_mm"]),
                    offset_x=next_x,
                    offset_y=0.0,
                )
                entry["geo"] = geo
                next_x += sw + 200.0

            combined_doc.saveas(str(dxf_path))

    finally:
        os.chdir(prev_cwd)
        if inserted:
            try:
                sys.path.remove(legacy_path)
            except ValueError:
                pass

    first_batch = all_batches[0]
    first_sizes = first_batch["sheet_sizes"]
    first_w = float(first_sizes[0][0])
    first_h = float(first_sizes[0][1])
    first_qty = int(first_sizes[0][2])

    first_input = LegacyPanelServiceInput(
        panel_mode=first_batch["panel_mode"],
        preset_code=_panel_mode_to_preset_code(first_batch["panel_mode"]),
        preset_name=first_batch["preset_name"],
        material=first_batch["material"],
        thickness_mm=float(first_batch["thickness_mm"]),
        width_mm=first_w,
        height_mm=first_h,
        quantity=first_qty,
        customer_code=customer,
        order_id=order_id,
        job_name=job_name,
        observations=observations,
        pattern_type=first_batch["pattern_type"],
        cut_partial_figures=bool(first_batch["cut_partial_figures"]),
        margin_mm=float(first_batch["margin_mm"]),
    )

    # Per-item material lookup so multi-material/multi-thickness orders are
    # calculated correctly (previously only the first batch's material was used).
    _mat_table = MaterialTable()
    _mat_lookup: dict = {
        (e["material"], float(e["espesor_mm"])): e
        for e in _mat_table.list()
    }

    # Load daily prices once; all items (old + new) are costed at today's rates.
    _daily_prices, _prices_missing = _load_daily_prices()

    all_resources = []
    _any_missing_material = False
    for item in all_result_items:
        _item_mat_entry = _mat_lookup.get((item.material, item.thickness))
        if _item_mat_entry is None:
            _any_missing_material = True
        cut_length_mm = calculate_cut_length_mm(item.geometry_items)
        pierce_count = calculate_pierce_count(item.geometry_items)
        sheet_area_m2 = calculate_sheet_area_m2(item.occupied_width, item.occupied_height)
        if _item_mat_entry is not None:
            consumed = calculate_consumed_resources(
                cut_length_m=cut_length_mm / 1000.0,
                pierce_count=pierce_count,
                sheet_area_m2=sheet_area_m2,
                material_entry=_item_mat_entry,
            )
        else:
            consumed = None

        # Calculate cost (always included; values are 0 when prices missing)
        cost_entry: dict
        if consumed is not None:
            cost_entry = calculate_cost(consumed, item.material, _daily_prices)
        else:
            cost_entry = {"costo_material": 0.0, "costo_maquina": 0.0, "costo_total": 0.0}
        if _prices_missing:
            cost_entry["prices_missing"] = True

        all_resources.append(
            {
                "name": item.name,
                "material": item.material,
                "thickness_mm": item.thickness,
                "quantity": item.quantity,
                "occupied_width_mm": item.occupied_width,
                "occupied_height_mm": item.occupied_height,
                "geometry_item_count": len(item.geometry_items),
                "cut_length_mm": cut_length_mm,
                # travel aún no se computa para patrones genéricos (solo grilla
                # cuadriculada). Se expone en 0.0 para el término crudo de calibración.
                "travel_length_mm": 0.0,
                "pierce_count": pierce_count,
                "bend_count": item.bend_count,
                "consumed_resources": consumed,
                "consumed_resources_warning": (
                    None if _item_mat_entry is not None else (
                        f"Material '{item.material}' {item.thickness} mm "
                        f"no está en la tabla de materiales."
                    )
                ),
                "cost": cost_entry,
            }
        )

    # Add resource entries for cuadriculado+square batches (bypassed the legacy engine).
    for entry in cuad_sq_batches_geo:
        b = entry["batch"]
        geo = entry["geo"] or {}
        sw, sh, sq = [(float(w), float(h), int(q)) for w, h, q in b["sheet_sizes"]][0]
        _item_mat_entry = _mat_lookup.get((b["material"], float(b["thickness_mm"])))
        if _item_mat_entry is None:
            _any_missing_material = True
        c_len = geo.get("cut_length_mm", 0.0)
        p_cnt = geo.get("pierce_count", 0)
        sheet_area_m2 = calculate_sheet_area_m2(sw, sh)
        if _item_mat_entry is not None:
            consumed = calculate_consumed_resources(
                cut_length_m=c_len / 1000.0,
                pierce_count=p_cnt,
                sheet_area_m2=sheet_area_m2,
                material_entry=_item_mat_entry,
                travel_length_mm=geo.get("travel_length_mm", 0.0),
            )
        else:
            consumed = None
        if consumed is not None:
            cost_entry = calculate_cost(consumed, b["material"], _daily_prices)
        else:
            cost_entry = {"costo_material": 0.0, "costo_maquina": 0.0, "costo_total": 0.0}
        if _prices_missing:
            cost_entry["prices_missing"] = True
        all_resources.append(
            {
                "name": b["preset_name"],
                "material": b["material"],
                "thickness_mm": float(b["thickness_mm"]),
                "quantity": sq,
                "occupied_width_mm": sw,
                "occupied_height_mm": sh,
                "geometry_item_count": p_cnt,
                "cut_length_mm": c_len,
                "travel_length_mm": geo.get("travel_length_mm", 0.0),
                "pierce_count": p_cnt,
                "bend_count": 0,
                "consumed_resources": consumed,
                "consumed_resources_warning": (
                    None if _item_mat_entry is not None else (
                        f"Material '{b['material']}' {b['thickness_mm']} mm "
                        f"no está en la tabla de materiales."
                    )
                ),
                "cost": cost_entry,
            }
        )

    # Add resource entries for tresbolillo+hexágono batches (bypassed the legacy engine).
    for entry in hex_batches_geo:
        b = entry["batch"]
        geo = entry["geo"] or {}
        sw, sh, sq = [(float(w), float(h), int(q)) for w, h, q in b["sheet_sizes"]][0]
        _item_mat_entry = _mat_lookup.get((b["material"], float(b["thickness_mm"])))
        if _item_mat_entry is None:
            _any_missing_material = True
        c_len = geo.get("cut_length_mm", 0.0)
        p_cnt = geo.get("pierce_count", 0)
        sheet_area_m2 = calculate_sheet_area_m2(sw, sh)
        if _item_mat_entry is not None:
            consumed = calculate_consumed_resources(
                cut_length_m=c_len / 1000.0,
                pierce_count=p_cnt,
                sheet_area_m2=sheet_area_m2,
                material_entry=_item_mat_entry,
                travel_length_mm=geo.get("travel_length_mm", 0.0),
            )
        else:
            consumed = None
        if consumed is not None:
            cost_entry = calculate_cost(consumed, b["material"], _daily_prices)
        else:
            cost_entry = {"costo_material": 0.0, "costo_maquina": 0.0, "costo_total": 0.0}
        if _prices_missing:
            cost_entry["prices_missing"] = True
        all_resources.append(
            {
                "name": b["preset_name"],
                "material": b["material"],
                "thickness_mm": float(b["thickness_mm"]),
                "quantity": sq,
                "occupied_width_mm": sw,
                "occupied_height_mm": sh,
                "geometry_item_count": p_cnt,
                "cut_length_mm": c_len,
                "travel_length_mm": geo.get("travel_length_mm", 0.0),
                "pierce_count": p_cnt,
                "bend_count": 0,
                "consumed_resources": consumed,
                "consumed_resources_warning": (
                    None if _item_mat_entry is not None else (
                        f"Material '{b['material']}' {b['thickness_mm']} mm "
                        f"no está en la tabla de materiales."
                    )
                ),
                "cost": cost_entry,
            }
        )

    warnings: list[str] = []
    if any(r["cut_length_mm"] == 0 for r in all_resources):
        warnings.append("Legacy engine returned cut_length_mm=0; preserving legacy value.")
    if any(r["pierce_count"] == 0 for r in all_resources):
        if any(r.get("geometry_item_count", 0) <= 1 for r in all_resources):
            warnings.append(
                "El panel generado no contiene perforaciones — el DXF es solo el rectángulo de la chapa. "
                "Verificá que el paso del patrón (offset X/Y) entre en las dimensiones efectivas de la chapa, "
                "o cambiá la distribución a 'Cortar figuras en borde'."
            )
        else:
            warnings.append("Legacy engine returned pierce_count=0; preserving legacy value.")
    if _any_missing_material:
        warnings.append(
            "Uno o más paneles no tienen entrada en la tabla de materiales — "
            "agregar las entradas en /admin para obtener recursos consumidos."
        )

    cut_piece_payload = _build_cut_piece_payload(first_input, dxf_path)
    quotation_payload = _build_quotation_payload(first_input, all_resources, price_cache)

    service_result = LegacyPanelServiceResult(
        panel_mode=first_input.panel_mode,
        preset_code=first_input.preset_code,
        preset_name=first_input.preset_name,
        material=first_input.material,
        thickness_mm=first_input.thickness_mm,
        width_mm=first_input.width_mm,
        height_mm=first_input.height_mm,
        quantity=first_input.quantity,
        calculated_resources=all_resources,
        dxf_path=dxf_path,
        warnings=warnings,
        legacy_result_raw={"batches": len(all_batches), "total_items": len(all_result_items)},
        cut_piece_payload=cut_piece_payload,
        quotation_payload=quotation_payload,
    )

    manifest_path = write_panel_service_outputs(service_result, output_dir)

    # Persist last generate data so /presupuesto can read it.
    # Store all_batches so a future reactivation can regenerate from scratch.
    try:
        import datetime as _dt
        _lineas = [
            {
                "patron": r.get("name", ""),
                "material": r.get("material", ""),
                "espesor_mm": r.get("thickness_mm", 0),
                "cantidad": r.get("quantity", 1),
                "consumed_resources": r.get("consumed_resources"),
                "cost": r.get("cost", {}),
            }
            for r in all_resources
        ]
        _last_gen = {
            "fecha": _dt.date.today().isoformat(),
            "customer": customer,
            "job_name": job_name,
            "dxf_path": str(dxf_path),
            "daily_prices": _daily_prices,
            "prices_missing": _prices_missing,
            "batches": all_batches,
            "lineas": _lineas,
        }
        LAST_GENERATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LAST_GENERATE_FILE.open("w", encoding="utf-8") as _f:
            json.dump(_last_gen, _f, indent=2, ensure_ascii=False)
    except Exception as _exc:
        logger.warning("No se pudo guardar last_generate.json: %s", _exc)

    return SalesRunResult(service_result, manifest_path, output_dir)


# ---------------------------------------------------------------------------
# HTTP multipart/form parsing
# ---------------------------------------------------------------------------

def _parse_multipart_form(handler: BaseHTTPRequestHandler) -> dict[str, list[str]]:
    form: dict[str, list[str]] = {}
    length = int(handler.headers.get("Content-Length", "0"))
    body = handler.rfile.read(length)
    content_type = handler.headers.get("Content-Type", "")
    message = BytesParser(policy=email_policy).parsebytes(
        b"Content-Type: " + content_type.encode("ascii") + b"\r\nMIME-Version: 1.0\r\n\r\n" + body
    )
    upload_dir = handler.output_dir / "uploaded_patterns"
    for part in message.iter_parts():
        key = part.get_param("name", header="content-disposition")
        if not key:
            continue
        filename = part.get_filename()
        payload = part.get_payload(decode=True) or b""
        if filename:
            if not payload:
                continue
            filename = Path(filename).name
            if not filename.lower().endswith(".dxf"):
                raise ValueError("El archivo DXF patron debe tener extension .dxf")
            upload_dir.mkdir(parents=True, exist_ok=True)
            upload_path = upload_dir / filename
            upload_path.write_bytes(payload)
            form.setdefault("dxf_pattern_file_path", []).append(str(upload_path))
        else:
            charset = part.get_content_charset() or "utf-8"
            form.setdefault(key, []).append(payload.decode(charset, errors="replace").strip())
    return form


def _parse_post_form(handler: BaseHTTPRequestHandler) -> dict[str, list[str]]:
    content_type = handler.headers.get("Content-Type", "")
    if content_type.startswith("multipart/form-data"):
        return _parse_multipart_form(handler)
    length = int(handler.headers.get("Content-Length", "0"))
    body = handler.rfile.read(length).decode("utf-8")
    return parse_qs(body)


def _parse_formdata_raw(handler: BaseHTTPRequestHandler) -> dict[str, list[str]]:
    """Parse form data without file upload handling (for API endpoints)."""
    content_type = handler.headers.get("Content-Type", "")
    length = int(handler.headers.get("Content-Length", "0"))
    if content_type.startswith("multipart/form-data"):
        body = handler.rfile.read(length)
        message = BytesParser(policy=email_policy).parsebytes(
            b"Content-Type: " + content_type.encode("ascii") + b"\r\nMIME-Version: 1.0\r\n\r\n" + body
        )
        form: dict[str, list[str]] = {}
        for part in message.iter_parts():
            key = part.get_param("name", header="content-disposition")
            if not key:
                continue
            payload = part.get_payload(decode=True) or b""
            charset = part.get_content_charset() or "utf-8"
            form.setdefault(key, []).append(payload.decode(charset, errors="replace").strip())
        return form
    body = handler.rfile.read(length).decode("utf-8")
    return parse_qs(body)


# ---------------------------------------------------------------------------
# CSS and navbar snippets shared between pages
# ---------------------------------------------------------------------------

_COMMON_CSS = """
  :root {
    --brand:#176b87; --brand-dark:#125a72; --green:#2e7d32;
    --bg:#f0f2f5; --card:#fff; --line:#e0e6ed;
    --ink:#1a1a2e; --muted:#607080; --accent2:#8a4b20;
    --red:#c62828;
  }
  *, *::before, *::after { box-sizing:border-box; margin:0; padding:0; }
  body { font-family:'Segoe UI',Arial,sans-serif; background:var(--bg); color:var(--ink); font-size:14px; }
  .topbar { background:var(--brand); color:#fff; display:flex; align-items:center; padding:0 24px; height:52px; gap:32px; box-shadow:0 2px 6px rgba(0,0,0,.25); }
  .topbar .logo { font-size:17px; font-weight:700; letter-spacing:.5px; white-space:nowrap; }
  .topbar nav { display:flex; gap:4px; }
  .topbar nav a { color:rgba(255,255,255,.75); text-decoration:none; padding:6px 14px; border-radius:4px; font-size:13px; font-weight:500; transition:background .15s; }
  .topbar nav a:hover { background:rgba(255,255,255,.15); color:#fff; }
  .topbar nav a.active { background:rgba(255,255,255,.22); color:#fff; }
  .topbar .spacer { flex:1; }
  .topbar .admin-link { font-size:12px; color:rgba(255,255,255,.65); text-decoration:none; border:1px solid rgba(255,255,255,.3); padding:4px 12px; border-radius:4px; }
  .topbar .admin-link:hover { background:rgba(255,255,255,.1); color:#fff; }
  .topbar .back-link { font-size:12px; color:rgba(255,255,255,.75); text-decoration:none; padding:4px 12px; border-radius:4px; border:1px solid rgba(255,255,255,.3); }
  .topbar .back-link:hover { background:rgba(255,255,255,.1); color:#fff; }
  .admin-badge { background:rgba(255,255,255,.15); border:1px solid rgba(255,255,255,.3); color:rgba(255,255,255,.9); font-size:11px; font-weight:700; letter-spacing:1px; text-transform:uppercase; padding:3px 10px; border-radius:12px; text-decoration:none; cursor:pointer; }
  .admin-badge:hover { background:rgba(255,255,255,.28); }
  .topbar .admin-link.active { background:rgba(255,255,255,.12); color:#fff; border-color:rgba(255,255,255,.55); }
  .page-wrapper { max-width:1100px; margin:0 auto; padding:28px 20px 60px; }
  .card { background:var(--card); border-radius:8px; box-shadow:0 2px 10px rgba(0,0,0,.08); padding:28px 32px; margin-bottom:24px; }
  .card-title { font-size:11px; font-weight:700; letter-spacing:1.2px; text-transform:uppercase; color:var(--brand); margin-bottom:20px; border-bottom:2px solid #e8f4f8; padding-bottom:10px; }
  label { font-size:11px; font-weight:700; letter-spacing:.8px; text-transform:uppercase; color:#555; margin-bottom:5px; display:block; }
  input[type=text], input[type=number], select, textarea { border:1px solid #ccc; border-radius:5px; padding:8px 10px; font-size:14px; color:#222; background:#fff; transition:border-color .15s; width:100%; font-family:inherit; }
  input[type=text]:focus, input[type=number]:focus, select:focus, textarea:focus { outline:none; border-color:var(--brand); box-shadow:0 0 0 2px rgba(23,107,135,.15); }
  input[readonly] { background:#f3f5f7; color:#555; }
  .field-hint { font-size:11px; color:#888; margin-top:3px; }
  .form-row { display:flex; gap:16px; margin-bottom:16px; }
  .form-group { display:flex; flex-direction:column; flex:1; }
  .hidden { display:none !important; }
  .error-box { background:#fdecea; border:1px solid #f5a5a0; color:var(--red); padding:12px; border-radius:6px; margin-bottom:14px; font-size:14px; }

  .dimmed { color:#aaa; font-size:12px; font-style:italic; }
  @media (max-width:700px) { .form-row { flex-direction:column; } }
  @media (max-width:600px) {
    .topbar { padding:0 12px; gap:4px; overflow-x:auto; overflow-y:hidden; -webkit-overflow-scrolling:touch; }
    .topbar > * { flex-shrink:0; }
    .topbar .spacer { display:none; }
    .topbar nav a, .topbar .admin-link, .topbar .back-link { white-space:nowrap; font-size:12px; padding:6px 10px; }
    .topbar .logo { font-size:14px; margin-right:4px; }
    .topbar .admin-link-secondary { display:none; }
    .page-wrapper { padding-left:0; padding-right:0; }
    .card { padding:16px 14px; border-radius:0; }
  }
"""

def _topbar_html(active: str = "") -> str:
    """Unified topbar for all pages.

    active: 'landing' | 'paneles' | 'perfiles_plegados' | 'plegados_complejos' |
            'admin' | 'materiales' | 'precios' | 'presupuesto' | 'presupuestos'
    """
    is_landing = active == "landing"
    badge_cls = "admin-badge" + (" active" if active == "admin" else "")

    def _alink(href: str, label: str, page: str) -> str:
        extra = " active" if page == active else ""
        return f'<a href="{href}" class="admin-link{extra}">{label}</a>'

    def _navlink(href: str, label: str, page: str) -> str:
        cls = ' class="active"' if page == active else ""
        return f'<a href="{href}"{cls}>{label}</a>'

    back_html = '' if is_landing else '\n  <a href="/" class="back-link" style="order:-1;margin-right:0">← Inicio</a>'
    nav_html = (
        f'\n  <nav>'
        f'{_navlink("/paneles", "Paneles Decorativos", "paneles")}'
        f'  {_navlink("/plegados/perfiles", "Perfiles Plegados", "perfiles_plegados")}'
        f'  {_navlink("/plegados/complejos", "Plegados Complejos", "plegados_complejos")}'
        f'</nav>'
    ) if not is_landing else ''

    return (
        '\n<header class="topbar">'
        + back_html
        + '\n  <a href="/" class="logo" style="color:inherit;text-decoration:none">SistemaIndustrial</a>'
        + nav_html
        + '\n  <div class="spacer"></div>'
        + f'\n  {_alink("/presupuestos", "Presupuestos", "presupuestos")}'
        + f'\n  <a href="/admin" class="{badge_cls}">ADMIN</a>'
        + f'\n  <a href="/materiales" class="admin-link admin-link-secondary{"  active" if active == "materiales" else ""}">Tabla de materiales</a>'
        + f'\n  <a href="/precios" class="admin-link admin-link-secondary{"  active" if active == "precios" else ""}">Precios diarios</a>'
        + '\n</header>\n'
    )


def _format_number_locale(value: float, decimals: int = 2) -> str:
    """Format a number using the OS regional separators so it pastes correctly into Excel.

    Reads the system locale once per call (fast on all modern OSes).
    Falls back to en-US style if locale is unavailable.
    """
    import locale as _lc
    try:
        _lc.setlocale(_lc.LC_ALL, "")
    except Exception:
        pass
    conv = _lc.localeconv()
    dec = conv.get("decimal_point") or "."
    thou = conv.get("thousands_sep") or ","
    # Build with en-US format, then swap separators
    formatted = f"{value:,.{decimals}f}"          # e.g. "56,463.03"
    if dec != "." or thou not in (",", "."):
        formatted = formatted.replace(".", "\x00")  # tmp placeholder for decimal
        formatted = formatted.replace(",", thou)
        formatted = formatted.replace("\x00", dec)
    return formatted


def _clean_pattern_name(name: str) -> str:
    """Strip engine-added suffixes from pattern name.

    Removes trailing dimension suffix (e.g. '600.0x600.0') and
    parenthetical tags (e.g. '(convertido)') added by the legacy motor.
    """
    import re as _re
    name = _re.sub(r'\s+\d+\.?\d*[xX]\d+\.?\d*\s*$', '', name)
    name = _re.sub(r'\s*\([^)]*\)\s*$', '', name)
    return name.strip()


def _format_material_label(material_name: str, thickness_mm: float) -> str:
    """Return the formatted material string for presupuesto/OT copy-paste blocks.

    Uses the 'familia' field from material_table.json to decide the format:
      hierro      → N°{calibre}
      galvanizada → Galv N°{calibre}
      inox304     → Inox 304 {espesor}mm
      inox430     → Inox 430 {espesor}mm
    Falls back to material-name inference when 'familia' is absent.
    """
    table = MaterialTable()
    entry = next(
        (
            e for e in table.list()
            if e["material"] == material_name
            and abs(float(e.get("espesor_mm", 0)) - thickness_mm) < 0.001
        ),
        None,
    )
    if entry is None:
        return f"{thickness_mm:g}mm"
    familia = str(entry.get("familia", "")).lower()
    calibre = str(entry.get("calibre", "-")).strip()
    espesor = float(entry.get("espesor_mm", thickness_mm))
    if familia == "hierro":
        return f"N°{calibre}" if calibre and calibre != "-" else f"{espesor:g}mm"
    if familia == "galvanizada":
        return f"Galv N°{calibre}" if calibre and calibre != "-" else f"Galv {espesor:g}mm"
    if familia == "inox304":
        return f"Inox 304 {espesor:g}mm"
    if familia == "inox430":
        return f"Inox 430 {espesor:g}mm"
    # Fallback: infer from material name
    mn = material_name.lower()
    if "galvaniz" in mn:
        return f"Galv N°{calibre}" if calibre and calibre != "-" else f"Galv {espesor:g}mm"
    if "304" in mn:
        return f"Inox 304 {espesor:g}mm"
    if "430" in mn:
        return f"Inox 430 {espesor:g}mm"
    return f"N°{calibre}" if calibre and calibre != "-" else f"{espesor:g}mm"


# ---------------------------------------------------------------------------
# render_landing — hub page at /
# ---------------------------------------------------------------------------

def render_landing() -> str:
    """Landing hub: navigation cards to product lines."""
    return """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SistemaIndustrial</title>
  <style>
""" + _COMMON_CSS + """
    .hub-title { font-size:26px; font-weight:700; color:var(--brand); margin:32px 0 8px; }
    .hub-sub { color:var(--muted); font-size:14px; margin-bottom:32px; }
    .hub-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(240px,1fr)); gap:20px; }
    .hub-card { background:#fff; border:1.5px solid #c5dde8; border-radius:10px; padding:28px 22px;
                text-decoration:none; color:inherit; display:block;
                transition:border-color .15s, box-shadow .15s; }
    .hub-card:hover { border-color:var(--brand); box-shadow:0 4px 16px rgba(23,107,135,.15); }
    .hub-card-icon { font-size:30px; margin-bottom:12px; line-height:1; }
    .hub-card-title { font-size:16px; font-weight:700; color:var(--brand); margin-bottom:6px; }
    .hub-card-desc { font-size:13px; color:var(--muted); line-height:1.55; }
    .hub-card.disabled { opacity:.5; cursor:default; pointer-events:none;
                         border-color:#dde3ea; background:#f7f9fb; }
    .badge-prox { display:inline-block; margin-top:10px; font-size:10px; font-weight:700;
                  text-transform:uppercase; letter-spacing:.5px; background:#e0e6ed;
                  color:#7a8fa0; padding:2px 8px; border-radius:4px; }
  </style>
</head>
<body>
""" + _topbar_html("landing") + """
<div class="page-wrapper">
  <h1 class="hub-title">Líneas de producto</h1>
  <p class="hub-sub">Seleccioná la sección con la que querés trabajar.</p>
  <div class="hub-grid">
    <a href="/paneles" class="hub-card">
      <div class="hub-card-icon">⬛</div>
      <div class="hub-card-title">Paneles Decorativos</div>
      <div class="hub-card-desc">Chapas perforadas con patrones. Cotización automática por lote.</div>
    </a>
    <a href="/plegados/perfiles" class="hub-card">
      <div class="hub-card-icon">📐</div>
      <div class="hub-card-title">Perfiles Plegados</div>
      <div class="hub-card-desc">Perfiles L, U, Z, C y variantes. Simulación de secuencia de plegado.</div>
    </a>
    <a href="/plegados/complejos" class="hub-card">
      <div class="hub-card-icon">📦</div>
      <div class="hub-card-title">Plegados Complejos</div>
      <div class="hub-card-desc">Bandejas, canales y formas compuestas. Cálculo de presets.</div>
    </a>
    <div class="hub-card disabled">
      <div class="hub-card-icon">🔩</div>
      <div class="hub-card-title">Perfiles y Caños</div>
      <div class="hub-card-desc">Corte y preparación de perfiles y caños.</div>
      <span class="badge-prox">Próximamente</span>
    </div>
  </div>
</div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# render_form — main gallery page (Steps 1-3 + batch list + generate)
# ---------------------------------------------------------------------------

def render_form(error: str = "", result: SalesRunResult | None = None, load: str | None = None) -> str:
    """Render the main gallery page."""

    result_section = ""
    if result is not None:
        import re as _re_paste
        import datetime as _dt_res
        data = result.service_result
        dxf_rel = escape(data.dxf_path.name)

        # ---- Read generation data -------------------------------------------
        _paste_items: list[dict] = []
        _pres_numero_link: str | None = None
        _fecha_gen = ""
        _customer_gen = ""
        _job_name_gen = ""
        try:
            if LAST_GENERATE_FILE.exists():
                _lg_full = json.loads(LAST_GENERATE_FILE.read_text(encoding="utf-8"))
                _paste_items = _lg_full.get("lineas", [])
                _pres_numero_link = _lg_full.get("pres_numero")
                _fecha_gen = _lg_full.get("fecha", "")
                _customer_gen = _lg_full.get("customer", "")
                _job_name_gen = _lg_full.get("job_name", "")
        except Exception:
            pass
        if not _paste_items:
            _paste_items = list(data.calculated_resources)

        try:
            _fecha_display = _dt_res.date.fromisoformat(_fecha_gen).strftime("%d/%m/%Y")
        except Exception:
            _fecha_display = _fecha_gen

        # ---- Build presupuesto inline table ---------------------------------
        _total_gen = 0.0
        _grand_kg = 0.0
        _grand_seconds = 0.0
        _grand_pierces = 0
        _inline_rows = ""
        _paste_lines_pres: list[str] = []
        _paste_lines_ot: list[str] = []

        for _pr in _paste_items:
            _pr_patron = str(_pr.get("patron") or _pr.get("name", ""))
            _pr_name_clean = _clean_pattern_name(_pr_patron)
            _pr_mat = str(_pr.get("material") or "")
            _pr_thick = float(_pr.get("espesor_mm") or _pr.get("thickness_mm") or 0)
            _pr_qty = int(_pr.get("cantidad") or _pr.get("quantity") or 1)
            _pr_w_raw = _pr.get("occupied_width_mm")
            _pr_h_raw = _pr.get("occupied_height_mm")
            if _pr_w_raw is None or _pr_h_raw is None:
                _m = _re_paste.search(r'(\d+\.?\d*)[xX](\d+\.?\d*)', _pr_patron)
                _pr_w_raw = _m.group(1) if _m else "?"
                _pr_h_raw = _m.group(2) if _m else "?"
            try:
                _pr_w_str = str(int(float(_pr_w_raw)))
                _pr_h_str = str(int(float(_pr_h_raw)))
            except (ValueError, TypeError):
                _pr_w_str = str(_pr_w_raw)
                _pr_h_str = str(_pr_h_raw)
            _pr_cost = float((_pr.get("cost") or {}).get("costo_total", 0.0))
            _pr_unit = _pr_cost / _pr_qty if _pr_qty else 0.0
            _pr_mat_label = _format_material_label(_pr_mat, _pr_thick)
            _pr_dims = f"{_pr_w_str} x {_pr_h_str}"
            _total_gen += _pr_cost

            _cr = _pr.get("consumed_resources") or {}
            _grand_kg += float(_cr.get("material_kg", 0))
            _grand_seconds += float(_cr.get("machine_seconds", 0))
            _grand_pierces += int(_cr.get("pierce_count", 0))

            _inline_rows += (
                f"<tr>"
                f"<td>{escape(_pr_patron)}</td>"
                f"<td>{escape(_pr_mat_label)}</td>"
                f"<td style='text-align:center'>{_pr_qty}</td>"
                f"<td style='text-align:right'>$ {_pr_unit:,.2f}</td>"
                f"<td style='text-align:right'>$ {_pr_cost:,.2f}</td>"
                f"</tr>"
            )
            _paste_lines_pres.append(
                f"{_pr_qty}\tPanel {_pr_name_clean}\t{_pr_dims}\ten {_pr_mat_label}\t{_format_number_locale(_pr_cost)}"
            )
            _paste_lines_ot.append(
                f"{_pr_qty}\tPanel {_pr_name_clean}\t{_pr_dims}\ten {_pr_mat_label} / [{_pr_name_clean}.dxf]"
            )

        _mins_res = int(_grand_seconds) // 60
        _secs_res = int(_grand_seconds) % 60
        _pres_href = f"/presupuesto?id={_pres_numero_link}" if _pres_numero_link else "/presupuesto"
        _pres_label = f"PRES_{_pres_numero_link}" if _pres_numero_link else "Presupuesto"

        _paste_pres_html = escape("\n".join(_paste_lines_pres))
        _paste_ot_html = escape("\n".join(_paste_lines_ot))
        _paste_rows_count = max(2, min(len(_paste_lines_pres), 6))

        _sug_raw = f"{_customer_gen}_{_job_name_gen}" if _job_name_gen else (_customer_gen or "panel")
        _dxf_suggested_name = re.sub(r'[^A-Za-z0-9._\-]', '_', _sug_raw).strip('_') + ".dxf"

        result_section = f"""
  <div class="card" id="result-card">
    <div class="card-title" style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
      <span>{_pres_label}</span>
      <div style="display:flex;gap:10px;align-items:center">
        <button onclick="saveDxfAs('/outputs/{dxf_rel}', '{_dxf_suggested_name}')"
                style="padding:6px 14px;background:var(--accent2);color:#fff;border-radius:6px;border:none;cursor:pointer;font-weight:700;font-size:13px">
          &#11015; Descargar DXF
        </button>
        <a href="{_pres_href}" target="_blank"
           style="padding:6px 14px;background:#eee;color:#333;border-radius:6px;text-decoration:none;font-size:13px">
          Imprimir ↗
        </a>
      </div>
    </div>

    <div style="font-size:13px;color:#555;margin-bottom:16px">
      {escape(_fecha_display)}&nbsp;&nbsp;|&nbsp;&nbsp;{escape(_customer_gen)}&nbsp;&nbsp;|&nbsp;&nbsp;{escape(_job_name_gen)}
    </div>

    <!-- Tabla de paneles -->
    <table style="width:100%;border-collapse:collapse;font-size:13px;margin-bottom:16px">
      <thead>
        <tr style="background:var(--surface-alt,#f5f5f5);font-weight:700;font-size:12px;text-transform:uppercase;letter-spacing:.04em">
          <th style="text-align:left;padding:8px 10px">Patrón</th>
          <th style="text-align:left;padding:8px 10px">Material</th>
          <th style="text-align:center;padding:8px 6px">Cant.</th>
          <th style="text-align:right;padding:8px 10px">P. Unit.</th>
          <th style="text-align:right;padding:8px 10px">Total</th>
        </tr>
      </thead>
      <tbody style="border-top:1px solid var(--border,#ddd)">
        {_inline_rows}
      </tbody>
      <tfoot>
        <tr style="border-top:2px solid var(--border,#ddd);font-weight:700">
          <td colspan="4" style="text-align:right;padding:10px 10px">TOTAL</td>
          <td style="text-align:right;padding:10px 10px">$ {_total_gen:,.2f}</td>
        </tr>
      </tfoot>
    </table>

    <!-- Recursos -->
    <div style="display:flex;gap:24px;font-size:12px;color:#666;padding:10px 0;border-top:1px solid var(--border,#eee)">
      <span>Material: <strong>{_grand_kg:.3f} kg</strong></span>
      <span>Tiempo de máquina: <strong>{_mins_res} min {_secs_res:02d} s</strong></span>
      <span>Perforaciones: <strong>{_grand_pierces}</strong></span>
    </div>

    <!-- Copy-paste para Excel / OT -->
    <div style="margin-top:20px;border-top:1px solid var(--border,#eee);padding-top:16px">
      <div class="paste-block">
        <div class="paste-block-header">
          <div>
            <span class="paste-block-title">Para el Presupuesto</span>
            <span class="paste-block-hint">Pegar en celda B25 del presupuesto</span>
          </div>
          <button class="btn-copy" onclick="copyPasteBlock(this,'paste-pres')">Copiar</button>
        </div>
        <textarea id="paste-pres" class="paste-textarea" readonly rows="{_paste_rows_count}">{_paste_pres_html}</textarea>
      </div>
      <div class="paste-block" style="margin-top:12px">
        <div class="paste-block-header">
          <div>
            <span class="paste-block-title">Para la OT</span>
            <span class="paste-block-hint">Pegar en columna B de la OT</span>
          </div>
          <button class="btn-copy" onclick="copyPasteBlock(this,'paste-ot')">Copiar</button>
        </div>
        <textarea id="paste-ot" class="paste-textarea" readonly rows="{_paste_rows_count}">{_paste_ot_html}</textarea>
      </div>
    </div>
  </div>"""

    error_html = f'<div class="error-box">{escape(error)}</div>' if error else ""

    # ---- Pre-load batches from ?load=NNNN ----------------------------------------
    _preloaded_batches: list = []
    if load:
        try:
            pfile = PRESUPUESTOS_DIR / f"PRES_{load}.json"
            _preloaded_batches = json.loads(pfile.read_text(encoding="utf-8")).get("batches", [])
        except Exception:
            pass

    import json as _json_bl
    _preloaded_batches_js = _json_bl.dumps(_preloaded_batches, ensure_ascii=False)
    _section_batches_class = "card hidden"
    _wizard_hidden = "hidden" if result is not None else ""

    _tres_url = _thumbnail_url("Tresbolillo")
    if _tres_url:
        tres_thumb_html = (
            f'        <div class="pattern-thumb thumb-tres">\n'
            f'          <img src="{_tres_url}" alt="Tresbolillo"'
            f' style="width:100%;height:100%;object-fit:contain">\n'
            f'        </div>'
        )
    else:
        tres_thumb_html = (
            '        <div class="pattern-thumb thumb-tres">\n'
            '          <svg width="100%" height="100%" viewBox="0 0 100 100" opacity=".5">\n'
            '            <circle cx="20" cy="20" r="7" fill="#7a9aaa"/>\n'
            '            <circle cx="50" cy="20" r="7" fill="#7a9aaa"/>\n'
            '            <circle cx="80" cy="20" r="7" fill="#7a9aaa"/>\n'
            '            <circle cx="35" cy="44" r="7" fill="#7a9aaa"/>\n'
            '            <circle cx="65" cy="44" r="7" fill="#7a9aaa"/>\n'
            '            <circle cx="20" cy="68" r="7" fill="#7a9aaa"/>\n'
            '            <circle cx="50" cy="68" r="7" fill="#7a9aaa"/>\n'
            '            <circle cx="80" cy="68" r="7" fill="#7a9aaa"/>\n'
            '            <circle cx="35" cy="92" r="7" fill="#7a9aaa"/>\n'
            '            <circle cx="65" cy="92" r="7" fill="#7a9aaa"/>\n'
            '          </svg>\n'
            '        </div>'
        )

    _cuad_url = _thumbnail_url("Cuadriculado")
    if _cuad_url:
        cuad_thumb_html = (
            f'        <div class="pattern-thumb thumb-cuad">\n'
            f'          <img src="{_cuad_url}" alt="Cuadriculado"'
            f' style="width:100%;height:100%;object-fit:contain">\n'
            f'        </div>'
        )
    else:
        cuad_thumb_html = (
            '        <div class="pattern-thumb thumb-cuad">\n'
            '          <svg width="100%" height="100%" viewBox="0 0 100 100" opacity=".5">\n'
            '            <circle cx="20" cy="20" r="7" fill="#7a9aaa"/>\n'
            '            <circle cx="50" cy="20" r="7" fill="#7a9aaa"/>\n'
            '            <circle cx="80" cy="20" r="7" fill="#7a9aaa"/>\n'
            '            <circle cx="20" cy="50" r="7" fill="#7a9aaa"/>\n'
            '            <circle cx="50" cy="50" r="7" fill="#7a9aaa"/>\n'
            '            <circle cx="80" cy="50" r="7" fill="#7a9aaa"/>\n'
            '            <circle cx="20" cy="80" r="7" fill="#7a9aaa"/>\n'
            '            <circle cx="50" cy="80" r="7" fill="#7a9aaa"/>\n'
            '            <circle cx="80" cy="80" r="7" fill="#7a9aaa"/>\n'
            '          </svg>\n'
            '        </div>'
        )

    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Nextango — Paneles Decorativos</title>
  <style>
{_COMMON_CSS}
    .page-title {{ font-size:22px; font-weight:700; color:var(--brand); margin-bottom:24px; }}
    /* Stepper */
    .stepper {{ display:flex; align-items:center; gap:0; margin-bottom:28px; }}
    .step-item {{ display:flex; align-items:center; gap:8px; }}
    .step-bubble {{ width:30px; height:30px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:13px; border:2px solid #ccc; background:#fff; color:#999; flex-shrink:0; transition:all .2s; }}
    .step-bubble.active {{ border-color:var(--brand); background:var(--brand); color:#fff; }}
    .step-bubble.done {{ border-color:var(--brand); background:#e8f4f8; color:var(--brand); }}
    .step-label {{ font-size:13px; color:#999; white-space:nowrap; }}
    .step-label.active {{ color:var(--brand); font-weight:600; }}
    .step-label.done {{ color:var(--brand); }}
    .step-connector {{ flex:1; height:2px; background:#ddd; margin:0 10px; min-width:40px; transition:background .2s; }}
    .step-connector.done {{ background:var(--brand); }}
    /* Pattern gallery */
    .pattern-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(140px,1fr)); gap:12px; }}
    .pattern-card {{ display:flex; flex-direction:column; align-items:center; cursor:pointer; border-radius:8px; border:2px solid #e0e0e0; padding:10px; background:#fafafa; transition:border-color .18s,box-shadow .18s; user-select:none; min-width:0; }}
    .pattern-card:hover {{ border-color:var(--brand); box-shadow:0 2px 12px rgba(23,107,135,.18); }}
    .pattern-card.selected {{ border-color:var(--brand); background:#e8f4f8; box-shadow:0 0 0 3px rgba(23,107,135,.15); }}
    .pattern-thumb {{ width:100%; aspect-ratio:1; background:#d0d8e0; border-radius:6px; display:flex; align-items:center; justify-content:center; overflow:hidden; }}
    .pattern-thumb img {{ width:100%; height:100%; object-fit:cover; border-radius:6px; }}
    .pattern-thumb.thumb-tres {{ background:#c8d5de; }}
    .pattern-thumb.thumb-dxf {{ background:#d0cfe0; }}
    .pattern-name {{ margin-top:8px; font-size:13px; font-weight:600; color:#2c3e50; text-align:center; }}
    .pattern-badge {{ margin-top:4px; font-size:10px; color:#888; text-transform:uppercase; letter-spacing:.8px; }}
    .selected-indicator {{ margin-top:6px; font-size:11px; font-weight:700; color:var(--brand); display:none; }}
    .pattern-card.selected .selected-indicator {{ display:block; }}
    /* Outline cards */
    .outline-options {{ display:flex; gap:14px; flex-wrap:wrap; }}
    .outline-card {{ display:flex; flex-direction:column; align-items:center; border:2px solid #e0e0e0; border-radius:8px; padding:14px 20px; cursor:pointer; background:#fafafa; transition:border-color .18s; min-width:130px; }}
    .outline-card.active {{ border-color:var(--brand); background:#e8f4f8; box-shadow:0 0 0 3px rgba(23,107,135,.15); }}
    .outline-card.disabled {{ opacity:.5; cursor:not-allowed; background:#f5f5f5; }}
    .outline-diagram {{ width:64px; height:46px; margin-bottom:10px; }}
    .outline-name {{ font-size:13px; font-weight:600; color:#2c3e50; text-align:center; }}
    .prox-badge {{ margin-top:4px; font-size:10px; color:#aaa; font-style:italic; }}
    /* Parameters form */
    .radio-group {{ display:flex; gap:0; border:1px solid #ccc; border-radius:5px; overflow:hidden; }}
    .radio-group label {{ flex:1; display:flex; align-items:center; justify-content:center; gap:6px; padding:8px 10px; cursor:pointer; background:#fff; font-size:12px; letter-spacing:0; text-transform:none; font-weight:500; color:#444; border-right:1px solid #ddd; transition:background .12s; }}
    .radio-group label:last-child {{ border-right:none; }}
    .radio-group input[type=radio] {{ display:none; }}
    .radio-group label.checked-option {{ background:#e8f4f8; color:var(--brand); font-weight:700; }}
    #dist-group label {{ flex-direction:column; align-items:center; gap:0; padding:10px 8px 0; }}
    .dist-thumb {{ overflow:hidden; align-self:stretch; margin-top:8px; border-top:1px solid #ddd; aspect-ratio:3/1; background-size:contain; background-repeat:no-repeat; background-position:center; background-color:#f8f9fa; }}
    .dist-thumb-left {{ background-image:url('/static/tools/comparacion_centradas.png'); }}
    .dist-thumb-right {{ background-image:url('/static/tools/comparacion_cortar.png'); }}
    .conditional-block {{ background:#f7fbfd; border:1px dashed #a8d0e0; border-radius:6px; padding:14px 16px; margin-bottom:16px; }}
    .conditional-label {{ font-size:11px; font-weight:700; letter-spacing:.9px; text-transform:uppercase; color:var(--brand); margin-bottom:12px; }}
    /* Buttons */
    .btn-add {{ display:block; width:100%; padding:13px; background:var(--brand); color:#fff; font-size:15px; font-weight:700; letter-spacing:1px; text-transform:uppercase; border:none; border-radius:6px; cursor:pointer; margin-top:8px; transition:background .15s; }}
    .btn-add:hover {{ background:var(--brand-dark); }}
    .btn-generate {{ padding:12px 36px; background:var(--green); color:#fff; font-size:15px; font-weight:700; letter-spacing:1.2px; text-transform:uppercase; border:none; border-radius:6px; cursor:pointer; transition:background .15s; box-shadow:0 2px 8px rgba(46,125,50,.3); }}
    .btn-generate:hover {{ background:#256427; }}
    /* Batch table */
    .batch-table {{ width:100%; border-collapse:collapse; font-size:13px; }}
    .batch-table thead tr {{ background:#e8f4f8; }}
    .batch-table th {{ padding:9px 12px; text-align:left; font-size:11px; font-weight:700; letter-spacing:.7px; text-transform:uppercase; color:var(--brand); border-bottom:2px solid #c5dde8; }}
    .batch-table td {{ padding:10px 12px; border-bottom:1px solid #eef1f4; color:#333; vertical-align:middle; }}
    .batch-table tr:last-child td {{ border-bottom:none; }}
    .batch-table tr:hover td {{ background:#f5fafe; }}
    .btn-delete {{ padding:4px 10px; background:#fff; border:1px solid #e57373; color:#e57373; border-radius:4px; font-size:12px; cursor:pointer; }}
    .btn-delete:hover {{ background:#fff0f0; }}
    .generate-row {{ display:flex; justify-content:flex-end; align-items:center; gap:16px; margin-top:20px; }}
    .generate-count {{ font-size:13px; color:#555; }}
    .section-label {{ font-size:11px; font-weight:700; letter-spacing:1.2px; text-transform:uppercase; color:var(--brand); margin-bottom:14px; border-bottom:2px solid #e8f4f8; padding-bottom:10px; }}
    .restricted-banner {{ background:#fff8e1; border:1px solid #ffe082; border-radius:6px; padding:10px 16px; margin-top:14px; font-size:13px; color:#e65100; display:flex; align-items:flex-start; gap:8px; }}
    .restricted-banner .rb-icon {{ font-size:16px; flex-shrink:0; margin-top:1px; }}
    /* Material dropdowns (cascade) */
    .mat-dropdown-row {{ display:flex; gap:8px; align-items:flex-end; margin-bottom:16px; }}
    .mat-dropdown-row .form-group {{ flex:1; margin-bottom:0; }}
    .btn-refresh {{ padding:8px 12px; background:#fff; border:1px solid #ccc; border-radius:5px; cursor:pointer; font-size:15px; color:var(--brand); transition:background .12s; height:36px; }}
    .btn-refresh:hover {{ background:#e8f4f8; }}
    /* Consumed resources panel */
    .consumed-panel {{ background:#f0f7ff; border:1px solid #b3d4f0; border-radius:8px; padding:16px 20px; margin-top:16px; }}
    .consumed-title {{ font-size:11px; font-weight:700; letter-spacing:1.1px; text-transform:uppercase; color:var(--brand); margin-bottom:10px; }}
    .consumed-table {{ border-collapse:collapse; font-size:14px; }}
    .consumed-table tr td {{ padding:4px 24px 4px 0; vertical-align:baseline; }}
    .consumed-label {{ color:#555; font-weight:600; width:130px; }}
    .consumed-val {{ color:#1a1a2e; font-family:monospace; font-size:15px; }}
    .consumed-warn {{ background:#fff8e1; border-color:#ffe082; color:#7a5000; display:flex; align-items:flex-start; gap:10px; }}
    .consumed-warn-icon {{ font-size:18px; flex-shrink:0; }}
    .consumed-partial-warn {{ margin-top:10px; font-size:12px; color:#7a5000; background:#fff8e1; border-radius:4px; padding:6px 10px; }}
    .consumed-type-block {{ border-left:3px solid var(--brand); padding-left:12px; }}
    .consumed-type-block.consumed-warn {{ border-left-color:#e6a000; background:#fff8e1; border-radius:0 6px 6px 0; padding:8px 12px; display:flex; align-items:flex-start; gap:10px; }}
    .consumed-type-header {{ font-size:13px; color:#2c3e50; margin-bottom:2px; }}
    .consumed-qty-badge {{ font-size:11px; color:#888; font-weight:400; }}
    .consumed-total-row {{ margin-top:12px; padding-top:10px; border-top:1px solid #c8dded; font-size:13px; color:#555; }}
    /* Copy-paste blocks */
    .paste-block {{ background:#f7fbfd; border:1px solid #c8dded; border-radius:8px; padding:14px 16px; }}
    .paste-block-header {{ display:flex; align-items:center; justify-content:space-between; margin-bottom:10px; flex-wrap:wrap; gap:8px; }}
    .paste-block-title {{ font-size:13px; font-weight:700; color:var(--brand); display:block; }}
    .paste-block-hint {{ font-size:11px; color:#888; margin-top:2px; display:block; }}
    .paste-textarea {{ width:100%; font-family:monospace; font-size:12px; background:#fff; border:1px solid #d0dde8; border-radius:5px; padding:10px 12px; color:#2c3e50; resize:vertical; box-sizing:border-box; white-space:pre; }}
    .btn-copy {{ padding:7px 16px; background:var(--brand); color:#fff; border:none; border-radius:5px; font-size:12px; font-weight:700; cursor:pointer; transition:background .15s; white-space:nowrap; flex-shrink:0; }}
    .btn-copy:hover {{ background:var(--brand-dark); }}
    .btn-copy.copied {{ background:var(--green); }}
  </style>
</head>
<body>
{_topbar_html("paneles")}
<div class="page-wrapper">
  <h1 class="page-title {_wizard_hidden}">Nuevo pedido — Paneles Decorativos</h1>
  {error_html}

  <!-- Stepper indicator -->
  <div class="stepper {_wizard_hidden}" id="stepper">
    <div class="step-item">
      <div class="step-bubble active" id="bubble-1">1</div>
      <span class="step-label active" id="label-1">Patron</span>
    </div>
    <div class="step-connector" id="conn-1-2"></div>
    <div class="step-item">
      <div class="step-bubble" id="bubble-2">2</div>
      <span class="step-label" id="label-2">Contorno</span>
    </div>
    <div class="step-connector" id="conn-2-3"></div>
    <div class="step-item">
      <div class="step-bubble" id="bubble-3">3</div>
      <span class="step-label" id="label-3">Parametros</span>
    </div>
  </div>

  <!-- PASO 1: Galeria de patrones -->
  <div class="card {_wizard_hidden}" id="step1">
    <div class="card-title">1 — Elegi un patron</div>
    <div class="pattern-grid" id="pattern-grid">
      <!-- Tresbolillo — always first, built-in -->
      <div class="pattern-card" id="pcard-tresbolillo"
           onclick="selectPattern('tresbolillo','Tresbolillo','tresbolillo',null,null,null)">
{tres_thumb_html}
        <div class="pattern-name">Tresbolillo</div>
        <div class="pattern-badge">Motor nativo</div>
        <div class="selected-indicator">Seleccionado</div>
      </div>
      <!-- Cuadriculado — built-in -->
      <div class="pattern-card" id="pcard-cuadriculado"
           onclick="selectPattern('cuadriculado','Cuadriculado','cuadriculado',null,null,null)">
{cuad_thumb_html}
        <div class="pattern-name">Cuadriculado</div>
        <div class="pattern-badge">Motor nativo</div>
        <div class="selected-indicator">Seleccionado</div>
      </div>
      <!-- DXF patterns injected by JS -->
    </div>
    <p id="pattern-loading" class="dimmed" style="margin-top:12px">Cargando patrones de la libreria...</p>

    <!-- Aviso modo restringido: visible solo cuando el patron seleccionado tiene restricciones -->
    <div id="restricted-banner" class="restricted-banner hidden">
      <span class="rb-icon">&#9888;</span>
      <span id="restricted-banner-text">Este patron solo admite modo centrado — el corte en borde esta deshabilitado.</span>
    </div>

    <!-- Parametros de tresbolillo: aparecen aqui cuando se selecciona ese patron -->
    <div id="tres-inline" style="display:none;margin-top:20px;border-top:1px solid #e8f4f8;padding-top:18px">
      <div class="conditional-label" style="margin-bottom:12px">Parametros del tresbolillo</div>
      <div class="form-row">
        <div class="form-group">
          <label for="p-diam">Diametro agujero mm</label>
          <input type="number" id="p-diam" placeholder="ej. 20" min="0.1" step="0.1" value="20">
        </div>
        <div class="form-group">
          <label for="p-dist">Distancia entre centros mm</label>
          <input type="number" id="p-dist" placeholder="ej. 60" min="0.1" step="0.1" value="60">
        </div>
      </div>
      <button class="btn-add" style="margin-top:4px" onclick="confirmTresbolillo()">Confirmar patron &rarr;</button>
    </div>

    <!-- Parametros de cuadriculado: aparecen aqui cuando se selecciona ese patron -->
    <div id="cuad-inline" style="display:none;margin-top:20px;border-top:1px solid #e8f4f8;padding-top:18px">
      <div class="conditional-label" style="margin-bottom:12px">Parametros del cuadriculado</div>
      <div class="form-row">
        <div class="form-group">
          <label for="cuad-shape">Forma</label>
          <select id="cuad-shape" onchange="cuadShapeChanged()">
            <option value="circle">Circulo</option>
            <option value="square">Cuadrado</option>
          </select>
        </div>
        <div class="form-group">
          <label id="cuad-size-label" for="cuad-size">Diametro mm</label>
          <input type="number" id="cuad-size" placeholder="ej. 20" min="0.1" step="0.1" value="20">
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label for="cuad-ox">Offset X mm</label>
          <input type="number" id="cuad-ox" placeholder="ej. 30" min="0.1" step="0.1" value="30">
        </div>
        <div class="form-group">
          <label for="cuad-oy">Offset Y mm</label>
          <input type="number" id="cuad-oy" placeholder="ej. 30" min="0.1" step="0.1" value="30">
        </div>
      </div>
      <button class="btn-add" style="margin-top:4px" onclick="confirmCuadriculado()">Confirmar patron &rarr;</button>
    </div>
  </div>

  <!-- PASO 2: Contorno exterior (oculto hasta completar paso 1) -->
  <div class="card hidden" id="step2">
    <div class="card-title">2 — Contorno exterior</div>
    <div class="outline-options">
      <div class="outline-card active" id="outline-rect" onclick="selectOutline()">
        <svg class="outline-diagram" viewBox="0 0 64 46" fill="none">
          <rect x="4" y="4" width="56" height="38" rx="2" stroke="#176b87" stroke-width="2.5"/>
          <line x1="4" y1="42" x2="60" y2="42" stroke="#176b87" stroke-width="1" stroke-dasharray="2 2"/>
          <line x1="62" y1="4" x2="62" y2="42" stroke="#176b87" stroke-width="1" stroke-dasharray="2 2"/>
        </svg>
        <div class="outline-name">Rectangulo simple</div>
      </div>
      <div class="outline-card disabled">
        <svg class="outline-diagram" viewBox="0 0 64 46" fill="none">
          <path d="M4 42 L4 10 L12 4 L52 4 L60 10 L60 42 Z" stroke="#aaa" stroke-width="2" fill="none"/>
        </svg>
        <div class="outline-name">Bandeja</div>
        <div class="prox-badge">Proximamente</div>
      </div>
      <div class="outline-card disabled">
        <svg class="outline-diagram" viewBox="0 0 64 46" fill="none">
          <path d="M4 4 L4 42 L60 42 L60 4" stroke="#aaa" stroke-width="2" fill="none"/>
        </svg>
        <div class="outline-name">U</div>
        <div class="prox-badge">Proximamente</div>
      </div>
      <div class="outline-card disabled">
        <svg class="outline-diagram" viewBox="0 0 64 46" fill="none">
          <path d="M14 4 L4 4 L4 42 L14 42 M50 4 L60 4 L60 42 L50 42" stroke="#aaa" stroke-width="2" fill="none"/>
          <line x1="14" y1="4" x2="14" y2="42" stroke="#aaa" stroke-width="1" stroke-dasharray="3 3"/>
          <line x1="50" y1="4" x2="50" y2="42" stroke="#aaa" stroke-width="1" stroke-dasharray="3 3"/>
        </svg>
        <div class="outline-name">C / Omega</div>
        <div class="prox-badge">Proximamente</div>
      </div>
    </div>
  </div>

  <!-- PASO 3: Parametros (oculto hasta completar paso 2) -->
  <div class="card hidden" id="step3">
    <div class="card-title">3 — Parametros del panel</div>

    <!-- Modo de distribucion -->
    <div class="form-row">
      <div class="form-group">
        <div class="radio-group" id="dist-group">
          <label class="checked-option" id="lbl-centradas" onclick="setDist('centradas')">
            <input type="radio" name="distrib" value="centradas" checked>
            Figuras completas centradas
            <div class="dist-thumb dist-thumb-left"></div>
          </label>
          <label id="lbl-cortar" onclick="setDist('cortar')">
            <input type="radio" name="distrib" value="cortar">
            Cortar en borde
            <div class="dist-thumb dist-thumb-right"></div>
          </label>
        </div>
      </div>
    </div>

    <!-- Material y Espesor — dos dropdowns en cascada poblados desde /api/materials -->
    <div class="mat-dropdown-row">
      <div class="form-group">
        <label for="p-mat-tipo">Material</label>
        <select id="p-mat-tipo" onchange="onMatTipoChange(this)">
          <option value="" disabled selected>Cargando materiales...</option>
        </select>
      </div>
      <div class="form-group">
        <label for="p-mat-espesor">Espesor</label>
        <select id="p-mat-espesor" disabled onchange="onMatEspesorChange(this)">
          <option value="">Primero selecciona material</option>
        </select>
      </div>
      <button class="btn-refresh" title="Actualizar lista de materiales" onclick="loadMaterialDropdowns()">&#8635;</button>
    </div>
    <!-- Hidden fields used by addBatch() to build the batch object -->
    <input type="hidden" id="p-material" value="">
    <input type="hidden" id="p-espesor" value="">

    <!-- Cantidad / Ancho / Alto / Margen en una fila -->
    <div class="form-row">
      <div class="form-group">
        <label for="p-cantidad">Cantidad</label>
        <input type="number" id="p-cantidad" placeholder="1" min="1" step="1" value="1">
      </div>
      <div class="form-group">
        <label for="p-ancho">Ancho mm</label>
        <input type="number" id="p-ancho" placeholder="ej. 1200" min="1">
      </div>
      <div class="form-group">
        <label for="p-alto">Alto mm</label>
        <input type="number" id="p-alto" placeholder="ej. 600" min="1">
      </div>
      <div class="form-group">
        <label for="p-margen">Margen mm <span style="font-weight:400;color:#888">(borde sin perforar)</span></label>
        <input type="number" id="p-margen" placeholder="ej. 20" min="0" value="20">
      </div>
    </div>

    <!-- Offset DXF: oculto, tomado de la librería al seleccionar el patrón -->
    <div style="display:none" id="block-dxf-offset">
      <input type="hidden" id="p-offset-x" value="84">
      <input type="hidden" id="p-offset-y" value="84">
    </div>

    <div id="batch-error" class="error-box hidden" style="margin-top:8px"></div>
    <button class="btn-add" onclick="addBatch()">+ AGREGAR A LA LISTA</button>
  </div>

  <!-- Lista de lotes + GENERAR -->
  <div class="{_section_batches_class}" id="section-batches">
    <div class="section-label">Lista de lotes</div>
    <table class="batch-table">
      <thead>
        <tr>
          <th>Patron</th>
          <th>Contorno</th>
          <th>Medidas</th>
          <th>Margen</th>
          <th>Material / Esp.</th>
          <th>Cantidad</th>
          <th>Acciones</th>
        </tr>
      </thead>
      <tbody id="batch-tbody"></tbody>
    </table>
    <div class="generate-row">
      <span class="generate-count" id="generate-count"></span>
      <button class="btn-generate" onclick="submitGenerate()">GENERAR DXF</button>
    </div>
  </div>

  {result_section}

</div><!-- /page-wrapper -->

<!-- Hidden form used for generate submission -->
<form id="generate-form" method="post" action="/generate"
      enctype="multipart/form-data" style="display:none">
  <input type="hidden" id="f-customer" name="customer_reference">
  <input type="hidden" id="f-job" name="job_name">
  <input type="hidden" id="f-obs" name="observations">
  <input type="hidden" id="f-batches" name="batches_json">
</form>

<script>
// ---- State ----
var selectedPattern = null;
var distMode = 'centradas';
var batches = {_preloaded_batches_js};

// ---- Load material dropdowns (cascade) from /api/materials ----
var _allMaterials = [];  // cache del API response

function loadMaterialDropdowns() {{
  var tipoSel = document.getElementById('p-mat-tipo');
  var espSel  = document.getElementById('p-mat-espesor');
  var btnAdd  = document.querySelector('.btn-add');
  tipoSel.innerHTML = '<option value="" disabled selected>Cargando...</option>';
  espSel.innerHTML  = '<option value="">Primero selecciona material</option>';
  espSel.disabled   = true;
  document.getElementById('p-material').value = '';
  document.getElementById('p-espesor').value  = '';

  fetch('/api/materials')
    .then(function(r) {{ return r.json(); }})
    .then(function(data) {{
      _allMaterials = data || [];
      tipoSel.innerHTML = '';
      if (!_allMaterials.length) {{
        var opt = document.createElement('option');
        opt.value = ''; opt.disabled = true; opt.selected = true;
        opt.textContent = '— Carga materiales en /materiales —';
        tipoSel.appendChild(opt);
        if (btnAdd) {{ btnAdd.disabled = true; btnAdd.title = 'Carga materiales en /materiales primero'; }}
        return;
      }}
      var placeholder = document.createElement('option');
      placeholder.value = ''; placeholder.disabled = true; placeholder.selected = true;
      placeholder.textContent = 'Selecciona material...';
      tipoSel.appendChild(placeholder);
      // Unique material types, preserving order of first occurrence
      var seen = [];
      _allMaterials.forEach(function(e) {{
        if (seen.indexOf(e.material) === -1) seen.push(e.material);
      }});
      seen.forEach(function(t) {{
        var opt = document.createElement('option');
        opt.value = t; opt.textContent = t;
        tipoSel.appendChild(opt);
      }});
      if (btnAdd) {{ btnAdd.disabled = false; btnAdd.title = ''; }}
    }})
    .catch(function() {{
      tipoSel.innerHTML = '<option value="" disabled selected>Error al cargar materiales</option>';
      if (btnAdd) {{ btnAdd.disabled = true; }}
    }});
}}

function onMatTipoChange(sel) {{
  var tipo = sel.value;
  var espSel = document.getElementById('p-mat-espesor');
  document.getElementById('p-material').value = tipo;
  document.getElementById('p-espesor').value  = '';

  if (!tipo) {{
    espSel.innerHTML = '<option value="">Primero selecciona material</option>';
    espSel.disabled = true;
    return;
  }}

  var entries = _allMaterials.filter(function(e) {{ return e.material === tipo; }});
  espSel.innerHTML = '<option value="">Selecciona espesor...</option>';
  var mostrarCalibre = entries[0] && entries[0].calibre && entries[0].calibre !== '-';
  entries.forEach(function(e) {{
    var opt = document.createElement('option');
    opt.value = e.espesor_mm;
    opt.textContent = mostrarCalibre
      ? ('N°' + e.calibre + ' - ' + e.espesor_mm + 'mm')
      : (e.espesor_mm + 'mm');
    espSel.appendChild(opt);
  }});
  espSel.disabled = false;
}}

function onMatEspesorChange(sel) {{
  document.getElementById('p-espesor').value = sel.value;
}}

// Load dropdowns on page mount
loadMaterialDropdowns();
if (batches.length) {{ renderBatchTable(); }}

// ---- Load DXF patterns from API ----
fetch('/api/patterns')
  .then(function(r) {{ return r.json(); }})
  .then(function(data) {{
    var grid = document.getElementById('pattern-grid');
    document.getElementById('pattern-loading').style.display = 'none';
    Object.keys(data).forEach(function(name) {{
      var p = data[name];
      var card = document.createElement('div');
      card.className = 'pattern-card';
      card.id = 'pcard-' + name.replace(/[^a-z0-9]/gi, '_');
      var isRestricted = !!p.restricted;
      var thumbContent = p.thumbnail_url
        ? '<img src="' + p.thumbnail_url + '" alt="' + name + '">'
        : '<svg width="80" height="80" viewBox="0 0 100 100" opacity=".4">'
          + '<rect x="10" y="10" width="22" height="22" fill="none" stroke="#8878aa" stroke-width="2"/>'
          + '<rect x="40" y="10" width="22" height="22" fill="none" stroke="#8878aa" stroke-width="2"/>'
          + '<rect x="10" y="40" width="22" height="22" fill="none" stroke="#8878aa" stroke-width="2"/>'
          + '<rect x="40" y="40" width="22" height="22" fill="none" stroke="#8878aa" stroke-width="2"/>'
          + '</svg>';
      var restrictedBadge = isRestricted
        ? '<div class="pattern-badge" style="color:#e65100">&#9888; Modo restringido</div>'
        : '';
      card.innerHTML =
        '<div class="pattern-thumb thumb-dxf">' + thumbContent + '</div>' +
        '<div class="pattern-name">' + name + '</div>' +
        '<div class="pattern-badge">DXF</div>' +
        restrictedBadge +
        '<div class="selected-indicator">Seleccionado</div>';
      var fp = p.file_path || null;
      var sx = p.step_x || 84;
      var sy = p.step_y || 84;
      var restr = isRestricted;
      card.onclick = (function(n,f,x,y,r) {{
        return function() {{ selectPattern('dxf_pattern_grid', n, 'dxf', f, x, y, r); }};
      }})(name, fp, sx, sy, restr);
      grid.appendChild(card);
    }});
  }})
  .catch(function() {{
    document.getElementById('pattern-loading').textContent = 'No se pudieron cargar patrones DXF.';
  }});

// ---- Step machine ----
function selectPattern(mode, name, ptype, file_path, step_x, step_y, restricted) {{
  // Highlight selected card
  document.querySelectorAll('.pattern-card').forEach(function(c) {{ c.classList.remove('selected'); }});
  var cardId = mode === 'tresbolillo' ? 'pcard-tresbolillo' : 'pcard-' + name.replace(/[^a-z0-9]/gi, '_');
  var el = document.getElementById(cardId);
  if (el) el.classList.add('selected');

  // Show or hide the restricted banner and disable "Cortar en borde" when restricted
  var banner = document.getElementById('restricted-banner');
  var lblCortar = document.getElementById('lbl-cortar');
  if (restricted) {{
    banner.classList.remove('hidden');
    if (lblCortar) {{
      lblCortar.style.opacity = '0.4';
      lblCortar.style.pointerEvents = 'none';
      lblCortar.title = 'No disponible para este patron (contiene entidades no soportadas)';
    }}
    // Force distribution mode to centradas
    setDist('centradas');
  }} else {{
    banner.classList.add('hidden');
    if (lblCortar) {{
      lblCortar.style.opacity = '';
      lblCortar.style.pointerEvents = '';
      lblCortar.title = '';
    }}
  }}

  if (mode === 'tresbolillo') {{
    // Tresbolillo: show inline params — don't advance to step 2 yet
    document.getElementById('tres-inline').style.display = '';
    document.getElementById('cuad-inline').style.display = 'none';
    setTimeout(function() {{
      document.getElementById('tres-inline').scrollIntoView({{behavior:'smooth', block:'nearest'}});
    }}, 60);
  }} else if (mode === 'cuadriculado') {{
    // Cuadriculado: show inline params — don't advance to step 2 yet
    document.getElementById('cuad-inline').style.display = '';
    document.getElementById('tres-inline').style.display = 'none';
    setTimeout(function() {{
      document.getElementById('cuad-inline').scrollIntoView({{behavior:'smooth', block:'nearest'}});
    }}, 60);
  }} else {{
    // DXF pattern: save state and advance to step 2 directly
    selectedPattern = {{mode:mode, name:name, ptype:ptype, file_path:file_path, step_x:step_x, step_y:step_y}};
    if (step_x) document.getElementById('p-offset-x').value = step_x;
    if (step_y) document.getElementById('p-offset-y').value = step_y;
    document.getElementById('tres-inline').style.display = 'none';
    document.getElementById('cuad-inline').style.display = 'none';
    _advanceToStep2();
  }}
}}

function confirmTresbolillo() {{
  var diam = parseFloat(document.getElementById('p-diam').value);
  var dist = parseFloat(document.getElementById('p-dist').value);
  if (isNaN(diam) || diam <= 0) {{ alert('Diametro invalido.'); return; }}
  if (isNaN(dist) || dist <= 0) {{ alert('Distancia entre centros invalida.'); return; }}
  selectedPattern = {{mode:'tresbolillo', name:'Tresbolillo d=' + diam + ' sep=' + dist,
                      ptype:'tresbolillo', file_path:null, step_x:null, step_y:null}};
  _advanceToStep2();
}}

function cuadShapeChanged() {{
  var shape = document.getElementById('cuad-shape').value;
  document.getElementById('cuad-size-label').textContent = shape === 'circle' ? 'Diametro mm' : 'Lado mm';
}}

function confirmCuadriculado() {{
  var shape = document.getElementById('cuad-shape').value;
  var size  = parseFloat(document.getElementById('cuad-size').value);
  var ox    = parseFloat(document.getElementById('cuad-ox').value);
  var oy    = parseFloat(document.getElementById('cuad-oy').value);
  if (isNaN(size) || size <= 0) {{ alert('Tamano invalido.'); return; }}
  if (isNaN(ox)   || ox <= 0)   {{ alert('Offset X invalido.'); return; }}
  if (isNaN(oy)   || oy <= 0)   {{ alert('Offset Y invalido.'); return; }}
  var shapeName = shape === 'circle' ? 'Circ d=' + size : 'Cuad l=' + size;
  selectedPattern = {{mode:'cuadriculado', name:'Cuadriculado ' + shapeName,
                      ptype:'cuadriculado', file_path:null,
                      hole_shape:shape, hole_size_mm:size,
                      offset_x_mm:ox, offset_y_mm:oy,
                      step_x:null, step_y:null}};
  _advanceToStep2();
}}

function _advanceToStep2() {{
  _stepDone(0);
  var s2 = document.getElementById('step2');
  if (s2.classList.contains('hidden')) {{
    s2.classList.remove('hidden');
    setTimeout(function() {{ s2.scrollIntoView({{behavior:'smooth', block:'start'}}); }}, 60);
  }}
}}

function selectOutline() {{
  _stepDone(1);
  var s3 = document.getElementById('step3');
  if (s3.classList.contains('hidden')) {{
    s3.classList.remove('hidden');
    setTimeout(function() {{ s3.scrollIntoView({{behavior:'smooth', block:'start'}}); }}, 60);
  }}
}}

function _stepDone(idx) {{
  var bubbles = ['bubble-1','bubble-2','bubble-3'];
  var labels = ['label-1','label-2','label-3'];
  var conns = ['conn-1-2','conn-2-3'];
  for (var i=0; i<=idx; i++) {{
    document.getElementById(bubbles[i]).className = 'step-bubble done';
    document.getElementById(labels[i]).className = 'step-label done';
    if (i < conns.length) document.getElementById(conns[i]).className = 'step-connector done';
  }}
  if (idx+1 < bubbles.length) {{
    document.getElementById(bubbles[idx+1]).className = 'step-bubble active';
    document.getElementById(labels[idx+1]).className = 'step-label active';
  }}
}}

function setDist(mode) {{
  distMode = mode;
  document.getElementById('lbl-centradas').className = mode==='centradas' ? 'checked-option' : '';
  document.getElementById('lbl-cortar').className   = mode==='cortar'    ? 'checked-option' : '';
}}

// ---- Add batch ----
function addBatch() {{
  var errEl = document.getElementById('batch-error');
  errEl.classList.add('hidden');
  try {{
    if (!selectedPattern) throw new Error('Selecciona un patron primero.');
    var ancho   = parseFloat(document.getElementById('p-ancho').value);
    var alto    = parseFloat(document.getElementById('p-alto').value);
    var margen  = parseFloat(document.getElementById('p-margen').value);
    var mat     = document.getElementById('p-material').value.trim();
    var esp     = parseFloat(document.getElementById('p-espesor').value);
    var cant    = parseInt(document.getElementById('p-cantidad').value);
    if (isNaN(ancho)  || ancho  <= 0) throw new Error('Ancho invalido.');
    if (isNaN(alto)   || alto   <= 0) throw new Error('Alto invalido.');
    if (isNaN(margen) || margen <  0) throw new Error('Margen invalido.');
    if (!mat)                          throw new Error('Selecciona un material del dropdown.');
    if (isNaN(esp)    || esp    <= 0) throw new Error('Espesor invalido — selecciona un material del dropdown.');
    if (isNaN(cant)   || cant   <= 0) throw new Error('Cantidad invalida.');

    var batch = {{
      panel_mode: selectedPattern.mode,
      preset_name: selectedPattern.name,
      pattern_type: selectedPattern.ptype,
      cut_partial_figures: distMode === 'cortar',
      margin_mm: margen,
      material: mat,
      thickness_mm: esp,
      sheet_sizes: [[ancho, alto, cant]],
      hole_diameter_mm: 0, hole_distance_mm: 0,
      pattern_dxf_path: null, step_x_mm: null, step_y_mm: null
    }};

    if (selectedPattern.mode === 'tresbolillo') {{
      var diam = parseFloat(document.getElementById('p-diam').value);
      var dist = parseFloat(document.getElementById('p-dist').value);
      if (isNaN(diam) || diam <= 0) throw new Error('Diametro invalido.');
      if (isNaN(dist) || dist <= 0) throw new Error('Distancia invalida.');
      batch.hole_diameter_mm = diam;
      batch.hole_distance_mm = dist;
    }} else if (selectedPattern.mode === 'cuadriculado') {{
      batch.hole_shape = selectedPattern.hole_shape;
      batch.hole_size_mm = selectedPattern.hole_size_mm;
      batch.offset_x_mm = selectedPattern.offset_x_mm;
      batch.offset_y_mm = selectedPattern.offset_y_mm;
    }} else {{
      var ox = parseFloat(document.getElementById('p-offset-x').value);
      var oy = parseFloat(document.getElementById('p-offset-y').value);
      if (isNaN(ox) || ox <= 0) throw new Error('Offset X invalido.');
      if (isNaN(oy) || oy <= 0) throw new Error('Offset Y invalido.');
      if (!selectedPattern.file_path) throw new Error('El patron DXF no tiene ruta de archivo. Recargalo desde /admin.');
      batch.pattern_dxf_path = selectedPattern.file_path;
      batch.step_x_mm = ox;
      batch.step_y_mm = oy;
    }}
    batches.push(batch);
    renderBatchTable();
  }} catch(e) {{
    errEl.textContent = e.message || String(e);
    errEl.classList.remove('hidden');
  }}
}}

function removeBatch(idx) {{
  batches.splice(idx, 1);
  renderBatchTable();
}}

function renderBatchTable() {{
  var tbody   = document.getElementById('batch-tbody');
  var section = document.getElementById('section-batches');
  tbody.innerHTML = '';
  if (!batches.length) {{ section.classList.add('hidden'); return; }}
  section.classList.remove('hidden');
  var total = 0;
  batches.forEach(function(b, i) {{
    var sz = b.sheet_sizes[0];
    total += sz[2];
    var patDesc;
    if (b.panel_mode === 'tresbolillo') {{
      patDesc = b.preset_name + ' <span style="color:#aaa;font-size:11px">d=' + b.hole_diameter_mm + ' sep=' + b.hole_distance_mm + '</span>';
    }} else if (b.panel_mode === 'cuadriculado') {{
      patDesc = b.preset_name + ' <span style="color:#aaa;font-size:11px">' + b.hole_shape + ' ' + b.hole_size_mm + 'mm ox=' + b.offset_x_mm + ' oy=' + b.offset_y_mm + '</span>';
    }} else {{
      patDesc = b.preset_name + ' <span style="color:#aaa;font-size:11px">DXF ' + b.step_x_mm + ',' + b.step_y_mm + '</span>';
    }}
    var tr = document.createElement('tr');
    tr.innerHTML =
      '<td>' + patDesc + '</td>' +
      '<td>Rectangulo simple</td>' +
      '<td style="font-family:monospace">' + sz[0] + ' x ' + sz[1] + ' mm</td>' +
      '<td>' + b.margin_mm + ' mm</td>' +
      '<td>' + b.material + ' / ' + b.thickness_mm + ' mm</td>' +
      '<td>' + sz[2] + '</td>' +
      '<td><button class="btn-delete" onclick="removeBatch(' + i + ')">Borrar</button></td>';
    tbody.appendChild(tr);
  }});
  document.getElementById('generate-count').textContent =
    batches.length + ' lote' + (batches.length > 1 ? 's' : '') + ' · ' + total + ' unidades en total';
}}

function submitGenerate() {{
  if (!batches.length) {{ alert('Agrega al menos un lote antes de generar.'); return; }}
  document.getElementById('f-customer').value = 'CLIENTE-DEMO';
  document.getElementById('f-job').value = 'Panel pedido';
  document.getElementById('f-obs').value = '';
  document.getElementById('f-batches').value = JSON.stringify(batches);
  document.getElementById('generate-form').submit();
}}

function copyPasteBlock(btn, textareaId) {{
  var text = document.getElementById(textareaId).value;
  navigator.clipboard.writeText(text).then(function() {{
    var orig = btn.textContent;
    btn.textContent = '✓ Copiado';
    btn.classList.add('copied');
    setTimeout(function() {{
      btn.textContent = orig;
      btn.classList.remove('copied');
    }}, 2000);
  }}).catch(function() {{
    alert('No se pudo copiar al portapapeles. Selectá el texto manualmente.');
  }});
}}

async function saveDxfAs(url, suggestedName) {{
  if (window.showSaveFilePicker) {{
    try {{
      const handle = await window.showSaveFilePicker({{
        suggestedName: suggestedName,
        types: [{{ description: 'Archivo DXF', accept: {{ 'application/dxf': ['.dxf'] }} }}]
      }});
      const resp = await fetch(url);
      const writable = await handle.createWritable();
      await writable.write(await resp.blob());
      await writable.close();
      return;
    }} catch (e) {{
      if (e.name === 'AbortError') return;
      // API falló — fallback a descarga normal
    }}
  }}
  // Fallback para browsers sin showSaveFilePicker
  const a = document.createElement('a');
  a.href = url;
  a.download = suggestedName;
  document.body.appendChild(a);
  a.click();
  a.remove();
}}


</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# render_admin — admin page for pattern management
# ---------------------------------------------------------------------------

def render_admin() -> str:
    """Render the admin page for pattern management."""
    try:
        patterns = get_pattern_library_patterns()
    except Exception:
        patterns = {}

    rows_html = ""
    # Tresbolillo — built-in, no delete
    tres_url = _thumbnail_url("Tresbolillo")
    tres_img = (
        f'<img src="{tres_url}" style="width:80px;height:80px;object-fit:cover;border-radius:6px">'
        if tres_url else
        '<div style="width:80px;height:80px;background:#c8d5de;border-radius:6px;'
        'display:flex;align-items:center;justify-content:center">'
        '<svg width="56" height="56" viewBox="0 0 100 100" opacity=".6">'
        '<circle cx="20" cy="20" r="8" fill="#7a9aaa"/><circle cx="50" cy="20" r="8" fill="#7a9aaa"/>'
        '<circle cx="80" cy="20" r="8" fill="#7a9aaa"/><circle cx="35" cy="46" r="8" fill="#7a9aaa"/>'
        '<circle cx="65" cy="46" r="8" fill="#7a9aaa"/><circle cx="20" cy="72" r="8" fill="#7a9aaa"/>'
        '<circle cx="50" cy="72" r="8" fill="#7a9aaa"/><circle cx="80" cy="72" r="8" fill="#7a9aaa"/>'
        '</svg></div>'
    )
    rows_html += f"""
    <tr>
      <td>{tres_img}</td>
      <td><strong>Tresbolillo</strong><br>
          <span style="font-size:11px;color:#aaa;font-style:italic">Motor nativo — parametros variables</span></td>
      <td><span class="type-badge type-native">Nativo</span></td>
      <td><span class="dimmed">No se puede borrar</span></td>
    </tr>"""

    for name, info in patterns.items():
        safe_name = escape(name)
        thumb_url = _thumbnail_url(name)
        thumb_html = (
            f'<img src="{thumb_url}" style="width:80px;height:80px;object-fit:cover;border-radius:6px">'
            if thumb_url else
            '<div style="width:80px;height:80px;background:#d0cfe0;border-radius:6px"></div>'
        )
        file_path = escape(str(info.get("file_path", "")))
        step_x = escape(str(info.get("step_x", 84)))
        step_y = escape(str(info.get("step_y", 84)))
        name_json = json.dumps(name)
        is_restricted = bool(info.get("restricted", False))
        restricted_reason = escape(str(info.get("restricted_reason", "")))
        restricted_badge_html = (
            f'<span class="restricted-badge" title="{restricted_reason}">Modo restringido</span>'
            if is_restricted else ""
        )
        restricted_note_html = (
            f'<br><span style="font-size:10px;color:#e65100">{restricted_reason}</span>'
            if is_restricted and restricted_reason else ""
        )
        file_path_json = json.dumps(info.get("file_path", ""))
        convert_btn_html = (
            f'<button class="btn-action btn-convert" '
            f'data-pattern-name="{safe_name}" '
            f'data-file-path="{escape(str(info.get("file_path", "")))}" '
            f'data-step-x="{info.get("step_x", 84)}" '
            f'data-step-y="{info.get("step_y", 84)}" '
            f'onclick="openSplineConverter(this.dataset.patternName, this.dataset.filePath, this)">'
            f'Convertir splines</button>'
            if is_restricted else ""
        )
        rows_html += f"""
    <tr id="pattern-row-{escape(name.replace(' ', '_'))}">
      <td>{thumb_html}</td>
      <td><strong>{safe_name}</strong>{restricted_badge_html}<br>
          <span style="font-size:11px;color:#aaa">offset {step_x} &times; {step_y} mm</span>{restricted_note_html}</td>
      <td><span class="type-badge type-dxf">DXF</span></td>
      <td>
        {convert_btn_html}
        <button class="btn-action btn-del" data-pattern-name="{safe_name}" onclick="deletePattern(this.dataset.patternName, this)">Borrar</button>
      </td>
    </tr>"""

    total = len(patterns) + 1  # +1 for Tresbolillo

    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Nextango — Admin patrones</title>
  <style>
{_COMMON_CSS}
    .page-title {{ font-size:22px; font-weight:700; color:var(--brand); margin-bottom:24px; }}
    .patterns-table {{ width:100%; border-collapse:collapse; font-size:13px; }}
    .patterns-table thead tr {{ background:#e8f4f8; }}
    .patterns-table th {{ padding:9px 12px; text-align:left; font-size:11px; font-weight:700; letter-spacing:.7px; text-transform:uppercase; color:var(--brand); border-bottom:2px solid #c5dde8; }}
    .patterns-table td {{ padding:12px; border-bottom:1px solid #eef1f4; color:#333; vertical-align:middle; }}
    .patterns-table tr:last-child td {{ border-bottom:none; }}
    .patterns-table tr:hover td {{ background:#f5fafe; }}
    .type-badge {{ display:inline-block; padding:3px 9px; border-radius:10px; font-size:11px; font-weight:700; letter-spacing:.5px; text-transform:uppercase; }}
    .type-native {{ background:#e8f4f8; color:var(--brand); }}
    .type-dxf {{ background:#f0ece8; color:#7a5c3a; }}
    .restricted-badge {{ display:inline-block; margin-left:6px; padding:2px 8px; border-radius:10px; font-size:10px; font-weight:700; letter-spacing:.4px; text-transform:uppercase; background:#fff3e0; color:#e65100; border:1px solid #ffcc80; }}
    .btn-action {{ padding:5px 12px; border-radius:4px; font-size:12px; cursor:pointer; font-weight:600; border:1px solid; transition:background .12s; margin-right:4px; }}
    .btn-del {{ background:#fff; border-color:#e57373; color:#e57373; }}
    .btn-del:hover {{ background:#fff0f0; }}
    .btn-convert {{ background:#fff3e0; border-color:#e65100; color:#e65100; }}
    .btn-convert:hover {{ background:#ffe0b2; }}
    /* Spline converter modal */
    .sc-overlay {{ display:none; position:fixed; inset:0; background:rgba(0,0,0,.55); z-index:1000; align-items:center; justify-content:center; }}
    .sc-overlay.active {{ display:flex; }}
    .sc-modal {{ background:#fff; border-radius:10px; box-shadow:0 8px 40px rgba(0,0,0,.3); width:92vw; max-width:1100px; max-height:92vh; display:flex; flex-direction:column; overflow:hidden; }}
    .sc-header {{ padding:16px 24px; border-bottom:1px solid #e0e6ed; display:flex; align-items:center; justify-content:space-between; }}
    .sc-title {{ font-size:16px; font-weight:700; color:var(--brand); }}
    .sc-close {{ background:none; border:none; font-size:22px; cursor:pointer; color:#888; line-height:1; padding:0 4px; }}
    .sc-close:hover {{ color:#333; }}
    .sc-body {{ flex:1; overflow:auto; padding:20px 24px; }}
    .sc-layer-controls {{ display:flex; gap:20px; margin-bottom:10px; font-size:13px; color:#444; user-select:none; }}
    .sc-layer-controls label {{ display:flex; align-items:center; gap:6px; cursor:pointer; font-weight:600; }}
    .sc-canvas-wrap {{ border:1px solid #d0d8e0; border-radius:6px; overflow:hidden; background:#f7f8fa; position:relative; height:400px; cursor:grab; }}
    .sc-canvas-wrap.loading {{ background:#f0f2f5; }}
    .sc-canvas-wrap .sc-placeholder {{ position:absolute; inset:0; display:flex; align-items:center; justify-content:center; color:#aaa; font-size:13px; }}
    .sc-canvas-wrap svg {{ width:100%; height:100%; display:block; }}
    .sc-controls {{ padding:8px 0; display:flex; align-items:center; gap:8px; font-size:12px; color:#888; }}
    .sc-stats {{ background:#f0f7ff; border:1px solid #b3d4f0; border-radius:6px; padding:12px 16px; margin-top:14px; font-size:13px; }}
    .sc-editor-hint {{ margin-top:8px; font-size:12px; color:#666; background:#f9f9f9; border:1px dashed #ccc; border-radius:4px; padding:7px 12px; }}
    .sc-footer {{ padding:14px 24px; border-top:1px solid #e0e6ed; display:flex; align-items:center; justify-content:flex-end; gap:12px; }}
    .btn-sc-cancel {{ padding:9px 22px; background:#fff; border:1px solid #ccc; border-radius:5px; font-size:13px; cursor:pointer; color:#555; }}
    .btn-sc-cancel:hover {{ background:#f5f5f5; }}
    .btn-sc-discard {{ padding:9px 22px; background:#fff; border:1px solid #e65100; border-radius:5px; font-size:13px; cursor:pointer; color:#e65100; }}
    .btn-sc-discard:hover {{ background:#fff3e0; }}
    .btn-sc-confirm {{ padding:9px 22px; background:var(--brand); border:none; border-radius:5px; font-size:13px; font-weight:700; cursor:pointer; color:#fff; letter-spacing:.5px; }}
    .btn-sc-confirm:hover {{ background:var(--brand-dark); }}
    .btn-sc-confirm:disabled {{ opacity:.5; cursor:not-allowed; }}
    .file-input-row {{ display:flex; align-items:center; gap:0; border:1px solid #ccc; border-radius:5px; overflow:hidden; }}
    .file-input-text {{ flex:1; padding:8px 10px; font-size:13px; color:#aaa; background:#fafafa; border:none; outline:none; width:auto; }}
    .file-browse-btn {{ padding:8px 16px; background:var(--brand); color:#fff; font-size:13px; font-weight:600; border:none; cursor:pointer; white-space:nowrap; transition:background .12s; }}
    .file-browse-btn:hover {{ background:var(--brand-dark); }}
    .btn-upload {{ display:inline-block; padding:11px 28px; background:var(--brand); color:#fff; font-size:14px; font-weight:700; letter-spacing:.8px; text-transform:uppercase; border:none; border-radius:6px; cursor:pointer; margin-top:8px; transition:background .15s; }}
    .btn-upload:hover {{ background:var(--brand-dark); }}
    .form-divider {{ border:none; border-top:1px solid #eef1f4; margin:20px 0; }}
    .feedback-area {{ margin-top:20px; border-radius:6px; padding:14px 18px; font-size:13px; display:flex; align-items:flex-start; gap:10px; }}
    .fb-loading {{ background:#e8f4f8; border:1px solid #a8d0e0; color:var(--brand); }}
    .fb-success {{ background:#e8f5e9; border:1px solid #a5d6a7; color:#2e7d32; }}
    .fb-warning {{ background:#fff8e1; border:1px solid #ffe082; color:#e65100; }}
    .fb-error {{ background:#fdecea; border:1px solid #f5a5a0; color:var(--red); }}
    .feedback-icon {{ font-size:18px; flex-shrink:0; margin-top:1px; }}
    .feedback-text strong {{ display:block; margin-bottom:3px; }}
  </style>
</head>
<body>
{_topbar_html("admin")}
<div class="page-wrapper">
  <h1 class="page-title">Administracion de patrones</h1>

  <!-- Tabla de patrones existentes -->
  <div class="card">
    <div class="card-title" style="display:flex;justify-content:space-between">
      <span>Patrones registrados</span>
      <span style="font-size:12px;color:#888;font-weight:400;letter-spacing:0;text-transform:none">{total} patrones</span>
    </div>
    <table class="patterns-table">
      <thead>
        <tr>
          <th>Preview</th>
          <th>Nombre</th>
          <th>Tipo</th>
          <th>Acciones</th>
        </tr>
      </thead>
      <tbody id="patterns-tbody">{rows_html}</tbody>
    </table>
  </div>

  <!-- Formulario: cargar nuevo patron DXF -->
  <div class="card">
    <div class="card-title">Cargar nuevo patron DXF</div>

    <div class="form-row">
      <div class="form-group">
        <label for="admin-nombre">Nombre del patron</label>
        <input type="text" id="admin-nombre" placeholder="ej. Hexagono regular">
        <div class="field-hint">Nombre visible en la galeria del vendedor.</div>
      </div>
    </div>

    <div class="form-row">
      <div class="form-group">
        <label>Archivo DXF</label>
        <div class="file-input-row">
          <input class="file-input-text" type="text" id="admin-dxf-path" readonly
                 placeholder="Ningun archivo seleccionado">
          <button class="file-browse-btn" onclick="browseAdminDxf()">Examinar...</button>
        </div>
        <div class="field-hint">El archivo DXF debe contener una sola unidad repetible del patron.</div>
      </div>
    </div>

    <div class="form-row">
      <div class="form-group">
        <label for="admin-offset-x">Offset X mm</label>
        <input type="number" id="admin-offset-x" placeholder="ej: 84" step="0.1">
      </div>
      <div class="form-group">
        <label for="admin-offset-y">Offset Y mm</label>
        <input type="number" id="admin-offset-y" placeholder="ej: 84" step="0.1">
      </div>
      <div class="form-group"></div>
    </div>
    <div style="margin-top:-10px;margin-bottom:16px">
      <span class="field-hint">Distancia entre la celda DXF y la siguiente repeticion en cada eje.</span>
    </div>

    <hr class="form-divider">

    <div style="margin-bottom:16px">
      <label style="display:flex;align-items:center;gap:8px;cursor:pointer;font-size:13px;font-weight:600;color:#444;text-transform:none;letter-spacing:0">
        <input type="checkbox" id="admin-convert-circles" onchange="toggleCirclesParams()">
        Convertir polígonos circulares a círculos
      </label>
      <div class="field-hint" style="margin-left:22px">
        Detecta LWPOLYLINE cerradas que aproximan círculos (p.ej. de vectorizadores de imágenes) y las reemplaza por entidades CIRCLE.
      </div>
      <div id="circles-params" style="display:none;margin-top:10px;margin-left:22px;display:none">
        <span style="font-size:12px;color:#555;font-weight:700">Tolerancia (mm):</span>
        <input type="number" id="admin-circles-tol" value="0.5" step="0.05" min="0.01"
               style="width:70px;padding:4px 6px;font-size:12px;border:1px solid #ccc;border-radius:4px;margin:0 12px 0 6px">
        <span style="font-size:12px;color:#555;font-weight:700">Radio máx (mm):</span>
        <input type="number" id="admin-circles-rmax" value="200" step="10" min="1"
               style="width:80px;padding:4px 6px;font-size:12px;border:1px solid #ccc;border-radius:4px;margin:0 0 0 6px">
      </div>
    </div>

    <button class="btn-upload" onclick="uploadPattern()">CARGAR Y GENERAR PREVIEW</button>

    <div id="admin-feedback" class="hidden"></div>
  </div>

</div><!-- /page-wrapper -->

<!-- ============================================================ -->
<!-- MODAL: Convertir splines — canvas superpuesto + editor      -->
<!-- ============================================================ -->
<div class="sc-overlay" id="sc-overlay" onclick="scOverlayClick(event)">
  <div class="sc-modal" onclick="event.stopPropagation()">
    <div class="sc-header">
      <span class="sc-title">Convertir splines — Vista y editor</span>
      <button class="sc-close" onclick="closeSplineConverter()" title="Cerrar">&times;</button>
    </div>
    <div class="sc-body">
      <div id="sc-status-top" style="margin-bottom:12px"></div>
      <!-- Layer visibility toggles -->
      <div class="sc-layer-controls">
        <label><input type="checkbox" id="sc-show-orig" checked onchange="scRenderLayers()">
          <span style="color:#bbb">&#9632;</span> Mostrar original (gris)</label>
        <label><input type="checkbox" id="sc-show-conv" checked onchange="scRenderLayers()">
          <span style="color:#1a6fa8">&#9632;</span> Mostrar convertido (azul)</label>
      </div>
      <!-- Single overlay canvas -->
      <div class="sc-canvas-wrap loading" id="sc-canvas-wrap">
        <div class="sc-placeholder" id="sc-placeholder-msg">Cargando...</div>
        <svg id="sc-svg" xmlns="http://www.w3.org/2000/svg"
             style="width:100%;height:100%;display:none"
             tabindex="0">
          <g id="sc-layer-orig"></g>
          <g id="sc-layer-conv"></g>
          <g id="sc-layer-editor"></g>
          <g id="sc-layer-nodes"></g>
          <g id="sc-layer-preview"></g>
        </svg>
      </div>
      <div class="sc-controls">
        <span>Rueda = zoom &nbsp;|&nbsp; Arrastrar = paneo &nbsp;|&nbsp;
              Click entidad = seleccionar &nbsp;|&nbsp; Delete/Backspace = borrar</span>
      </div>
      <div id="sc-editor-hint" class="sc-editor-hint hidden"></div>
      <div id="sc-stats" class="sc-stats hidden"></div>
    </div>
    <div class="sc-footer">
      <button class="btn-sc-cancel" onclick="closeSplineConverter()">Cancelar</button>
      <button class="btn-sc-discard" id="sc-discard-btn" style="display:none"
              onclick="scDiscardEdits()">Descartar cambios</button>
      <button class="btn-sc-confirm" id="sc-confirm-btn" disabled
              onclick="confirmAndLoad()">Cargar patron convertido</button>
    </div>
  </div>
</div>

<script>
// ============================================================
// Spline Converter — state
// ============================================================
var _scPatternName = '';
var _scOrigPath    = '';
var _scConvPath    = '';
var _scStepX       = 84;
var _scStepY       = 84;

// SVG viewBox shared by both layers
var _scViewBox     = null;  // {{x, y, w, h}}

// Original SVG segments (for background layer, never changes)
var _scOrigSegments = [];  // [{{pts:[{{x,y}}...], isArc:false}}]

// Editor state
var _editEntities    = [];  // array of entity objects {{type,id,...}}
var _editOrigEntities= [];  // deep copy for discard
var _selectedId      = null;
var _freeNodes       = [];  // [{{x,y}}] — 0 or 2 elements

// Pan/zoom state (applied to the SVG viewBox)
var _svgPan = {{tx:0, ty:0, scale:1}};
var _svgDragging = false, _svgDragStart = null, _svgDragPanStart = null;
var _svgMouseDown = false;
var _svgMouseDownPos = null;

// ============================================================
// Open / close
// ============================================================
function openSplineConverter(patternName, filePath, btn) {{
  _scPatternName = patternName;
  _scOrigPath    = filePath;
  _scStepX = parseFloat(btn.dataset.stepX) || 84;
  _scStepY = parseFloat(btn.dataset.stepY) || 84;
  _scConvPath    = '';
  _editEntities  = [];
  _editOrigEntities = [];
  _selectedId    = null;
  _freeNodes     = [];

  // Reset UI
  document.getElementById('sc-overlay').classList.add('active');
  document.getElementById('sc-confirm-btn').disabled = true;
  document.getElementById('sc-discard-btn').style.display = 'none';
  document.getElementById('sc-stats').classList.add('hidden');
  document.getElementById('sc-editor-hint').classList.add('hidden');
  _setScStatus('');

  var wrap = document.getElementById('sc-canvas-wrap');
  wrap.classList.add('loading');
  document.getElementById('sc-svg').style.display = 'none';
  document.getElementById('sc-placeholder-msg').style.display = 'flex';
  document.getElementById('sc-placeholder-msg').textContent = 'Cargando preview original...';

  // Step 1: fetch original SVG for bounding box + background rendering
  fetch('/api/patterns/preview_dxf?path=' + encodeURIComponent(filePath) + '&mode=original')
    .then(function(r) {{ return r.text(); }})
    .then(function(svgText) {{
      _scOrigSegments = _parseSvgPaths(svgText);
      _scViewBox      = _parseSvgViewBox(svgText);
      document.getElementById('sc-placeholder-msg').textContent = 'Convirtiendo splines...';
      // Step 2: convert
      return fetch('/api/patterns/convert_splines', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{dxf_path: filePath, tolerance: 0.1}})
      }});
    }})
    .then(function(r) {{ return r.json(); }})
    .then(function(d) {{
      if (!d.ok) {{
        _showPlaceholderError('Error al convertir: ' + (d.error || '?'));
        _setScStatus('error', 'Error al convertir: ' + (d.error || '?'));
        return;
      }}
      _scConvPath = d.output_path;
      // Show stats
      var statsEl = document.getElementById('sc-stats');
      statsEl.classList.remove('hidden');
      statsEl.innerHTML =
        '<strong>Resultado de la conversion:</strong> ' +
        d.converted_count + ' curva(s) &rarr; ' +
        d.arc_count + ' arco(s) + ' + d.line_count + ' linea(s).' +
        ' <code style="font-size:11px">' + d.output_path + '</code>';

      // Step 3: load editable entities from converted DXF
      return fetch('/api/patterns/entities?path=' + encodeURIComponent(d.output_path));
    }})
    .then(function(r) {{ return r ? r.json() : null; }})
    .then(function(data) {{
      if (!data) return;
      if (!data.entities) {{
        _showPlaceholderError('Error al cargar entidades.');
        return;
      }}
      // Union viewBox with converted paths
      var convSegments = _entitiesAsSegments(data.entities);
      if (_scViewBox && convSegments.length) {{
        var allPts = [];
        _scOrigSegments.forEach(function(s) {{ s.pts.forEach(function(p){{ allPts.push(p); }}); }});
        convSegments.forEach(function(s) {{ s.pts.forEach(function(p){{ allPts.push(p); }}); }});
        if (allPts.length) {{
          var xs = allPts.map(function(p){{return p.x;}});
          var ys = allPts.map(function(p){{return p.y;}});
          var minX = Math.min.apply(null,xs), maxX = Math.max.apply(null,xs);
          var minY = Math.min.apply(null,ys), maxY = Math.max.apply(null,ys);
          var pw = maxX-minX||1, ph = maxY-minY||1;
          var pad = Math.max(pw,ph)*0.05;
          _scViewBox = {{x:minX-pad, y:minY-pad, w:pw+2*pad, h:ph+2*pad}};
        }}
      }}

      _editEntities     = data.entities.map(function(e,i){{ return Object.assign({{id:'e'+i}}, e); }});
      _editOrigEntities = JSON.parse(JSON.stringify(_editEntities));

      _svgPan = {{tx:0, ty:0, scale:1}};
      wrap.classList.remove('loading');
      document.getElementById('sc-placeholder-msg').style.display = 'none';
      var svgEl = document.getElementById('sc-svg');
      svgEl.style.display = '';
      svgEl.focus();
      _scSetViewBox();
      _scRenderOrigLayer();
      scRenderLayers();
      _scAttachSvgInteraction();
      document.getElementById('sc-confirm-btn').disabled = false;
      document.getElementById('sc-discard-btn').style.display = '';
    }})
    .catch(function(e) {{
      _showPlaceholderError('Error: ' + e);
      _setScStatus('error', String(e));
    }});
}}

function closeSplineConverter() {{
  document.getElementById('sc-overlay').classList.remove('active');
  _scConvPath = '';
  _editEntities = [];
  _freeNodes = [];
  _selectedId = null;
}}

function scOverlayClick(e) {{
  if (e.target === document.getElementById('sc-overlay')) closeSplineConverter();
}}

// ============================================================
// SVG viewBox helper
// ============================================================
function _scSetViewBox() {{
  if (!_scViewBox) return;
  var svg = document.getElementById('sc-svg');
  svg.setAttribute('viewBox', _scViewBox.x+' '+_scViewBox.y+' '+_scViewBox.w+' '+_scViewBox.h);
}}

// ============================================================
// Parse original SVG paths into point segments (for grey layer)
// ============================================================
function _parseSvgPaths(svgText) {{
  var segs = [];
  var re = /d="([^"]+)"/g, m;
  while ((m = re.exec(svgText)) !== null) {{
    var pts = [];
    var cmds = m[1].match(/[ML][^ML]*/g) || [];
    cmds.forEach(function(cmd) {{
      var nums = cmd.slice(1).trim().split(/[\\s,]+/).map(Number);
      if (nums.length >= 2 && !isNaN(nums[0]) && !isNaN(nums[1])) {{
        pts.push({{x:nums[0], y:nums[1]}});
      }}
    }});
    if (pts.length >= 2) segs.push({{pts:pts}});
  }}
  return segs;
}}

function _parseSvgViewBox(svgText) {{
  var m = svgText.match(/viewBox="([^"]+)"/);
  if (!m) return null;
  var parts = m[1].trim().split(/[\\s,]+/).map(Number);
  if (parts.length < 4) return null;
  return {{x:parts[0], y:parts[1], w:parts[2], h:parts[3]}};
}}

// ============================================================
// Convert entities to point segments for viewBox calculation
// ============================================================
function _entitiesAsSegments(entities) {{
  var segs = [];
  entities.forEach(function(e) {{
    if (e.type === 'line') {{
      segs.push({{pts:[{{x:e.x1,y:e.y1}},{{x:e.x2,y:e.y2}}]}});
    }} else if (e.type === 'arc') {{
      segs.push({{pts:_arcPts(e.cx,e.cy,e.radius,e.startAngle,e.endAngle)}});
    }}
  }});
  return segs;
}}

function _arcPts(cx, cy, r, startDeg, endDeg) {{
  var pts = [];
  var a0 = startDeg % 360, a1 = endDeg % 360;
  if (a1 <= a0) a1 += 360;
  var span = a1 - a0;
  var n = Math.max(8, Math.ceil(span / 5));
  for (var i = 0; i <= n; i++) {{
    var a = (a0 + span * i / n) * Math.PI / 180;
    pts.push({{x: cx + r * Math.cos(a), y: cy + r * Math.sin(a)}});
  }}
  return pts;
}}

// ============================================================
// Render: grey original layer (static, never changes)
// ============================================================
function _scRenderOrigLayer() {{
  var g = document.getElementById('sc-layer-orig');
  var sw = (_scViewBox ? Math.max(_scViewBox.w, _scViewBox.h) * 0.003 : 0.5);
  var paths = [];
  _scOrigSegments.forEach(function(seg) {{
    if (seg.pts.length < 2) return;
    // pts already in SVG-space (Y-flipped by _dxf_to_svg) — use directly
    var d = seg.pts.map(function(p,i) {{
      return (i===0?'M':'L') + p.x.toFixed(4) + ',' + p.y.toFixed(4);
    }}).join(' ');
    paths.push('<path d="'+d+'" fill="none" stroke="#bbb" stroke-width="'+sw.toFixed(4)+'" opacity="0.5" stroke-linecap="round"/>');
  }});
  g.innerHTML = paths.join('');
}}

// ============================================================
// Render: blue converted layer + editor highlights
// ============================================================
function scRenderLayers() {{
  var showOrig = document.getElementById('sc-show-orig').checked;
  var showConv = document.getElementById('sc-show-conv').checked;
  document.getElementById('sc-layer-orig').style.display = showOrig ? '' : 'none';

  if (!showConv) {{
    document.getElementById('sc-layer-conv').style.display = 'none';
    document.getElementById('sc-layer-editor').style.display = 'none';
  }} else {{
    document.getElementById('sc-layer-conv').style.display = '';
    document.getElementById('sc-layer-editor').style.display = '';
    _scRenderConvLayer();
  }}
  _scRenderNodes();
}}

function _scRenderConvLayer() {{
  var g = document.getElementById('sc-layer-conv');
  var sw = (_scViewBox ? Math.max(_scViewBox.w, _scViewBox.h) * 0.003 : 0.5);
  var vbH = _scViewBox ? _scViewBox.y + _scViewBox.h : 0;
  var paths = [];
  _editEntities.forEach(function(e) {{
    var isSelected = (e.id === _selectedId);
    var color  = isSelected ? '#cc0000' : '#1a6fa8';
    var swidth = isSelected ? (sw * 2.5).toFixed(4) : sw.toFixed(4);
    var extra  = isSelected ? ' stroke-dasharray=""' : '';
    var d = _entityToSvgD(e, vbH);
    if (!d) return;
    paths.push(
      '<path d="'+d+'" fill="none" stroke="'+color+'" stroke-width="'+swidth+'"'+extra+
      ' stroke-linecap="round" cursor="pointer"'+
      ' data-eid="'+e.id+'" onclick="scEntityClick(this.dataset.eid)" />'
    );
    // Wider invisible hit-target
    paths.push(
      '<path d="'+d+'" fill="none" stroke="transparent" stroke-width="'+(sw*6).toFixed(4)+'"'+
      ' cursor="pointer" data-eid="'+e.id+'" onclick="scEntityClick(this.dataset.eid)" />'
    );
  }});
  g.innerHTML = paths.join('');
}}

function _entityToSvgD(e, vbH) {{
  function sy(y) {{ return vbH - (y - (_scViewBox ? _scViewBox.y : 0)); }}
  if (e.type === 'line') {{
    return 'M'+e.x1.toFixed(4)+','+sy(e.y1).toFixed(4)+
           ' L'+e.x2.toFixed(4)+','+sy(e.y2).toFixed(4);
  }}
  if (e.type === 'arc') {{
    var pts = _arcPts(e.cx, e.cy, e.radius, e.startAngle, e.endAngle);
    if (pts.length < 2) return null;
    var d = pts.map(function(p,i){{
      return (i===0?'M':'L')+p.x.toFixed(4)+','+sy(p.y).toFixed(4);
    }}).join(' ');
    return d;
  }}
  return null;
}}

// ============================================================
// Render: free nodes (red dots) and arc preview (green dashed)
// ============================================================
function _scRenderNodes() {{
  var gN = document.getElementById('sc-layer-nodes');
  var r = (_scViewBox ? Math.max(_scViewBox.w, _scViewBox.h) * 0.012 : 2);
  var vbH = _scViewBox ? _scViewBox.y + _scViewBox.h : 0;
  function sy(y) {{ return vbH - (y - (_scViewBox ? _scViewBox.y : 0)); }}
  var circles = _freeNodes.map(function(n) {{
    return '<circle cx="'+n.x.toFixed(4)+'" cy="'+sy(n.y).toFixed(4)+
           '" r="'+r.toFixed(4)+'" fill="#cc0000" stroke="#fff" stroke-width="'+(r*0.3).toFixed(4)+'"/>';
  }});
  gN.innerHTML = circles.join('');
}}

function _scRenderPreview(mouseX, mouseY) {{
  var gP = document.getElementById('sc-layer-preview');
  if (_freeNodes.length !== 2 || !_scViewBox) {{ gP.innerHTML = ''; return; }}
  var p3 = _svgToModel(mouseX, mouseY);
  var arc = arcThrough3Points(_freeNodes[0], p3, _freeNodes[1]);
  if (!arc) {{ gP.innerHTML = ''; return; }}
  // Determine direction (CCW vs CW) via cross-product of p1->p3 and p1->p2
  var crossZ = (_freeNodes[1].x - _freeNodes[0].x) * (p3.y - _freeNodes[0].y)
             - (_freeNodes[1].y - _freeNodes[0].y) * (p3.x - _freeNodes[0].x);
  var sweep = (crossZ < 0) ? 1 : 0;  // SVG: sweep=1 CW
  var vbH = _scViewBox.y + _scViewBox.h;
  function sy(y) {{ return vbH - (y - _scViewBox.y); }}
  // Start point (freeNodes[0]) and end point (freeNodes[1])
  var x1 = _freeNodes[0].x, y1 = _freeNodes[0].y;
  var x2 = _freeNodes[1].x, y2 = _freeNodes[1].y;
  var r  = arc.radius;
  // Large arc flag: angle span > 180 deg
  var angleDiff = arc.endAngle - arc.startAngle;
  if (angleDiff < 0) angleDiff += 360;
  var largeArc = (angleDiff > 180) ? 1 : 0;
  var d = 'M'+x1.toFixed(4)+','+sy(y1).toFixed(4)+
          ' A'+r.toFixed(4)+','+r.toFixed(4)+' 0 '+largeArc+' '+sweep+
          ' '+x2.toFixed(4)+','+sy(y2).toFixed(4);
  var sw = Math.max(_scViewBox.w, _scViewBox.h) * 0.003;
  gP.innerHTML = '<path d="'+d+'" fill="none" stroke="#2e7d32" stroke-width="'+(sw*1.5).toFixed(4)+
                 '" stroke-dasharray="'+(sw*4).toFixed(4)+','+(sw*3).toFixed(4)+
                 '" stroke-linecap="round"/>';
}}

// ============================================================
// Coordinate conversion: SVG screen px → model coords
// ============================================================
function _svgToModel(screenX, screenY) {{
  var svg = document.getElementById('sc-svg');
  var rect = svg.getBoundingClientRect();
  // SVG viewBox → screen mapping
  if (!_scViewBox) return {{x:0,y:0}};
  var scaleX = rect.width  / _scViewBox.w;
  var scaleY = rect.height / _scViewBox.h;
  var modelX = _scViewBox.x + (screenX - rect.left) / scaleX;
  var modelSvgY = _scViewBox.y + (screenY - rect.top)  / scaleY;
  // SVG Y is flipped relative to DXF Y
  var vbH = _scViewBox.y + _scViewBox.h;
  var modelY = vbH - (modelSvgY - _scViewBox.y);
  return {{x: modelX, y: modelY}};
}}

// ============================================================
// Pan/zoom via SVG viewBox manipulation
// ============================================================
var _scInteractionBound = false;
function _scAttachSvgInteraction() {{
  if (_scInteractionBound) return;
  _scInteractionBound = true;
  var svg = document.getElementById('sc-svg');

  svg.addEventListener('wheel', function(e) {{
    e.preventDefault();
    if (!_scViewBox) return;
    var factor = e.deltaY < 0 ? 0.88 : 1.14;
    var rect = svg.getBoundingClientRect();
    var mx = _scViewBox.x + (e.clientX - rect.left) / rect.width  * _scViewBox.w;
    var my = _scViewBox.y + (e.clientY - rect.top)  / rect.height * _scViewBox.h;
    _scViewBox.w *= factor; _scViewBox.h *= factor;
    _scViewBox.x = mx - (e.clientX - rect.left) / rect.width  * _scViewBox.w;
    _scViewBox.y = my - (e.clientY - rect.top)  / rect.height * _scViewBox.h;
    _scSetViewBox();
  }}, {{passive: false}});

  svg.addEventListener('mousedown', function(e) {{
    if (e.button !== 0) return;
    _svgMouseDown = true;
    _svgMouseDownPos = {{x: e.clientX, y: e.clientY}};
    _svgDragStart = {{x: e.clientX, y: e.clientY}};
    _svgDragPanStart = _scViewBox ? {{x:_scViewBox.x, y:_scViewBox.y}} : {{x:0,y:0}};
    _svgDragging = false;
    svg.style.cursor = 'grabbing';
  }});

  window.addEventListener('mousemove', function(e) {{
    if (!_svgMouseDown || !_scViewBox) return;
    var dx = e.clientX - _svgDragStart.x;
    var dy = e.clientY - _svgDragStart.y;
    if (!_svgDragging && (Math.abs(dx) > 3 || Math.abs(dy) > 3)) {{
      _svgDragging = true;
    }}
    if (_svgDragging) {{
      var rect = svg.getBoundingClientRect();
      var sx = _scViewBox.w / rect.width;
      var sy2 = _scViewBox.h / rect.height;
      _scViewBox.x = _svgDragPanStart.x - dx * sx;
      _scViewBox.y = _svgDragPanStart.y - dy * sy2;
      _scSetViewBox();
    }}
    // Arc preview
    if (_freeNodes.length === 2) {{
      _scRenderPreview(e.clientX, e.clientY);
    }}
  }});

  window.addEventListener('mouseup', function(e) {{
    if (!_svgMouseDown) return;
    _svgMouseDown = false;
    svg.style.cursor = _freeNodes.length === 2 ? 'crosshair' : 'grab';
    // Click on canvas (not on entity path, not a drag) — confirm arc
    if (!_svgDragging && _freeNodes.length === 2) {{
      _scConfirmArc(e.clientX, e.clientY);
    }}
  }});

  svg.addEventListener('keydown', function(e) {{
    if (e.key === 'Delete' || e.key === 'Backspace') {{
      e.preventDefault();
      scDeleteSelected();
    }}
  }});
}}

// ============================================================
// Entity click — select
// ============================================================
function scEntityClick(eid) {{
  if (_svgDragging) return;
  if (_freeNodes.length === 2) return;  // in arc-draw mode, ignore
  _selectedId = (eid === _selectedId) ? null : eid;
  _scRenderConvLayer();
  _scUpdateEditorHint();
}}

// ============================================================
// Delete selected entity
// ============================================================
function scDeleteSelected() {{
  if (!_selectedId) return;
  var idx = _editEntities.findIndex(function(e) {{ return e.id === _selectedId; }});
  if (idx < 0) return;
  var e = _editEntities[idx];
  // Compute endpoints
  var p1, p2;
  if (e.type === 'line') {{
    p1 = {{x: e.x1, y: e.y1}};
    p2 = {{x: e.x2, y: e.y2}};
  }} else if (e.type === 'arc') {{
    var a0 = e.startAngle * Math.PI / 180;
    var a1 = e.endAngle   * Math.PI / 180;
    p1 = {{x: e.cx + e.radius * Math.cos(a0), y: e.cy + e.radius * Math.sin(a0)}};
    p2 = {{x: e.cx + e.radius * Math.cos(a1), y: e.cy + e.radius * Math.sin(a1)}};
  }} else {{ return; }}
  _editEntities.splice(idx, 1);
  _selectedId = null;
  _freeNodes = [p1, p2];
  document.getElementById('sc-svg').style.cursor = 'crosshair';
  scRenderLayers();
  _scRenderNodes();
  _scUpdateEditorHint();
}}

// ============================================================
// 3-point arc math
// ============================================================
function arcThrough3Points(p1, p2, p3) {{
  var ax=p1.x, ay=p1.y, bx=p2.x, by=p2.y, cx=p3.x, cy=p3.y;
  var D = 2*(ax*(by-cy)+bx*(cy-ay)+cx*(ay-by));
  if (Math.abs(D) < 1e-10) return null;
  var ux = ((ax*ax+ay*ay)*(by-cy)+(bx*bx+by*by)*(cy-ay)+(cx*cx+cy*cy)*(ay-by))/D;
  var uy = ((ax*ax+ay*ay)*(cx-bx)+(bx*bx+by*by)*(ax-cx)+(cx*cx+cy*cy)*(bx-ax))/D;
  var radius = Math.hypot(ax-ux, ay-uy);
  var startAngle = Math.atan2(ay-uy, ax-ux)*180/Math.PI;
  var endAngle   = Math.atan2(cy-uy, cx-ux)*180/Math.PI;
  return {{cx:ux, cy:uy, radius:radius, startAngle:startAngle, endAngle:endAngle}};
}}

// ============================================================
// Confirm arc click
// ============================================================
function _scConfirmArc(screenX, screenY) {{
  var p3 = _svgToModel(screenX, screenY);
  var arc = arcThrough3Points(_freeNodes[0], p3, _freeNodes[1]);
  if (!arc) {{
    _setScStatus('warning', 'Puntos colineales — no se puede trazar el arco. Hace click en otro punto.');
    return;
  }}
  var newId = 'e_new_' + Date.now();
  _editEntities.push({{
    type: 'arc',
    cx: arc.cx, cy: arc.cy,
    radius: arc.radius,
    startAngle: arc.startAngle,
    endAngle: arc.endAngle,
    id: newId,
  }});
  _freeNodes = [];
  _selectedId = null;
  document.getElementById('sc-svg').style.cursor = 'grab';
  document.getElementById('sc-layer-preview').innerHTML = '';
  scRenderLayers();
  _scRenderNodes();
  _setScStatus('success', 'Arco agregado.');
  setTimeout(function(){{ _setScStatus(''); }}, 2000);
  _scUpdateEditorHint();
}}

// ============================================================
// Editor hint bar
// ============================================================
function _scUpdateEditorHint() {{
  var hint = document.getElementById('sc-editor-hint');
  if (_freeNodes.length === 2) {{
    hint.classList.remove('hidden');
    hint.textContent = 'Modo arco activo — 2 nodos libres. Mové el mouse sobre el canvas para previsualizar el arco y hacé click para confirmar.';
  }} else if (_selectedId) {{
    hint.classList.remove('hidden');
    hint.textContent = 'Entidad seleccionada. Presioná Delete o Backspace para eliminarla.';
  }} else {{
    hint.classList.add('hidden');
  }}
}}

// ============================================================
// Discard edits — restore from _editOrigEntities
// ============================================================
function scDiscardEdits() {{
  _editEntities = JSON.parse(JSON.stringify(_editOrigEntities));
  _selectedId   = null;
  _freeNodes    = [];
  document.getElementById('sc-svg').style.cursor = 'grab';
  document.getElementById('sc-layer-preview').innerHTML = '';
  scRenderLayers();
  _scRenderNodes();
  _setScStatus('warning', 'Cambios descartados — volviste al estado post-conversion.');
  setTimeout(function(){{ _setScStatus(''); }}, 2500);
  _scUpdateEditorHint();
}}

// ============================================================
// Confirm and load — serialise entities → POST finalize_edit
// ============================================================
function confirmAndLoad() {{
  if (!_scConvPath) return;
  var newName = _scPatternName + ' (convertido)';
  var newNameInput = prompt('Nombre del nuevo patron:', newName);
  if (!newNameInput || !newNameInput.trim()) return;
  newNameInput = newNameInput.trim();

  var ox = _scStepX || 84;
  var oy = _scStepY || 84;

  _setScStatus('loading', 'Generando DXF y registrando patron...');
  document.getElementById('sc-confirm-btn').disabled = true;

  function _doFinalize(force) {{
    fetch('/api/patterns/finalize_edit', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{
        entities: _editEntities,
        name: newNameInput,
        step_x: ox,
        step_y: oy,
        force: !!force,
      }})
    }})
      .then(function(r) {{ return r.json(); }})
      .then(function(d) {{
        if (d.ok) {{
          _setScStatus('success', '"' + newNameInput + '" cargado exitosamente. Recargando...');
          setTimeout(function() {{ closeSplineConverter(); location.reload(); }}, 1800);
        }} else if (d.exists) {{
          document.getElementById('sc-confirm-btn').disabled = false;
          var ok = confirm(
            '"' + newNameInput + '" ya existe en la galería.\\n\\n' +
            '¿Reemplazar el patrón existente con la versión convertida?\\n' +
            '(El archivo original se perderá.)'
          );
          if (ok) {{ _doFinalize(true); }} else {{
            _setScStatus('warning', 'Guardado cancelado. Elegí otro nombre.');
          }}
        }} else {{
          _setScStatus('error', 'Error: ' + (d.error || '?'));
          document.getElementById('sc-confirm-btn').disabled = false;
        }}
      }})
      .catch(function(e) {{
        _setScStatus('error', 'Error de red: ' + e);
        document.getElementById('sc-confirm-btn').disabled = false;
      }});
  }}
  _doFinalize(false);
}}

// ============================================================
// Status bar
// ============================================================
function _setScStatus(type, msg) {{
  var el = document.getElementById('sc-status-top');
  if (!type || !msg) {{ el.innerHTML = ''; return; }}
  var icons = {{loading:'&#8635;', success:'&#x2713;', warning:'&#9888;', error:'&#x2715;'}};
  var cls   = {{loading:'fb-loading', success:'fb-success', warning:'fb-warning', error:'fb-error'}};
  el.className = 'feedback-area ' + (cls[type]||'');
  el.innerHTML = '<div class="feedback-icon">'+(icons[type]||'')+'</div>'
    + '<div class="feedback-text">' + msg + '</div>';
}}

function _showPlaceholderError(msg) {{
  var p = document.getElementById('sc-placeholder-msg');
  p.style.display = 'flex';
  p.style.color = 'var(--red)';
  p.textContent = msg;
}}

function browseAdminDxf() {{
  fetch('/api/browse-dxf')
    .then(function(r) {{ return r.json(); }})
    .then(function(d) {{ if (d.path) document.getElementById('admin-dxf-path').value = d.path; }})
    .catch(function() {{}});
}}

function toggleCirclesParams() {{
  var checked = document.getElementById('admin-convert-circles').checked;
  document.getElementById('circles-params').style.display = checked ? 'block' : 'none';
}}

function _doAddPattern(nombre, dxfPath, ox, oy) {{
  var fd = new FormData();
  fd.append('name', nombre); fd.append('file_path', dxfPath);
  fd.append('step_x', ox);   fd.append('step_y', oy);
  return fetch('/api/patterns/add', {{method:'POST', body:fd}})
    .then(function(r) {{ return r.json(); }})
    .then(function(d) {{
      if (d.ok) {{
        if (d.restricted) {{
          showFeedback('warning','Patron cargado con restricciones',
            '"' + nombre + '" fue cargado en modo restringido (solo centrado — el corte en borde no estara disponible). '
            + (d.restricted_reason ? d.restricted_reason : ''));
        }} else {{
          showFeedback('success','Patron cargado exitosamente',
            '"' + nombre + '" ya esta en la galeria.' + (d.thumbnail ? ' Preview generado.' : ''));
        }}
        setTimeout(function() {{ location.reload(); }}, 2500);
      }} else {{
        showFeedback('error','Error al procesar el archivo', d.error || 'Error desconocido.');
      }}
    }});
}}

function uploadPattern() {{
  var nombre  = document.getElementById('admin-nombre').value.trim();
  var dxfPath = document.getElementById('admin-dxf-path').value.trim();
  var ox = document.getElementById('admin-offset-x').value;
  var oy = document.getElementById('admin-offset-y').value;
  if (!nombre)  {{ showFeedback('error','Campo requerido','El nombre del patron es obligatorio.'); return; }}
  if (!dxfPath) {{ showFeedback('error','Campo requerido','Selecciona un archivo DXF.'); return; }}
  if (!ox || isNaN(parseFloat(ox)) || parseFloat(ox) <= 0) {{ showFeedback('error','Campo requerido','Ingresá el Offset X en mm.'); return; }}
  if (!oy || isNaN(parseFloat(oy)) || parseFloat(oy) <= 0) {{ showFeedback('error','Campo requerido','Ingresá el Offset Y en mm.'); return; }}

  var convertCircles = document.getElementById('admin-convert-circles').checked;
  if (convertCircles) {{
    var tol  = parseFloat(document.getElementById('admin-circles-tol').value)  || 0.5;
    var rmax = parseFloat(document.getElementById('admin-circles-rmax').value) || 200.0;
    showFeedback('loading','Convirtiendo polígonos...','Detectando LWPOLYLINE circulares y reemplazando por CIRCLE. Puede tardar unos segundos.');
    fetch('/api/patterns/convert_circles', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{dxf_path: dxfPath, tol_mm: tol, r_min: 1.0, r_max: rmax}})
    }})
      .then(function(r) {{ return r.json(); }})
      .then(function(d) {{
        if (!d.ok) {{ showFeedback('error','Error en conversión de círculos', d.error || '?'); return; }}
        var newPath = d.output_path;
        var cnt = d.converted_count;
        showFeedback('loading','Cargando patrón...','Conversión completada: ' + cnt + ' polígono(s) → círculo(s). Registrando patrón...');
        return _doAddPattern(nombre, newPath, ox, oy);
      }})
      .catch(function(e) {{ showFeedback('error','Error de red', String(e)); }});
  }} else {{
    showFeedback('loading','Generando preview...','Validando y procesando el archivo DXF. Puede tardar unos segundos.');
    _doAddPattern(nombre, dxfPath, ox, oy)
      .catch(function(e) {{ showFeedback('error','Error de red', String(e)); }});
  }}
}}

function showFeedback(type, title, detail) {{
  var fb = document.getElementById('admin-feedback');
  fb.classList.remove('hidden');
  var icons = {{loading:'&#8635;', success:'&#x2713;', warning:'&#9888;', error:'&#x2715;'}};
  var cls   = {{loading:'fb-loading', success:'fb-success', warning:'fb-warning', error:'fb-error'}};
  fb.className = 'feedback-area ' + (cls[type]||'fb-loading');
  fb.innerHTML = '<div class="feedback-icon">'+(icons[type]||'')+'</div>'
    + '<div class="feedback-text"><strong>' + title + '</strong> ' + detail + '</div>';
}}

function deletePattern(name, btn) {{
  btn.textContent = 'Borrando...';
  btn.disabled = true;
  fetch('/api/patterns/delete', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{name: name}})
  }})
    .then(function(r) {{ return r.json(); }})
    .then(function(d) {{
      if (d.ok) {{
        btn.textContent = '✓ Borrado';
        btn.style.background = '#e8f8e8';
        btn.style.borderColor = '#4caf50';
        btn.style.color = '#2e7d32';
        setTimeout(function() {{ location.reload(); }}, 800);
      }} else {{
        btn.textContent = 'Borrar';
        btn.disabled = false;
        alert('Error al borrar: ' + (d.error || '?'));
      }}
    }})
    .catch(function(e) {{
      btn.textContent = 'Borrar';
      btn.disabled = false;
      alert('Error de red: ' + e);
    }});
}}

// ---- Material table ----
function showMatFeedback(type, title, detail) {{
  var fb = document.getElementById('mat-feedback');
  fb.classList.remove('hidden');
  var icons = {{loading:'&#8635;', success:'&#x2713;', error:'&#x2715;'}};
  var cls   = {{loading:'fb-loading', success:'fb-success', error:'fb-error'}};
  fb.className = 'feedback-area ' + (cls[type]||'fb-loading');
  fb.innerHTML = '<div class="feedback-icon">'+(icons[type]||'')+'</div>'
    + '<div class="feedback-text"><strong>' + title + '</strong> ' + detail + '</div>';
}}

function addMaterial() {{
  var material   = document.getElementById('mat-material').value.trim();
  var espesor    = parseFloat(document.getElementById('mat-espesor').value);
  var densidad   = parseFloat(document.getElementById('mat-densidad').value);
  var velocidad  = parseFloat(document.getElementById('mat-velocidad').value);
  var pierce     = parseFloat(document.getElementById('mat-pierce').value);
  var consumible = parseFloat(document.getElementById('mat-consumible').value);
  if (!material)             {{ showMatFeedback('error','Campo requerido','El nombre del material es obligatorio.'); return; }}
  if (isNaN(espesor)  || espesor  <= 0) {{ showMatFeedback('error','Valor invalido','Espesor debe ser mayor a cero.'); return; }}
  if (isNaN(densidad) || densidad <  0) {{ showMatFeedback('error','Valor invalido','Densidad no puede ser negativa.'); return; }}
  if (isNaN(velocidad)|| velocidad <= 0) {{ showMatFeedback('error','Valor invalido','Velocidad de corte debe ser mayor a cero.'); return; }}
  if (isNaN(pierce)   || pierce   <  0) {{ showMatFeedback('error','Valor invalido','Tiempo de perforacion no puede ser negativo.'); return; }}
  if (isNaN(consumible)|| consumible < 0) {{ showMatFeedback('error','Valor invalido','Consumible no puede ser negativo.'); return; }}
  showMatFeedback('loading','Guardando...','Agregando material a la tabla.');
  fetch('/api/materials', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{
      material: material,
      espesor_mm: espesor,
      densidad_kg_m2: densidad,
      velocidad_corte_mm_s: velocidad,
      tiempo_perforacion_s: pierce,
      consumible_por_perforacion: consumible
    }})
  }})
    .then(function(r) {{ return r.json(); }})
    .then(function(d) {{
      if (d.ok) {{
        showMatFeedback('success','Material agregado','La tabla se actualizara.');
        setTimeout(function() {{ location.reload(); }}, 900);
      }} else {{
        showMatFeedback('error','Error al guardar', d.error || 'Error desconocido.');
      }}
    }})
    .catch(function(e) {{ showMatFeedback('error','Error de red', String(e)); }});
}}

function deleteMaterialByData(btn) {{
  var payload = {{
    material: btn.dataset.material,
    espesor_mm: parseFloat(btn.dataset.espesor)
  }};
  deleteMaterial(payload, btn);
}}

function deleteMaterial(payload, btn) {{
  btn.textContent = 'Borrando...';
  btn.disabled = true;
  fetch('/api/materials', {{
    method: 'DELETE',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify(payload)
  }})
    .then(function(r) {{ return r.json(); }})
    .then(function(d) {{
      if (d.ok) {{
        btn.textContent = '✓ Borrado';
        btn.style.background = '#e8f8e8';
        btn.style.borderColor = '#4caf50';
        btn.style.color = '#2e7d32';
        setTimeout(function() {{ location.reload(); }}, 800);
      }} else {{
        btn.textContent = 'Borrar';
        btn.disabled = false;
        alert('Error al borrar: ' + (d.error || '?'));
      }}
    }})
    .catch(function(e) {{
      btn.textContent = 'Borrar';
      btn.disabled = false;
      alert('Error de red: ' + e);
    }});
}}
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# render_materiales — standalone spreadsheet-style materials page
# ---------------------------------------------------------------------------

def render_materiales() -> str:
    """Render the /materiales page: an inline-editable spreadsheet table."""
    return """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Nextango — Tabla de materiales</title>
  <style>
""" + _COMMON_CSS + """
    .page-title { font-size:22px; font-weight:700; color:var(--brand); margin-bottom:24px; }
    .mat-sheet { width:100%; border-collapse:collapse; font-size:13px; }
    .mat-sheet thead tr { background:#e8f4f8; }
    .mat-sheet th { padding:9px 12px; text-align:left; font-size:11px; font-weight:700;
                    letter-spacing:.7px; text-transform:uppercase; color:var(--brand);
                    border-bottom:2px solid #c5dde8; white-space:nowrap; }
    .mat-sheet th.num { text-align:right; }
    .mat-sheet td { padding:0; border-bottom:1px solid #eef1f4; vertical-align:middle; }
    .mat-sheet tr:last-child td { border-bottom:none; }
    .mat-sheet tr:hover td { background:#f5fafe; }
    .mat-sheet tr.new-row td { background:#f0faf5; }
    .mat-sheet tr.new-row:hover td { background:#e8f8f0; }
    /* cell display mode */
    .cell-view { display:block; padding:10px 12px; cursor:pointer; min-height:38px; }
    .cell-view.num { text-align:right; }
    /* cell edit mode */
    .cell-edit { display:none; width:100%; border:none; outline:none; padding:8px 12px;
                 font-size:13px; background:#fffbe6; font-family:inherit;
                 box-shadow:inset 0 0 0 2px var(--brand); }
    .cell-edit.num { text-align:right; }
    td.editing .cell-view { display:none; }
    td.editing .cell-edit { display:block; }
    /* new row always shows inputs */
    .new-row .cell-view { display:none; }
    .new-row .cell-edit { display:block; background:#f0faf5; }
    .btn-action { padding:5px 12px; border-radius:4px; font-size:12px; cursor:pointer;
                  font-weight:600; border:1px solid; transition:background .12s; margin:6px 8px; }
    .btn-del { background:#fff; border-color:#e57373; color:#e57373; }
    .btn-del:hover { background:#fff0f0; }
    .add-hint { font-size:12px; color:#888; padding:8px 12px; font-style:italic; }
    .status-bar { font-size:12px; color:#888; margin-top:12px; min-height:20px; }
    .status-ok { color:#2e7d32; }
    .status-err { color:var(--red); }
  </style>
</head>
<body>
""" + _topbar_html("materiales") + """
<div class="page-wrapper">
  <h1 class="page-title">Tabla de materiales</h1>
  <div class="card">
    <div style="display:flex;justify-content:flex-end;margin-bottom:12px">
      <button class="btn-action btn-defaults" onclick="loadDefaults()" id="btn-load-defaults"
              style="background:#e8f4f8;border-color:var(--brand);color:var(--brand);font-size:13px;padding:7px 18px">
        Cargar tabla predeterminada
      </button>
    </div>
    <table class="mat-sheet" id="mat-table">
      <thead>
        <tr>
          <th>Material</th>
          <th class="num">Espesor mm</th>
          <th class="num">Densidad kg/m²</th>
          <th class="num">Vel. corte mm/s</th>
          <th class="num">T. perforación s</th>
          <th>Acciones</th>
        </tr>
      </thead>
      <tbody id="mat-tbody">
        <tr><td colspan="6" style="padding:16px;color:#aaa;font-style:italic">Cargando...</td></tr>
      </tbody>
    </table>
    <div class="status-bar" id="status-bar"></div>
  </div>
</div>

<script>
// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
var _rows = [];   // array of {material, espesor_mm, densidad_kg_m2, velocidad_corte_mm_s, tiempo_perforacion_s}

// Column definitions: [key, isNumeric, placeholder]
var COLS = [
  ['material',              false, 'ej. Acero negro'],
  ['espesor_mm',            true,  'ej. 2'],
  ['densidad_kg_m2',        true,  'ej. 15.7'],
  ['velocidad_corte_mm_s',  true,  'ej. 83.3'],
  ['tiempo_perforacion_s',  true,  'ej. 0.5'],
];

function setStatus(msg, cls) {
  var el = document.getElementById('status-bar');
  el.textContent = msg;
  el.className = 'status-bar ' + (cls || '');
}

// ---------------------------------------------------------------------------
// Load from API
// ---------------------------------------------------------------------------
function loadMaterials() {
  fetch('/api/materials')
    .then(function(r) { return r.json(); })
    .then(function(data) {
      _rows = data;
      renderTable();
    })
    .catch(function(e) { setStatus('Error al cargar materiales: ' + e, 'status-err'); });
}

// ---------------------------------------------------------------------------
// Render
// ---------------------------------------------------------------------------
function renderTable() {
  var tbody = document.getElementById('mat-tbody');
  var html = '';

  _rows.forEach(function(row, ri) {
    html += '<tr data-ri="' + ri + '">';
    COLS.forEach(function(col, ci) {
      var key = col[0], isNum = col[1], ph = col[2];
      var val = row[key] !== undefined ? row[key] : '';
      var numCls = isNum ? ' num' : '';
      html += '<td>'
        + '<span class="cell-view' + numCls + '" onclick="startEdit(this)">' + escHtml(String(val)) + '</span>'
        + '<input class="cell-edit' + numCls + '" type="' + (isNum ? 'number' : 'text') + '"'
        + ' value="' + escHtml(String(val)) + '"'
        + ' placeholder="' + escHtml(ph) + '"'
        + (isNum ? ' step="any" min="0"' : '')
        + ' onkeydown="cellKeydown(event, ' + ri + ', ' + ci + ')"'
        + ' onblur="cellBlur(event, ' + ri + ', ' + ci + ')"'
        + '>'
        + '</td>';
    });
    // Delete button
    html += '<td><button class="btn-action btn-del" onclick="deleteRow(' + ri + ', this)">Borrar</button></td>';
    html += '</tr>';
  });

  // New row — always visible at bottom
  html += '<tr class="new-row" id="new-row">';
  COLS.forEach(function(col, ci) {
    var key = col[0], isNum = col[1], ph = col[2];
    var numCls = isNum ? ' num' : '';
    html += '<td>'
      + '<span class="cell-view' + numCls + '"></span>'
      + '<input class="cell-edit' + numCls + '" type="' + (isNum ? 'number' : 'text') + '"'
      + ' id="new-' + key + '"'
      + ' placeholder="' + escHtml(ph) + '"'
      + (isNum ? ' step="any" min="0"' : '')
      + ' onkeydown="newRowKeydown(event, ' + ci + ')"'
      + '>'
      + '</td>';
  });
  html += '<td><span class="add-hint">nueva fila</span></td>';
  html += '</tr>';

  tbody.innerHTML = html;
}

function escHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ---------------------------------------------------------------------------
// Inline editing — existing rows
// ---------------------------------------------------------------------------
function startEdit(span) {
  var td = span.parentElement;
  td.classList.add('editing');
  var input = td.querySelector('.cell-edit');
  input.focus();
  input.select();
}

function cellKeydown(ev, ri, ci) {
  if (ev.key === 'Enter' || ev.key === 'Tab') {
    ev.preventDefault();
    commitCell(ev.target, ri, ci, function() {
      // Move focus: Tab → next col, Enter → next row same col
      if (ev.key === 'Tab') {
        focusCell(ri, ci + 1);
      } else {
        focusCell(ri + 1, ci);
      }
    });
  } else if (ev.key === 'Escape') {
    // Revert
    var td = ev.target.parentElement;
    ev.target.value = _rows[ri][COLS[ci][0]] !== undefined ? String(_rows[ri][COLS[ci][0]]) : '';
    td.classList.remove('editing');
  }
}

function cellBlur(ev, ri, ci) {
  // Save on blur without navigation
  commitCell(ev.target, ri, ci, null);
}

function commitCell(input, ri, ci, afterCb) {
  var col = COLS[ci];
  var key = col[0], isNum = col[1];
  var raw = input.value.trim();
  var val = isNum ? parseFloat(raw) : raw;
  if (isNum && isNaN(val)) {
    // Revert
    input.value = _rows[ri][key] !== undefined ? String(_rows[ri][key]) : '';
    var td = input.parentElement;
    td.classList.remove('editing');
    if (afterCb) afterCb();
    return;
  }
  var prev = _rows[ri][key];
  if (String(val) === String(prev)) {
    // No change
    var td = input.parentElement;
    td.classList.remove('editing');
    if (afterCb) afterCb();
    return;
  }

  // Build updated entry
  var updated = Object.assign({}, _rows[ri]);
  updated[key] = val;
  // Ensure consumible_por_perforacion preserved
  if (updated.consumible_por_perforacion === undefined) {
    updated.consumible_por_perforacion = 0;
  }

  setStatus('Guardando...', '');
  fetch('/api/materials', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(updated)
  })
    .then(function(r) { return r.json(); })
    .then(function(d) {
      if (d.ok) {
        _rows[ri] = updated;
        setStatus('Guardado.', 'status-ok');
        // Update span text
        var td = input.parentElement;
        td.querySelector('.cell-view').textContent = String(val);
        td.classList.remove('editing');
        if (afterCb) afterCb();
        // Clear status after a moment
        setTimeout(function() { if (document.getElementById('status-bar').textContent === 'Guardado.') setStatus(''); }, 1500);
      } else {
        input.value = String(prev);
        var td = input.parentElement;
        td.classList.remove('editing');
        setStatus('Error al guardar: ' + (d.error || '?'), 'status-err');
        if (afterCb) afterCb();
      }
    })
    .catch(function(e) {
      input.value = String(prev);
      var td = input.parentElement;
      td.classList.remove('editing');
      setStatus('Error de red: ' + e, 'status-err');
      if (afterCb) afterCb();
    });
}

function focusCell(ri, ci) {
  if (ci >= COLS.length) { ci = 0; ri++; }
  var tbody = document.getElementById('mat-tbody');
  var rows = tbody.querySelectorAll('tr[data-ri]');
  if (ri < rows.length) {
    var tds = rows[ri].querySelectorAll('td');
    if (ci < tds.length) {
      var td = tds[ci];
      td.classList.add('editing');
      var input = td.querySelector('.cell-edit');
      if (input) { input.focus(); input.select(); }
    }
  } else {
    // Move to new row
    var newInputs = document.getElementById('new-row').querySelectorAll('.cell-edit');
    if (newInputs.length > 0) { newInputs[0].focus(); }
  }
}

// ---------------------------------------------------------------------------
// New row
// ---------------------------------------------------------------------------
function newRowKeydown(ev, ci) {
  if (ev.key === 'Tab' && ci === COLS.length - 1) {
    ev.preventDefault();
    submitNewRow(true);
  } else if (ev.key === 'Enter') {
    ev.preventDefault();
    submitNewRow(false);
  } else if (ev.key === 'Escape') {
    clearNewRow();
  }
}

function submitNewRow(focusFirst) {
  var entry = {};
  var valid = true;
  COLS.forEach(function(col) {
    var key = col[0], isNum = col[1];
    var input = document.getElementById('new-' + key);
    var raw = input ? input.value.trim() : '';
    if (isNum) {
      var v = parseFloat(raw);
      if (isNaN(v)) { valid = false; return; }
      entry[key] = v;
    } else {
      if (!raw) { valid = false; return; }
      entry[key] = raw;
    }
  });
  if (!valid) {
    setStatus('Completa todos los campos de la nueva fila.', 'status-err');
    return;
  }
  // consumible_por_perforacion: not shown in UI but required by API
  entry.consumible_por_perforacion = 0;

  setStatus('Guardando nueva fila...', '');
  fetch('/api/materials', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(entry)
  })
    .then(function(r) { return r.json(); })
    .then(function(d) {
      if (d.ok) {
        setStatus('Fila agregada.', 'status-ok');
        clearNewRow();
        loadMaterials();
        if (focusFirst) {
          setTimeout(function() {
            var inp = document.getElementById('new-material');
            if (inp) inp.focus();
          }, 100);
        }
        setTimeout(function() { if (document.getElementById('status-bar').textContent === 'Fila agregada.') setStatus(''); }, 1500);
      } else {
        setStatus('Error: ' + (d.error || '?'), 'status-err');
      }
    })
    .catch(function(e) { setStatus('Error de red: ' + e, 'status-err'); });
}

function clearNewRow() {
  COLS.forEach(function(col) {
    var inp = document.getElementById('new-' + col[0]);
    if (inp) inp.value = '';
  });
}

// ---------------------------------------------------------------------------
// Delete
// ---------------------------------------------------------------------------
function deleteRow(ri, btn) {
  var row = _rows[ri];
  btn.textContent = 'Borrando...';
  btn.disabled = true;
  fetch('/api/materials', {
    method: 'DELETE',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({material: row.material, espesor_mm: row.espesor_mm})
  })
    .then(function(r) { return r.json(); })
    .then(function(d) {
      if (d.ok) {
        setStatus('Borrado.', 'status-ok');
        loadMaterials();
        setTimeout(function() { if (document.getElementById('status-bar').textContent === 'Borrado.') setStatus(''); }, 1500);
      } else {
        btn.textContent = 'Borrar';
        btn.disabled = false;
        setStatus('Error al borrar: ' + (d.error || '?'), 'status-err');
      }
    })
    .catch(function(e) {
      btn.textContent = 'Borrar';
      btn.disabled = false;
      setStatus('Error de red: ' + e, 'status-err');
    });
}

// ---------------------------------------------------------------------------
// Load defaults
// ---------------------------------------------------------------------------
function loadDefaults() {
  var btn = document.getElementById('btn-load-defaults');
  var currentCount = _rows.length;
  var confirmed = true;
  if (currentCount > 0) {
    confirmed = confirm(
      'La tabla ya tiene ' + currentCount + ' fila' + (currentCount !== 1 ? 's' : '') +
      '. ¿Reemplazar con los valores predeterminados? Esto borrara los valores actuales.'
    );
  }
  if (!confirmed) return;
  btn.disabled = true;
  btn.textContent = 'Cargando...';
  setStatus('Cargando tabla predeterminada...', '');
  fetch('/api/materials/load_defaults', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({replace: true})
  })
    .then(function(r) { return r.json(); })
    .then(function(d) {
      btn.disabled = false;
      btn.textContent = 'Cargar tabla predeterminada';
      if (d.ok) {
        setStatus('Cargadas ' + d.loaded + ' filas predeterminadas (anteriores: ' + d.previous + ').', 'status-ok');
        loadMaterials();
        setTimeout(function() {
          if (document.getElementById('status-bar').textContent.indexOf('Cargadas') === 0) setStatus('');
        }, 3000);
      } else {
        setStatus('Error: ' + (d.error || '?'), 'status-err');
      }
    })
    .catch(function(e) {
      btn.disabled = false;
      btn.textContent = 'Cargar tabla predeterminada';
      setStatus('Error de red: ' + e, 'status-err');
    });
}

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------
loadMaterials();
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# render_plegados — Plegados Preseteados page
# ---------------------------------------------------------------------------

def render_plegados() -> str:
    """Render the /plegados page: gallery + Bandeja form with AJAX calculation."""
    return """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Nextango — Plegados Preseteados</title>
  <style>
""" + _COMMON_CSS + """
    .page-title { font-size:22px; font-weight:700; color:var(--brand); margin-bottom:24px; }
    .preset-grid { display:flex; flex-wrap:wrap; gap:16px; }
    .preset-thumb { width:100%; height:110px; display:flex; align-items:center;
                    justify-content:center; background:#e8f4f8; border-radius:6px 6px 0 0; }
    .hidden { display:none !important; }
    .result-table { width:100%; border-collapse:collapse; font-size:14px; margin-bottom:18px; }
    .result-table td { padding:8px 12px; border-bottom:1px solid #eef1f4; }
    .result-table tr:last-child td { border-bottom:none; }
    .result-table .lbl { color:#666; width:50%; }
    .result-table .val { font-family:monospace; font-weight:600; color:#176b87; }
    .cost-table { width:100%; border-collapse:collapse; font-size:14px; margin-bottom:18px; }
    .cost-table td { padding:7px 10px; border-bottom:1px solid #eef1f4; }
    .cost-table tr:last-child td { border-bottom:none; }
    .cost-table input[type=number] { width:120px; padding:5px 8px; border:1px solid #c5dde8;
                                     border-radius:4px; font-size:13px; }
    .cost-total-row { background:#e8f4f8; font-weight:700; }
    .btn-dxf { display:inline-block; padding:10px 28px; background:var(--accent2); color:#fff;
               font-size:13px; font-weight:700; letter-spacing:.7px; text-transform:uppercase;
               border:none; border-radius:6px; cursor:pointer; text-decoration:none;
               transition:background .15s; margin-top:8px; }
    .btn-dxf:hover { background:#1a6b3c; }
    .btn-calc { display:inline-block; padding:10px 28px; background:var(--brand); color:#fff;
                font-size:13px; font-weight:700; letter-spacing:.7px; text-transform:uppercase;
                border:none; border-radius:6px; cursor:pointer; transition:background .15s; margin-top:8px; }
    .btn-calc:hover { background:var(--brand-dark); }
    .sep-line { border:none; border-top:1px solid #c5dde8; margin:14px 0; }
    .section-sub { font-size:12px; font-weight:700; letter-spacing:.6px; text-transform:uppercase;
                   color:#176b87; margin:16px 0 8px; }
    .form-row { display:flex; gap:16px; flex-wrap:wrap; }
    .form-group { display:flex; flex-direction:column; gap:4px; min-width:120px; flex:1; }
    .form-group label { font-size:12px; font-weight:600; color:#555; }
    .form-group input, .form-group select { padding:8px 10px; border:1px solid #c5dde8;
      border-radius:6px; font-size:14px; background:#fff; }
    .calc-err { color:var(--red); font-size:13px; margin-top:6px; min-height:18px; }
  </style>
</head>
<body>
""" + _topbar_html("plegados_complejos") + """
<div class="page-wrapper">
  <h1 class="page-title">Plegados Preseteados</h1>

  <!-- PASO 1: Galería de presets -->
  <div class="card" id="step-galeria">
    <div class="card-title">1 — Elegí un preset</div>
    <div class="preset-grid">
      <div class="pattern-card" id="pcard-bandeja" onclick="selectPreset('bandeja')"
           style="cursor:pointer;max-width:200px">
        <div class="preset-thumb">
          <svg viewBox="0 0 100 75" width="100" height="75">
            <polygon points="0,12 12,12 12,0 88,0 88,12 100,12 100,63 88,63 88,75 12,75 12,63 0,63"
                     fill="#c5dde8" stroke="#176b87" stroke-width="2" stroke-linejoin="round"/>
          </svg>
        </div>
        <div class="pattern-name">Bandeja</div>
        <div class="pattern-badge">Motor nativo</div>
        <div class="selected-indicator">Seleccionado</div>
      </div>
    </div>
  </div>

  <!-- PASO 2: Formulario -->
  <div class="card hidden" id="step-form">
    <div class="card-title">2 — Parámetros de la bandeja</div>
    <div class="form-row" style="margin-bottom:14px">
      <div class="form-group">
        <label for="f-material">Material</label>
        <select id="f-material" onchange="onMaterialChange()">
          <option value="">— cargando... —</option>
        </select>
      </div>
      <div class="form-group">
        <label for="f-espesor">Calibre / Espesor</label>
        <select id="f-espesor">
          <option value="">— elegí material —</option>
        </select>
      </div>
    </div>
    <div class="form-row" style="margin-bottom:14px">
      <div class="form-group">
        <label for="f-ancho">Ancho interior (mm)</label>
        <input type="number" id="f-ancho" min="1" step="0.1" placeholder="ej. 300">
      </div>
      <div class="form-group">
        <label for="f-largo">Largo interior (mm)</label>
        <input type="number" id="f-largo" min="1" step="0.1" placeholder="ej. 200">
      </div>
      <div class="form-group">
        <label for="f-alto">Alto de lados (mm)</label>
        <input type="number" id="f-alto" min="1" step="0.1" placeholder="ej. 50">
      </div>
      <div class="form-group">
        <label for="f-cant">Cantidad</label>
        <input type="number" id="f-cant" min="1" step="1" value="1">
      </div>
    </div>
    <div class="calc-err" id="calc-err"></div>
    <button class="btn-calc" onclick="calcular()">Calcular recursos &rarr;</button>
  </div>

  <!-- PASO 3: Resultado -->
  <div class="card hidden" id="step-result">
    <div class="card-title">3 — Recursos y costos</div>

    <div class="section-sub">Desarrollo plano</div>
    <table class="result-table" id="result-blank">
      <tr><td class="lbl">Blank</td><td class="val" id="r-blank">— × — mm</td></tr>
      <tr><td class="lbl">Despunte</td><td class="val" id="r-desp">— mm</td></tr>
    </table>

    <hr class="sep-line">
    <div class="section-sub">Recursos calculados</div>
    <table class="result-table">
      <tr><td class="lbl">Kg de chapa</td><td class="val" id="r-kg">—</td></tr>
      <tr><td class="lbl">Tiempo de laser</td><td class="val" id="r-laser">—</td></tr>
      <tr><td class="lbl">Perforaciones</td><td class="val">0</td></tr>
      <tr><td class="lbl">Plegados</td><td class="val">4</td></tr>
    </table>

    <hr class="sep-line">
    <div class="section-sub">Costos (editables)</div>
    <table class="cost-table">
      <tr>
        <td>Costo chapa</td>
        <td>$ <input type="number" id="c-kg-precio" min="0" step="0.01" oninput="recalcTotal()"> / kg</td>
        <td>&times; <span id="c-kg-cant">—</span> kg</td>
        <td style="font-family:monospace">= $ <span id="c-kg-sub">0.00</span></td>
      </tr>
      <tr>
        <td>Costo laser</td>
        <td>$ <input type="number" id="c-laser-precio" min="0" step="0.01" oninput="recalcTotal()"> / min</td>
        <td>&times; <span id="c-laser-cant">—</span> min</td>
        <td style="font-family:monospace">= $ <span id="c-laser-sub">0.00</span></td>
      </tr>
      <tr>
        <td>Costo plegado</td>
        <td>$ <input type="number" id="c-doblez-precio" min="0" step="0.01" oninput="recalcTotal()"> / doblez</td>
        <td>&times; 4 dobleces</td>
        <td style="font-family:monospace">= $ <span id="c-doblez-sub">0.00</span></td>
      </tr>
      <tr class="cost-total-row">
        <td colspan="3">Subtotal &times; <span id="c-cant-display">1</span> unidades</td>
        <td style="font-family:monospace;font-size:15px">$ <span id="c-total">0.00</span></td>
      </tr>
    </table>

    <hr class="sep-line">
    <form id="dxf-form" method="GET" action="/api/plegados/dxf">
      <input type="hidden" id="dxf-ancho" name="ancho">
      <input type="hidden" id="dxf-largo" name="largo">
      <input type="hidden" id="dxf-alto" name="alto">
      <input type="hidden" id="dxf-espesor" name="espesor">
      <input type="hidden" id="dxf-material" name="material">
      <input type="hidden" id="dxf-calibre" name="calibre">
      <button type="submit" class="btn-dxf">&#11015; Generar DXF</button>
    </form>
  </div>

</div>

<script>
var _matData = {};     // material -> [{espesor_mm, densidad_kg_m2, velocidad_corte_mm_s}]
var _calcResult = {};  // last calcular() response

// ---- Inicialización ----
(function init() {
  // Cargar materiales
  fetch('/api/materials')
    .then(function(r) { return r.json(); })
    .then(function(rows) {
      var byMat = {};
      rows.forEach(function(row) {
        var m = row.material;
        if (!byMat[m]) byMat[m] = [];
        byMat[m].push(row);
      });
      _matData = byMat;
      var sel = document.getElementById('f-material');
      sel.innerHTML = '<option value="">— elegí material —</option>';
      Object.keys(byMat).sort().forEach(function(m) {
        var opt = document.createElement('option');
        opt.value = m; opt.textContent = m;
        sel.appendChild(opt);
      });
    })
    .catch(function() {
      document.getElementById('f-material').innerHTML =
        '<option value="">— carga materiales en /materiales —</option>';
    });
})();

function selectPreset(name) {
  document.querySelectorAll('.pattern-card').forEach(function(c) {
    c.classList.remove('selected');
  });
  document.getElementById('pcard-' + name).classList.add('selected');
  var sf = document.getElementById('step-form');
  sf.classList.remove('hidden');
  setTimeout(function() { sf.scrollIntoView({behavior:'smooth', block:'start'}); }, 60);
}

function onMaterialChange() {
  var mat = document.getElementById('f-material').value;
  var sel = document.getElementById('f-espesor');
  sel.innerHTML = '<option value="">— elegí espesor —</option>';
  if (!mat || !_matData[mat]) return;
  var rows = _matData[mat].slice().sort(function(a,b) {
    return parseFloat(a.espesor_mm) - parseFloat(b.espesor_mm);
  });
  rows.forEach(function(r) {
    var opt = document.createElement('option');
    opt.value = r.espesor_mm;
    opt.textContent = (r.calibre && r.calibre !== '-')
      ? ('N°' + r.calibre + ' (' + r.espesor_mm + ' mm)')
      : (r.espesor_mm + ' mm');
    opt.dataset.densidad = r.densidad_kg_m2;
    opt.dataset.velocidad = r.velocidad_corte_mm_s;
    sel.appendChild(opt);
  });
}

function calcular() {
  var errEl = document.getElementById('calc-err');
  errEl.textContent = '';

  var mat = document.getElementById('f-material').value;
  var espSel = document.getElementById('f-espesor');
  var esp = parseFloat(espSel.value);
  var ancho = parseFloat(document.getElementById('f-ancho').value);
  var largo = parseFloat(document.getElementById('f-largo').value);
  var alto  = parseFloat(document.getElementById('f-alto').value);
  var cant  = parseInt(document.getElementById('f-cant').value, 10) || 1;

  if (!mat) { errEl.textContent = 'Elegí un material.'; return; }
  if (isNaN(esp) || esp <= 0) { errEl.textContent = 'Elegí un espesor.'; return; }
  if (isNaN(ancho) || ancho <= 0) { errEl.textContent = 'Ancho inválido.'; return; }
  if (isNaN(largo) || largo <= 0) { errEl.textContent = 'Largo inválido.'; return; }
  if (isNaN(alto)  || alto  <= 0) { errEl.textContent = 'Alto inválido.'; return; }
  if (alto <= esp) { errEl.textContent = 'El alto debe ser mayor al espesor.'; return; }

  var payload = {ancho_int: ancho, largo_int: largo, alto: alto, espesor: esp,
                 material: mat, cantidad: cant};

  fetch('/api/plegados/calcular', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload)
  })
  .then(function(r) { return r.json(); })
  .then(function(d) {
    if (!d.ok) { errEl.textContent = 'Error: ' + (d.error || '?'); return; }
    _calcResult = d;
    mostrarResultado(d, mat, esp, cant);
  })
  .catch(function(e) { errEl.textContent = 'Error de red: ' + e; });
}

function mostrarResultado(d, mat, esp, cant) {
  document.getElementById('r-blank').textContent =
    d.blank_ancho.toFixed(1) + ' × ' + d.blank_largo.toFixed(1) + ' mm';
  document.getElementById('r-desp').textContent = d.despunte.toFixed(2) + ' mm';
  document.getElementById('r-kg').textContent = d.kg_chapa.toFixed(3) + ' kg';
  var min = (d.tiempo_laser_s / 60).toFixed(2);
  document.getElementById('r-laser').textContent =
    d.tiempo_laser_s.toFixed(1) + ' s (' + min + ' min)';

  // Precargar costos desde precios
  document.getElementById('c-kg-cant').textContent = d.kg_chapa.toFixed(3);
  document.getElementById('c-laser-cant').textContent = (d.tiempo_laser_s / 60).toFixed(2);
  document.getElementById('c-cant-display').textContent = cant;

  // Cargar precios desde /api/prices
  fetch('/api/prices')
    .then(function(r) { return r.json(); })
    .then(function(prices) {
      // Precio kg según material
      var matLow = (mat || '').toLowerCase();
      var precioKg = 0;
      if (matLow.indexOf('galvanizado') !== -1)
        precioKg = parseFloat(prices.precio_kg_galvanizado || 0);
      else if (matLow.indexOf('430') !== -1)
        precioKg = parseFloat(prices.precio_kg_inoxidable_430 || 0);
      else if (matLow.indexOf('304') !== -1 || matLow.indexOf('inoxidable') !== -1)
        precioKg = parseFloat(prices.precio_kg_inoxidable_304 || 0);
      else
        precioKg = parseFloat(prices.precio_kg_doble_decapada || 0);

      var precioMin = parseFloat(prices.precio_segundo_maquina || 0) * 60;
      var precioDoblez = parseFloat(prices.precio_doblez_plegadora || 0);

      document.getElementById('c-kg-precio').value = precioKg || '';
      document.getElementById('c-laser-precio').value = precioMin ? precioMin.toFixed(4) : '';
      document.getElementById('c-doblez-precio').value = precioDoblez || '';
      recalcTotal();
    })
    .catch(function() { recalcTotal(); });

  // Rellenar campos ocultos del form DXF
  document.getElementById('dxf-ancho').value = document.getElementById('f-ancho').value;
  document.getElementById('dxf-largo').value = document.getElementById('f-largo').value;
  document.getElementById('dxf-alto').value  = document.getElementById('f-alto').value;
  document.getElementById('dxf-espesor').value = esp;
  document.getElementById('dxf-material').value = mat;
  document.getElementById('dxf-calibre').value = esp;

  var sr = document.getElementById('step-result');
  sr.classList.remove('hidden');
  setTimeout(function() { sr.scrollIntoView({behavior:'smooth', block:'start'}); }, 60);
}

function recalcTotal() {
  var cant = parseInt(document.getElementById('f-cant').value, 10) || 1;
  var kg   = parseFloat(document.getElementById('c-kg-cant').textContent) || 0;
  var min  = parseFloat(document.getElementById('c-laser-cant').textContent) || 0;

  var pKg  = parseFloat(document.getElementById('c-kg-precio').value)     || 0;
  var pMin = parseFloat(document.getElementById('c-laser-precio').value)   || 0;
  var pDob = parseFloat(document.getElementById('c-doblez-precio').value)  || 0;

  var subKg  = kg  * pKg;
  var subMin = min * pMin;
  var subDob = 4   * pDob;
  var total  = (subKg + subMin + subDob) * cant;

  document.getElementById('c-kg-sub').textContent    = subKg.toFixed(2);
  document.getElementById('c-laser-sub').textContent = subMin.toFixed(2);
  document.getElementById('c-doblez-sub').textContent = subDob.toFixed(2);
  document.getElementById('c-total').textContent     = total.toFixed(2);
  document.getElementById('c-cant-display').textContent = cant;
}
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# render_precios — daily prices page
# ---------------------------------------------------------------------------

def render_precios() -> str:
    """Render the /precios page: form to set/save 5 daily price parameters."""
    # Read current values from daily_prices.json (if it exists)
    prices: dict = {}
    if DAILY_PRICES_FILE.exists():
        try:
            with DAILY_PRICES_FILE.open("r", encoding="utf-8") as f:
                prices = json.load(f)
        except Exception:
            prices = {}

    def _val(key: str) -> str:
        v = prices.get(key)
        return str(v) if v is not None else ""

    return """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Nextango — Precios diarios</title>
  <style>
""" + _COMMON_CSS + """
    .page-title { font-size:22px; font-weight:700; color:var(--brand); margin-bottom:24px; }
    .price-table { width:100%; border-collapse:collapse; font-size:14px; margin-bottom:20px; }
    .price-table th { padding:9px 12px; text-align:left; font-size:11px; font-weight:700;
                      letter-spacing:.7px; text-transform:uppercase; color:var(--brand);
                      border-bottom:2px solid #c5dde8; background:#e8f4f8; }
    .price-table td { padding:10px 12px; border-bottom:1px solid #eef1f4; }
    .price-table tr:last-child td { border-bottom:none; }
    .unit-badge { font-size:11px; color:#888; margin-left:6px; }
    .btn-save { display:inline-block; padding:11px 32px; background:var(--brand); color:#fff;
                font-size:14px; font-weight:700; letter-spacing:.8px; text-transform:uppercase;
                border:none; border-radius:6px; cursor:pointer; transition:background .15s; }
    .btn-save:hover { background:var(--brand-dark); }
    .status-bar { font-size:13px; margin-top:14px; min-height:20px; }
    .status-ok { color:#2e7d32; }
    .status-err { color:var(--red); }
    .field-unit { display:flex; align-items:center; gap:8px; }
    .field-unit input { flex:1; }
    .field-unit .unit-label { font-size:13px; color:#666; white-space:nowrap; min-width:40px; }
  </style>
</head>
<body>
""" + _topbar_html("precios") + """
<div class="page-wrapper">
  <h1 class="page-title">Parametros de precios diarios</h1>
  <div class="card">
    <p style="font-size:13px;color:#555;margin-bottom:20px">
      Estos valores se usan para calcular el costo de cada panel:
      <code style="background:#f0f2f5;padding:2px 6px;border-radius:3px;font-size:12px">
        costo = kg_material &times; precio_kg + segundos &times; precio_segundo_maquina
      </code>
    </p>
    <table class="price-table">
      <thead>
        <tr>
          <th>Parametro</th>
          <th>Valor</th>
          <th>Unidad</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><label for="precio_segundo_maquina">Precio por segundo de maquina</label></td>
          <td><input type="number" id="precio_segundo_maquina" value=\"""" + _val("precio_segundo_maquina") + """\" min="0" step="0.0001" placeholder="ej. 0.05"></td>
          <td><span class="unit-badge">$/s</span></td>
        </tr>
        <tr>
          <td><label for="precio_kg_doble_decapada">Precio por kg — chapa doble decapada</label></td>
          <td><input type="number" id="precio_kg_doble_decapada" value=\"""" + _val("precio_kg_doble_decapada") + """\" min="0" step="0.01" placeholder="ej. 1.50"></td>
          <td><span class="unit-badge">$/kg</span></td>
        </tr>
        <tr>
          <td><label for="precio_kg_galvanizado">Precio por kg — galvanizado</label></td>
          <td><input type="number" id="precio_kg_galvanizado" value=\"""" + _val("precio_kg_galvanizado") + """\" min="0" step="0.01" placeholder="ej. 1.80"></td>
          <td><span class="unit-badge">$/kg</span></td>
        </tr>
        <tr>
          <td><label for="precio_kg_inoxidable_430">Precio por kg — inoxidable 430</label></td>
          <td><input type="number" id="precio_kg_inoxidable_430" value=\"""" + _val("precio_kg_inoxidable_430") + """\" min="0" step="0.01" placeholder="ej. 4.00"></td>
          <td><span class="unit-badge">$/kg</span></td>
        </tr>
        <tr>
          <td><label for="precio_kg_inoxidable_304">Precio por kg — inoxidable 304</label></td>
          <td><input type="number" id="precio_kg_inoxidable_304" value=\"""" + _val("precio_kg_inoxidable_304") + """\" min="0" step="0.01" placeholder="ej. 5.00"></td>
          <td><span class="unit-badge">$/kg</span></td>
        </tr>
        <tr>
          <td><label for="precio_doblez_plegadora">Precio por doblez de plegadora</label></td>
          <td><input type="number" id="precio_doblez_plegadora" value=\"""" + _val("precio_doblez_plegadora") + """\" min="0" step="0.01" placeholder="ej. 500.00"></td>
          <td><span class="unit-badge">$/doblez</span></td>
        </tr>
      </tbody>
    </table>
    <button class="btn-save" onclick="savePrices()">GUARDAR PRECIOS</button>
    <div class="status-bar" id="status-bar"></div>
  </div>
</div>

<script>
function savePrices() {
  var fields = [
    'precio_segundo_maquina',
    'precio_kg_doble_decapada',
    'precio_kg_galvanizado',
    'precio_kg_inoxidable_430',
    'precio_kg_inoxidable_304',
    'precio_doblez_plegadora'
  ];
  var payload = {};
  for (var i = 0; i < fields.length; i++) {
    var el = document.getElementById(fields[i]);
    var raw = el.value.trim();
    if (raw === '') { payload[fields[i]] = null; continue; }
    var v = parseFloat(raw);
    if (isNaN(v) || v < 0) {
      setStatus('Valor invalido en el campo: ' + fields[i], 'status-err');
      el.focus();
      return;
    }
    payload[fields[i]] = v;
  }
  setStatus('Guardando...', '');
  fetch('/api/prices', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload)
  })
    .then(function(r) { return r.json(); })
    .then(function(d) {
      if (d.ok) {
        setStatus('Precios guardados correctamente.', 'status-ok');
        setTimeout(function() {
          if (document.getElementById('status-bar').textContent === 'Precios guardados correctamente.') setStatus('');
        }, 3000);
      } else {
        setStatus('Error: ' + (d.error || '?'), 'status-err');
      }
    })
    .catch(function(e) { setStatus('Error de red: ' + e, 'status-err'); });
}

function setStatus(msg, cls) {
  var el = document.getElementById('status-bar');
  el.textContent = msg;
  el.className = 'status-bar ' + (cls || '');
}
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# render_presupuesto — printable budget page
# ---------------------------------------------------------------------------

def render_presupuesto(presupuesto_id: str | None = None) -> str:
    """Render a printable presupuesto.

    presupuesto_id=None: reads last_generate.json, creates new number, saves PRES_NNNN.json.
    presupuesto_id="NNNN": reads PRES_NNNN.json directly, no new number created.
    """
    import datetime as _dt
    saved_mode = presupuesto_id is not None

    if saved_mode:
        # ---- Load from saved PRES_NNNN.json ---------------------------------
        pres_file = PRESUPUESTOS_DIR / f"PRES_{presupuesto_id}.json"
        if not pres_file.exists():
            return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>Presupuesto</title></head>
<body style="font-family:sans-serif;padding:40px">
  <h2 style="color:#c62828">Presupuesto PRES_{presupuesto_id} no encontrado</h2>
  <p><a href="/presupuestos">Volver a la lista</a></p>
</body></html>"""
        try:
            presupuesto_data = json.loads(pres_file.read_text(encoding="utf-8"))
        except Exception as exc:
            return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>Presupuesto</title></head>
<body style="font-family:sans-serif;padding:40px">
  <h2 style="color:#c62828">Error al leer PRES_{presupuesto_id}</h2>
  <p>{escape(str(exc))}</p>
</body></html>"""
        numero = int(presupuesto_data.get("numero", int(presupuesto_id)))
        fecha_str = presupuesto_data.get("fecha", _dt.date.today().isoformat())
        lineas: list[dict] = presupuesto_data.get("lineas", [])
        daily_prices: dict = presupuesto_data.get("precios_aplicados", {})
        prices_missing: bool = len(daily_prices) == 0
        dxf_path_from_gen = presupuesto_data.get("dxf_path", "")
        gen = presupuesto_data
    else:
        # ---- Load from last_generate.json (original behavior) ---------------
        if not LAST_GENERATE_FILE.exists():
            return """<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>Presupuesto</title></head>
<body style="font-family:sans-serif;padding:40px">
  <h2 style="color:#c62828">Sin datos para presupuesto</h2>
  <p>Genera un pedido primero desde <a href="/">la pagina principal</a>.</p>
</body></html>"""

        try:
            with LAST_GENERATE_FILE.open("r", encoding="utf-8") as f:
                gen = json.load(f)
        except Exception as exc:
            return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>Presupuesto</title></head>
<body style="font-family:sans-serif;padding:40px">
  <h2 style="color:#c62828">Error al leer datos</h2>
  <p>{escape(str(exc))}</p>
</body></html>"""

        fecha_str = gen.get("fecha", _dt.date.today().isoformat())
        lineas: list[dict] = gen.get("lineas", [])
        daily_prices: dict = gen.get("daily_prices", {})
        prices_missing: bool = gen.get("prices_missing", True)
        dxf_path_from_gen = gen.get("dxf_path", "")

        # ---- Assign presupuesto number and persist --------------------------
        # If auto-save already ran (pres_numero in last_generate), reuse that
        # number instead of creating a new one.
        _existing_pres_num = gen.get("pres_numero")
        if _existing_pres_num:
            _pfile = PRESUPUESTOS_DIR / f"PRES_{_existing_pres_num}.json"
            if _pfile.exists():
                # Already saved — load its data and switch to saved_mode
                presupuesto_data = json.loads(_pfile.read_text(encoding="utf-8"))
                numero = int(_existing_pres_num)
                saved_mode = True
            else:
                _existing_pres_num = None
        if not _existing_pres_num:
            numero = _next_presupuesto_number()
            presupuesto_data = {
                "numero": numero,
                "fecha": fecha_str,
                "customer": gen.get("customer", ""),
                "job_name": gen.get("job_name", ""),
                "cliente": "",
                "dxf_path": dxf_path_from_gen,
                "lineas": lineas,
                "batches": gen.get("batches", []),
                "total": round(sum(float((ln.get("cost") or {}).get("costo_total", 0)) for ln in lineas), 2),
                "precios_aplicados": daily_prices,
            }
            try:
                _save_presupuesto(presupuesto_data)
            except Exception as exc:
                logger.warning("No se pudo guardar presupuesto JSON: %s", exc)

    try:
        fecha_display = _dt.date.fromisoformat(fecha_str).strftime("%d/%m/%Y")
    except Exception:
        fecha_display = fecha_str

    total_general = sum(float((ln.get("cost") or {}).get("costo_total", 0)) for ln in lineas)

    # ---- Build table rows --------------------------------------------------
    rows_html = ""
    for i, ln in enumerate(lineas):
        patron = escape(str(ln.get("patron", "")))
        material = escape(str(ln.get("material", "")))
        espesor = ln.get("espesor_mm", "")
        cantidad = int(ln.get("cantidad", 1))
        cost = ln.get("cost") or {}
        costo_total_ln = float(cost.get("costo_total", 0))
        # Unit cost = total / quantity
        costo_unit = costo_total_ln / cantidad if cantidad else 0.0
        mat_esp = f"{material}/{espesor}"
        del_btn = (
            f"<td class='no-print'><button class='btn-del-linea'"
            f" onclick='delLinea({i},{numero:04d})'>&#10005;</button></td>"
            if saved_mode else ""
        )
        rows_html += (
            f"<tr>"
            f"<td>{patron}</td>"
            f"<td>{escape(mat_esp)}</td>"
            f"<td style='text-align:center'>{cantidad}</td>"
            f"<td style='text-align:right'>$ {costo_unit:,.2f}</td>"
            f"<td style='text-align:right'>$ {costo_total_ln:,.2f}</td>"
            f"{del_btn}"
            f"</tr>"
        )

    # ---- Totals row --------------------------------------------------------
    total_row = (
        f"<tr class='total-row'>"
        f"<td colspan='4' style='text-align:right;font-weight:700'>TOTAL</td>"
        f"<td style='text-align:right;font-weight:700'>$ {total_general:,.2f}</td>"
        f"</tr>"
    )

    # ---- Resources summary -------------------------------------------------
    grand_kg = 0.0
    grand_seconds = 0.0
    grand_pierces = 0
    for ln in lineas:
        cr = ln.get("consumed_resources") or {}
        grand_kg += float(cr.get("material_kg", 0))
        grand_seconds += float(cr.get("machine_seconds", 0))
        grand_pierces += int(cr.get("pierce_count", 0))

    mins = int(grand_seconds) // 60
    secs = int(grand_seconds) % 60
    resources_html = f"""
    <div class="section-block">
      <div class="section-title">Recursos totales</div>
      <table class="res-table">
        <tr><td>Material consumido</td><td>{grand_kg:.3f} kg</td></tr>
        <tr><td>Tiempo de maquina</td><td>{mins} min {secs:02d} s</td></tr>
        <tr><td>Perforaciones</td><td>{grand_pierces}</td></tr>
      </table>
    </div>"""

    # ---- Applied prices ----------------------------------------------------
    def _pfmt(key: str, label: str) -> str:
        val = daily_prices.get(key)
        if val is None or val == 0:
            return f"<span class='price-missing'>{label}: —</span>"
        return f"{label}: $ {float(val):,.4f}"

    prices_html = f"""
    <div class="section-block">
      <div class="section-title">Precios aplicados</div>
      <div class="prices-grid">
        <span>{_pfmt('precio_kg_doble_decapada', 'Doble decapada')}/kg</span>
        <span>{_pfmt('precio_kg_galvanizado', 'Galvanizado')}/kg</span>
        <span>{_pfmt('precio_kg_inoxidable_430', 'Inoxidable 430')}/kg</span>
        <span>{_pfmt('precio_kg_inoxidable_304', 'Inoxidable 304')}/kg</span>
        <span>{_pfmt('precio_segundo_maquina', 'Maquina')}/s</span>
      </div>
      {"<div class='prices-missing-warn'>Precios no configurados — los costos son estimativos ($ 0). Configura los precios en <a href='/precios'>/precios</a>.</div>" if prices_missing else ""}
    </div>"""

    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Presupuesto N&deg; {numero:04d} — Nextango</title>
  <style>
{_COMMON_CSS}
    /* ---- Screen layout ---- */
    .pres-wrapper {{ max-width:860px; margin:28px auto; padding:0 20px 60px; }}
    .pres-header {{ background:var(--brand); color:#fff; border-radius:8px 8px 0 0; padding:20px 28px; }}
    .pres-header h1 {{ font-size:20px; font-weight:700; letter-spacing:1px; margin-bottom:4px; }}
    .pres-header .meta {{ display:flex; flex-wrap:wrap; gap:8px 20px; font-size:13px; opacity:.85; }}
    .pres-body {{ background:#fff; border:1px solid #dde; border-top:none; border-radius:0 0 8px 8px; padding:24px 28px 32px; }}
    .pres-table {{ width:100%; border-collapse:collapse; margin-bottom:24px; }}
    .pres-table thead tr {{ background:#e8f4f8; }}
    .pres-table th {{ padding:9px 12px; text-align:left; font-size:11px; font-weight:700; letter-spacing:.7px; text-transform:uppercase; color:var(--brand); border-bottom:2px solid #c5dde8; }}
    .pres-table td {{ padding:10px 12px; border-bottom:1px solid #eef1f4; font-size:13px; }}
    .pres-table tr:last-child td {{ border-bottom:none; }}
    .pres-table tr:hover td {{ background:#f5fafe; }}
    .total-row td {{ background:#e8f4f8 !important; border-top:2px solid #aac8d8; font-size:14px; }}
    .section-block {{ margin-bottom:20px; }}
    .section-title {{ font-size:11px; font-weight:700; letter-spacing:1.1px; text-transform:uppercase;
                      color:var(--brand); margin-bottom:8px; border-bottom:1px solid #e0e6ed; padding-bottom:6px; }}
    .res-table {{ border-collapse:collapse; font-size:13px; }}
    .res-table td {{ padding:4px 24px 4px 0; }}
    .res-table td:first-child {{ color:#555; font-weight:600; min-width:180px; }}
    .res-table td:last-child {{ font-family:monospace; font-size:14px; color:#1a1a2e; }}
    .prices-grid {{ display:flex; flex-wrap:wrap; gap:12px 28px; font-size:13px; color:#333; }}
    .price-missing {{ color:#e65100; }}
    .prices-missing-warn {{ margin-top:10px; font-size:12px; color:#e65100; background:#fff8e1;
                            border:1px solid #ffe082; border-radius:4px; padding:6px 10px; }}
    /* Actions bar (hidden in print) */
    .actions-bar {{ display:flex; gap:12px; margin-bottom:20px; align-items:center; flex-wrap:wrap; }}
    .btn-print {{ padding:9px 22px; background:var(--brand); color:#fff; font-size:13px; font-weight:700;
                  letter-spacing:.5px; border:none; border-radius:5px; cursor:pointer; }}
    .btn-print:hover {{ background:var(--brand-dark); }}
    .btn-back {{ padding:9px 18px; background:#fff; border:1px solid #ccc; border-radius:5px;
                 font-size:13px; cursor:pointer; color:#555; text-decoration:none; }}
    .btn-back:hover {{ background:#f5f5f5; }}
    .btn-dxf {{ padding:9px 18px; background:#f5f5f5; border:1px solid #aaa; border-radius:5px;
                font-size:13px; cursor:pointer; color:#333; text-decoration:none; font-weight:600; }}
    .btn-dxf:hover {{ background:#e8e8e8; }}
    .pres-num {{ font-size:14px; color:#888; }}
    .btn-del-linea {{ background:none; border:none; color:#c62828; font-size:14px; cursor:pointer;
                      padding:2px 6px; border-radius:3px; opacity:.6; }}
    .btn-del-linea:hover {{ background:#ffebee; opacity:1; }}
    .btn-cargar {{ padding:9px 18px; background:#4caf50; color:#fff; border:none; border-radius:5px;
                   font-size:13px; font-weight:700; cursor:pointer; text-decoration:none; display:inline-block; }}
    .btn-cargar:hover {{ background:#388e3c; }}
    /* Cliente field */
    .cliente-row {{ display:flex; align-items:center; gap:10px; margin-bottom:16px; }}
    .cliente-row label {{ font-size:13px; font-weight:700; color:#555; min-width:60px; }}
    .cliente-input {{ border:1px solid #ccc; border-radius:4px; padding:6px 10px; font-size:13px;
                      max-width:260px; width:100%; color:#222; }}
    .cliente-input:focus {{ outline:none; border-color:var(--brand); }}
    .cliente-saved {{ font-size:11px; color:#4caf50; margin-left:4px; display:none; }}
    @media (max-width:600px) {{
      .pres-wrapper {{ padding-left:0; padding-right:0; margin:0; }}
      .pres-header {{ border-radius:0; }}
      .pres-body {{ padding:16px 12px 24px; border-radius:0; }}
      .res-table td:first-child {{ min-width:100px; font-size:11px; }}
    }}
    /* Print */
    @media print {{
      .actions-bar, header, .topbar {{ display:none !important; }}
      .pres-wrapper {{ margin:0; padding:0; max-width:100%; }}
      .pres-header {{ border-radius:0; }}
      .pres-body {{ border:none; }}
      body {{ background:#fff; }}
    }}
  </style>
</head>
<body>
{_topbar_html("presupuesto")}
<div class="pres-wrapper">

  <div class="actions-bar no-print">
    <a href="/" class="btn-back">&larr; Volver</a>
    <button class="btn-print" onclick="window.print()">Imprimir / PDF</button>
    <a href="/presupuestos" class="btn-back">Lista de presupuestos</a>
    {f'<a href="/download_dxf?path={escape(dxf_path_from_gen)}" class="btn-dxf" download>&#11015; Descargar DXF</a>' if dxf_path_from_gen else ""}
    {f"<a href='/generate?load={numero:04d}' class='btn-cargar'>&#9654; Cargar en lista</a>" if saved_mode else ""}
    <span class="pres-num">PRES_{numero:04d}</span>
  </div>

  <div class="cliente-row no-print">
    <label for="cliente-input">Cliente:</label>
    <input id="cliente-input" class="cliente-input" type="text"
           placeholder="Nombre del cliente (opcional)"
           value="{escape(presupuesto_data.get('cliente', ''))}"
           data-pres-id="{numero:04d}">
    <span id="cliente-saved" class="cliente-saved">&#10003; guardado</span>
  </div>

  <div class="pres-header">
    <h1>NEXTANGO &mdash; PRESUPUESTO</h1>
    <div class="meta">
      <span>Fecha: {fecha_display}</span>
      <span>N&deg;: {numero:04d}</span>
      <span>Ref: {escape(gen.get("customer", ""))}</span>
      <span>Trabajo: {escape(gen.get("job_name", ""))}</span>
    </div>
  </div>

  <div class="pres-body">

    <div style="overflow-x:auto">
    <table class="pres-table">
      <thead>
        <tr>
          <th>Panel</th>
          <th>Mat/Esp</th>
          <th style="text-align:center">Cant</th>
          <th style="text-align:right">Costo unit.</th>
          <th style="text-align:right">Subtotal</th>
          {"<th class='no-print'></th>" if saved_mode else ""}
        </tr>
      </thead>
      <tbody>
        {rows_html}
        {total_row}
      </tbody>
    </table>
    </div>

    {resources_html}
    {prices_html}

  </div>
</div>
<script>
(function() {{
  var inp = document.getElementById('cliente-input');
  var saved = document.getElementById('cliente-saved');
  if (!inp) return;
  var presId = inp.dataset.presId;
  var timer = null;
  function saveCliente(val) {{
    fetch('/api/presupuestos/' + presId + '/cliente', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{cliente: val}})
    }}).then(function(r) {{ return r.json(); }}).then(function(data) {{
      if (data.ok) {{
        saved.style.display = 'inline';
        setTimeout(function() {{ saved.style.display = 'none'; }}, 2000);
      }}
    }}).catch(function() {{}});
  }}
  inp.addEventListener('blur', function() {{ saveCliente(inp.value.trim()); }});
  inp.addEventListener('input', function() {{
    clearTimeout(timer);
    timer = setTimeout(function() {{ saveCliente(inp.value.trim()); }}, 1500);
  }});
}})();

function delLinea(idx, presId) {{
  var id = String(presId).padStart(4, '0');
  if (!confirm('¿Eliminar esta línea del presupuesto?')) return;
  fetch('/api/presupuestos/' + id + '/linea/' + idx, {{method: 'DELETE'}})
    .then(function(r) {{ return r.json(); }})
    .then(function(data) {{
      if (data.ok) {{ location.reload(); }}
      else {{ alert('Error: ' + (data.error || 'desconocido')); }}
    }}).catch(function(e) {{ alert('Error de red: ' + e); }});
}}


</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# render_presupuestos — list of saved presupuestos
# ---------------------------------------------------------------------------

def render_presupuestos() -> str:
    """Render /presupuestos: list of all PRES_NNNN.json files, newest first."""
    import datetime as _dt

    files = sorted(
        PRESUPUESTOS_DIR.glob("PRES_*.json"),
        key=lambda p: p.name,
        reverse=True,
    )

    rows_html = ""
    for pfile in files:
        try:
            data = json.loads(pfile.read_text(encoding="utf-8"))
        except Exception:
            continue
        numero = data.get("numero", 0)
        fecha_raw = data.get("fecha", "")
        try:
            fecha_disp = _dt.date.fromisoformat(fecha_raw).strftime("%d/%m/%Y")
        except Exception:
            fecha_disp = fecha_raw
        cliente = escape(str(data.get("cliente", "") or data.get("customer", "")))
        total = data.get("total", 0.0)
        rows_html += (
            f"<tr>"
            f"<td>PRES_{numero:04d}</td>"
            f"<td>{fecha_disp}</td>"
            f"<td>{cliente or '<span style=\"color:#aaa\">Sin nombre</span>'}</td>"
            f"<td style='text-align:right'>$ {float(total):,.2f}</td>"
            f"<td><a href='/presupuesto?id={numero:04d}' class='btn-list-ver'>Ver</a></td>"
            f"<td><button class='btn-list-del' onclick='delPres({numero})'>Borrar</button></td>"
            f"<td><a href='/generate?load={numero:04d}' class='btn-list-react'>&#9654; Cargar en lista</a></td>"
            f"</tr>"
        )

    if not rows_html:
        rows_html = "<tr><td colspan='6' style='text-align:center;color:#888;padding:20px'>No hay presupuestos guardados.</td></tr>"

    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Presupuestos — Nextango</title>
  <style>
{_COMMON_CSS}
    .list-wrapper {{ max-width:860px; margin:28px auto; padding:0 20px 60px; }}
    .list-title {{ font-size:20px; font-weight:700; color:var(--brand); margin-bottom:20px; }}
    .pres-list-table {{ width:100%; border-collapse:collapse; background:#fff; border-radius:8px;
                        box-shadow:0 1px 4px rgba(0,0,0,.08); overflow:hidden; }}
    .pres-list-table th {{ padding:10px 14px; background:#e8f4f8; font-size:11px; font-weight:700;
                           letter-spacing:.7px; text-transform:uppercase; color:var(--brand);
                           border-bottom:2px solid #c5dde8; text-align:left; }}
    .pres-list-table td {{ padding:11px 14px; border-bottom:1px solid #eef1f4; font-size:13px; }}
    .pres-list-table tr:last-child td {{ border-bottom:none; }}
    .pres-list-table tr:hover td {{ background:#f5fafe; }}
    .btn-list-ver {{ padding:5px 12px; background:var(--brand); color:#fff; border-radius:4px;
                     font-size:12px; font-weight:600; text-decoration:none; }}
    .btn-list-ver:hover {{ background:var(--brand-dark); }}
    .btn-list-del {{ padding:5px 12px; background:#fff; border:1px solid #e57373; color:#c62828;
                     border-radius:4px; font-size:12px; font-weight:600; cursor:pointer; }}
    .btn-list-del:hover {{ background:#ffebee; }}
    .btn-list-react {{ padding:5px 12px; background:#fff; border:1px solid #a5d6a7; color:#2e7d32;
                       border-radius:4px; font-size:12px; font-weight:600; cursor:pointer; }}
    .btn-list-react:hover {{ background:#e8f5e9; }}
  </style>
</head>
<body>
{_topbar_html("presupuestos")}
<div class="list-wrapper">
  <div class="list-title">Presupuestos guardados</div>
  <table class="pres-list-table">
    <thead>
      <tr>
        <th>N&deg;</th>
        <th>Fecha</th>
        <th>Cliente</th>
        <th style="text-align:right">Total</th>
        <th></th>
        <th></th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>
</div>
<script>
function delPres(num) {{
  var id = String(num).padStart(4, '0');
  if (!confirm('¿Eliminar PRES_' + id + '? Esta acción no se puede deshacer.')) return;
  fetch('/api/presupuestos/' + id, {{method: 'DELETE'}})
    .then(function(r) {{ return r.json(); }})
    .then(function(data) {{
      if (data.ok) {{ location.reload(); }}
      else {{ alert('Error: ' + (data.error || 'desconocido')); }}
    }}).catch(function(e) {{ alert('Error de red: ' + e); }});
}}


</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# JSON helper
# ---------------------------------------------------------------------------

def _send_json(handler: BaseHTTPRequestHandler, data: dict, status: int = 200) -> None:
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(payload)))
    handler.end_headers()
    handler.wfile.write(payload)


# ---------------------------------------------------------------------------
# HTTP server
# ---------------------------------------------------------------------------

class PanelSalesHandler(BaseHTTPRequestHandler):
    output_dir = DEFAULT_OUTPUT_DIR
    price_file = DEFAULT_PRICE_FILE

    def _send_html(self, html: str, status: int = 200) -> None:
        payload = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:
        try:
            self._do_GET_inner()
        except Exception as exc:
            logger.error("Unhandled GET error for %s: %s", self.path, exc, exc_info=True)
            try:
                _send_json(self, {"ok": False, "error": "Error interno del servidor"}, 500)
            except Exception:
                pass

    def _do_GET_inner(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/":
            if callable(globals().get("render_landing")):
                self._send_html(render_landing())  # type: ignore[name-defined]
            else:
                # Placeholder until Vega implements render_landing()
                self.send_response(302)
                self.send_header("Location", "/paneles")
                self.end_headers()
            return

        if parsed.path == "/paneles":
            self._send_html(render_form())
            return

        if parsed.path == "/generate":
            from urllib.parse import parse_qs as _pqs
            _qp = _pqs(parsed.query)
            _load_id = (_qp.get("load") or [None])[0]
            self._send_html(render_form(load=_load_id))
            return

        if parsed.path == "/admin":
            self._send_html(render_admin())
            return

        if parsed.path == "/materiales":
            self._send_html(render_materiales())
            return

        if parsed.path == "/precios":
            self._send_html(render_precios())
            return

        if parsed.path == "/presupuesto":
            from urllib.parse import parse_qs as _pqs
            _qp = _pqs(parsed.query)
            _pres_id = (_qp.get("id") or [None])[0]
            self._send_html(render_presupuesto(presupuesto_id=_pres_id))
            return

        if parsed.path == "/presupuestos":
            self._send_html(render_presupuestos())
            return

        if parsed.path in ("/plegados", "/plegados/complejos"):
            self._send_html(render_plegados())
            return

        if parsed.path == "/plegados/perfiles":
            self._handle_plegados_perfiles()
            return

        if parsed.path == "/api/plegados/dxf":
            self._handle_plegados_dxf()
            return

        if parsed.path == "/api/plegados/pedidos":
            self._handle_plegados_pedidos_list()
            return

        if parsed.path.startswith("/api/plegados/pedido/"):
            _pid = parsed.path.removeprefix("/api/plegados/pedido/").strip("/")
            self._handle_plegados_pedido_get(_pid)
            return

        if parsed.path == "/download_dxf":
            self._handle_download_dxf()
            return

        if parsed.path == "/api/prices":
            self._handle_prices_get()
            return

        if parsed.path == "/api/patterns":
            try:
                raw = get_pattern_library_patterns()
            except Exception:
                raw = {}
            # Enrich with thumbnail_url
            result = {}
            for name, info in raw.items():
                entry = dict(info)
                entry["thumbnail_url"] = _thumbnail_url(name)
                result[name] = entry
            _send_json(self, result)
            return

        if parsed.path == "/api/materials":
            self._handle_material_list()
            return

        if parsed.path == "/api/browse-dxf":
            selected = _browse_dxf_file()
            _send_json(self, {"path": selected})
            return

        if parsed.path == "/api/patterns/preview_dxf":
            self._handle_preview_dxf()
            return

        if parsed.path == "/api/patterns/entities":
            self._handle_patterns_entities()
            return

        if parsed.path.startswith("/static/pattern_thumbnails/"):
            rel = parsed.path.removeprefix("/static/pattern_thumbnails/")
            if ".." in rel or "/" in rel:
                self.send_error(400)
                return
            path = THUMBNAIL_DIR / rel
            if not path.exists() or not path.is_file():
                self.send_error(404)
                return
            payload = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        if parsed.path.startswith("/static/tools/"):
            rel = parsed.path.removeprefix("/static/tools/")
            if ".." in rel or "/" in rel:
                self.send_error(400)
                return
            path = TOOLS_DIR / rel
            if not path.exists() or not path.is_file():
                self.send_error(404)
                return
            payload = path.read_bytes()
            ext = path.suffix.lower()
            content_type = "image/png" if ext == ".png" else "image/jpeg" if ext in (".jpg", ".jpeg") else "application/octet-stream"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        if parsed.path.startswith("/outputs/"):
            rel = parsed.path.removeprefix("/outputs/")
            path = self.output_dir / Path(rel)
            if not path.exists() or not path.is_file():
                self.send_error(404)
                return
            payload = path.read_bytes()
            sfx = path.suffix.lower()
            if sfx == ".json":
                content_type = "application/json"
            elif sfx == ".zip":
                content_type = "application/zip"
            elif sfx == ".dxf":
                content_type = "application/dxf"
            else:
                content_type = "application/octet-stream"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Disposition", f'attachment; filename="{path.name}"')
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        if parsed.path == "/api/cortes/items":
            self._handle_cortes_items_list()
            return

        if parsed.path == "/api/cortes/dxf":
            self._handle_cortes_dxf()
            return

        if parsed.path == "/api/presupuestos":
            self._handle_presupuestos_list_json()
            return

        import re as _re
        _pm = _re.match(r"^/api/presupuestos/((?:PRES_)?\d{4})$", parsed.path)
        if _pm:
            self._handle_presupuesto_get_json(_pm.group(1))
            return

        self.send_error(404)

    def do_POST(self) -> None:
        try:
            self._do_POST_inner()
        except Exception as exc:
            logger.error("Unhandled POST error for %s: %s", self.path, exc, exc_info=True)
            try:
                _send_json(self, {"ok": False, "error": "Error interno del servidor"}, 500)
            except Exception:
                pass

    def _do_POST_inner(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/generate":
            self._handle_generate()
            return

        if parsed.path == "/api/patterns/add":
            self._handle_pattern_add()
            return

        if parsed.path == "/api/patterns/delete":
            self._handle_pattern_delete()
            return

        if parsed.path == "/api/materials":
            self._handle_material_add()
            return

        if parsed.path == "/api/patterns/convert_splines":
            self._handle_convert_splines()
            return

        if parsed.path == "/api/patterns/convert_circles":
            self._handle_convert_circles()
            return

        if parsed.path == "/api/materials/load_defaults":
            self._handle_material_load_defaults()
            return

        if parsed.path == "/api/prices":
            self._handle_prices_save()
            return

        if parsed.path == "/api/plegados/calcular":
            self._handle_plegados_calcular()
            return

        if parsed.path == "/api/plegados/pedido":
            self._handle_plegados_pedido_post()
            return

        if parsed.path == "/api/cortes/item":
            self._handle_cortes_item_post()
            return

        if parsed.path == "/api/patterns/finalize_edit":
            self._handle_finalize_edit()
            return

        # POST /api/presupuestos/:id/cliente
        import re as _re
        m = _re.match(r"^/api/presupuestos/(\d{4})/cliente$", parsed.path)
        if m:
            self._handle_presupuesto_cliente(m.group(1))
            return

        self.send_error(404)

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/api/materials":
            self._handle_material_delete()
            return

        if parsed.path == "/api/cortes/items":
            self._handle_cortes_items_clear()
            return

        # DELETE /api/cortes/item/<id>
        import re as _re
        mc = _re.match(r"^/api/cortes/item/(.+)$", parsed.path)
        if mc:
            self._handle_cortes_item_delete(mc.group(1))
            return

        # DELETE /api/presupuestos/:id
        m = _re.match(r"^/api/presupuestos/(\d{4})$", parsed.path)
        if m:
            self._handle_presupuesto_delete(m.group(1))
            return

        # DELETE /api/presupuestos/:id/linea/:idx
        m2 = _re.match(r"^/api/presupuestos/(\d{4})/linea/(\d+)$", parsed.path)
        if m2:
            self._handle_presupuesto_del_linea(m2.group(1), int(m2.group(2)))
            return

        self.send_error(404)

    def _handle_generate(self) -> None:
        try:
            form = _parse_post_form(self)
            batches_json = _first(form, "batches_json", "")
            customer = _first(form, "customer_reference", "CLIENTE-DEMO")
            job_name = _first(form, "job_name", "Panel decorativo")
            observations = _first(form, "observations", "")

            # Capture pres_numero before _run_all_batches overwrites last_generate.json
            _prev_pres_numero: str | None = None
            try:
                if LAST_GENERATE_FILE.exists():
                    _prev_lg = json.loads(LAST_GENERATE_FILE.read_text(encoding="utf-8"))
                    _prev_pres_numero = _prev_lg.get("pres_numero")
            except Exception:
                pass

            if batches_json:
                batches = json.loads(batches_json)
                if not batches:
                    raise ValueError("Lista de lotes vacia.")
                result = _run_all_batches(
                    batches, customer, job_name, observations,
                    self.output_dir, self.price_file,
                )
            else:
                # Fallback: single-batch legacy path (also used by HTTP test)
                data = build_sales_input(form)
                result = run_sales_flow(data, self.output_dir, self.price_file)

            # Auto-save presupuesto so it persists regardless of subsequent navigation
            _auto_save_presupuesto(_prev_pres_numero)

        except Exception as exc:
            self._send_html(render_form(error=str(exc)), status=400)
            return
        self._send_html(render_form(result=result))

    def _handle_pattern_add(self) -> None:
        try:
            form = _parse_formdata_raw(self)
            name = _first(form, "name", "").strip()
            file_path = _first(form, "file_path", "").strip()
            step_x = float(_first(form, "step_x", "84"))
            step_y = float(_first(form, "step_y", "84"))
            if not name:
                _send_json(self, {"ok": False, "error": "name requerido"}, 400)
                return
            if not file_path:
                _send_json(self, {"ok": False, "error": "file_path requerido"}, 400)
                return
            # Check for unsupported entities. Instead of blocking the upload we
            # accept the pattern in "restricted mode": centred placement only,
            # no edge-cutting.
            ok, msg = validate_dxf_entities(file_path)
            restricted = not ok
            restricted_reason = msg if restricted else ""

            add_pattern_to_library(
                name, file_path, step_x, step_y,
                restricted=restricted,
                restricted_reason=restricted_reason,
            )
            # Respond immediately — thumbnail generation happens in background.
            # Include restricted fields so the admin JS can surface the warning.
            _send_json(self, {
                "ok": True,
                "thumbnail": False,
                "restricted": restricted,
                "restricted_reason": restricted_reason,
            })
            # Fire-and-forget thumbnail generation (must not block HTTP thread)
            import threading
            pattern_data = {"file_path": file_path, "step_x": step_x, "step_y": step_y, "type": "dxf"}
            t = threading.Thread(
                target=generate_pattern_thumbnail, args=(name, pattern_data), daemon=True
            )
            t.start()
        except Exception as exc:
            _send_json(self, {"ok": False, "error": str(exc)}, 500)

    def _handle_pattern_delete(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            payload = json.loads(body)
            name = str(payload.get("name", "")).strip()
            if not name:
                _send_json(self, {"ok": False, "error": "name requerido"}, 400)
                return
            delete_pattern_from_library(name)
            _send_json(self, {"ok": True})
        except Exception as exc:
            _send_json(self, {"ok": False, "error": str(exc)}, 500)

    def _handle_material_list(self) -> None:
        try:
            table = MaterialTable()
            _send_json(self, table.list())
        except Exception as exc:
            _send_json(self, {"ok": False, "error": str(exc)}, 500)

    def _handle_material_add(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            entry = json.loads(body)
            table = MaterialTable()
            table.add(entry)
            _send_json(self, {"ok": True})
        except (ValueError, KeyError) as exc:
            _send_json(self, {"ok": False, "error": str(exc)}, 400)
        except Exception as exc:
            _send_json(self, {"ok": False, "error": str(exc)}, 500)

    def _handle_material_delete(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            payload = json.loads(body)
            material = str(payload.get("material", "")).strip()
            espesor_mm = float(payload.get("espesor_mm", 0))
            if not material:
                _send_json(self, {"ok": False, "error": "material requerido"}, 400)
                return
            table = MaterialTable()
            table.delete(material, espesor_mm)
            _send_json(self, {"ok": True})
        except KeyError as exc:
            _send_json(self, {"ok": False, "error": str(exc)}, 404)
        except Exception as exc:
            _send_json(self, {"ok": False, "error": str(exc)}, 500)

    def _handle_preview_dxf(self) -> None:
        """GET /api/patterns/preview_dxf?path=...&mode=original|converted

        Returns an SVG document that renders the DXF entities.
        """
        from urllib.parse import parse_qs, urlparse as _up
        qs = parse_qs(_up(self.path).query)
        dxf_path = (qs.get("path") or [""])[0].strip()
        mode = (qs.get("mode") or ["original"])[0].strip()
        if mode not in ("original", "converted"):
            mode = "original"

        if not dxf_path:
            svg = '<svg xmlns="http://www.w3.org/2000/svg"><text y="20" fill="red">path requerido</text></svg>'
        elif not Path(dxf_path).exists():
            svg = f'<svg xmlns="http://www.w3.org/2000/svg"><text y="20" fill="red">Archivo no encontrado</text></svg>'
        else:
            try:
                svg = _dxf_to_svg(dxf_path, mode)
            except Exception as exc:
                svg = f'<svg xmlns="http://www.w3.org/2000/svg"><text y="20" fill="red">Error: {escape(str(exc))}</text></svg>'

        payload = svg.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "image/svg+xml; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _handle_convert_splines(self) -> None:
        """POST /api/patterns/convert_splines

        Body JSON: {"dxf_path": "...", "tolerance": 0.1}
        Generates a clean _converted.dxf in the same directory.
        Returns: {"ok": true, "output_path": "...", "converted_count": N, "arc_count": N, "line_count": N}
        """
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            payload = json.loads(body)
            dxf_path = str(payload.get("dxf_path", "")).strip()
            tolerance = float(payload.get("tolerance", 0.1))
            if not dxf_path:
                _send_json(self, {"ok": False, "error": "dxf_path requerido"}, 400)
                return
            if not Path(dxf_path).exists():
                _send_json(self, {"ok": False, "error": f"Archivo no encontrado: {dxf_path}"}, 400)
                return
            p = Path(dxf_path)
            output_path = str(p.parent / (p.stem + "_converted.dxf"))
            stats = convert_dxf_splines_clean(dxf_path, output_path, tolerance)
            _send_json(self, {
                "ok": True,
                "output_path": output_path,
                "converted_count": stats["converted_count"],
                "arc_count": stats["arc_count"],
                "line_count": stats["line_count"],
            })
        except Exception as exc:
            _send_json(self, {"ok": False, "error": str(exc)}, 500)

    def _handle_convert_circles(self) -> None:
        """POST /api/patterns/convert_circles

        Body JSON: {"dxf_path": "...", "tol_mm": 0.5, "r_min": 1.0, "r_max": 200.0}
        Converts circular LWPOLYLINE entities to CIRCLE and saves to _circles.dxf.
        Returns: {"ok": true, "output_path": "...", "converted_count": N}
        """
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            payload = json.loads(body)
            dxf_path = str(payload.get("dxf_path", "")).strip()
            tol_mm = float(payload.get("tol_mm", 0.5))
            r_min = float(payload.get("r_min", 1.0))
            r_max = float(payload.get("r_max", 200.0))
            if not dxf_path:
                _send_json(self, {"ok": False, "error": "dxf_path requerido"}, 400)
                return
            if not Path(dxf_path).exists():
                _send_json(self, {"ok": False, "error": f"Archivo no encontrado: {dxf_path}"}, 400)
                return
            p = Path(dxf_path)
            output_path = str(p.parent / (p.stem + "_circles.dxf"))
            count = convert_dxf_poly_to_circles(dxf_path, output_path, tol_mm, r_min, r_max)
            _send_json(self, {"ok": True, "output_path": output_path, "converted_count": count})
        except Exception as exc:
            _send_json(self, {"ok": False, "error": str(exc)}, 500)

    def _handle_material_load_defaults(self) -> None:
        """POST /api/materials/load_defaults  — replace table with MATERIAL_DEFAULTS."""
        try:
            from sistema_industrial.presets.material_defaults import MATERIAL_DEFAULTS  # noqa: PLC0415
            table = MaterialTable()
            previous = len(table.list())
            # Load defaults including the 'calibre' field
            table._entries = []  # clear in-memory list
            for entry in MATERIAL_DEFAULTS:
                table._entries.append({
                    "material": str(entry["material"]).strip(),
                    "calibre": str(entry.get("calibre", "-")).strip() or "-",
                    "espesor_mm": float(entry["espesor_mm"]),
                    "densidad_kg_m2": float(entry["densidad_kg_m2"]),
                    "velocidad_corte_mm_s": float(entry["velocidad_corte_mm_s"]),
                    "tiempo_perforacion_s": float(entry["tiempo_perforacion_s"]),
                    "consumible_por_perforacion": float(entry["consumible_por_perforacion"]),
                })
            table.save()
            _send_json(self, {"ok": True, "loaded": len(MATERIAL_DEFAULTS), "previous": previous})
        except Exception as exc:
            _send_json(self, {"ok": False, "error": str(exc)}, 500)

    def _handle_prices_get(self) -> None:
        """GET /api/prices — return current daily_prices.json content."""
        try:
            if DAILY_PRICES_FILE.exists():
                with DAILY_PRICES_FILE.open("r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {}
            _send_json(self, data)
        except Exception as exc:
            _send_json(self, {"ok": False, "error": str(exc)}, 500)

    def _handle_prices_save(self) -> None:
        """POST /api/prices — save 5 price params to daily_prices.json."""
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            payload = json.loads(body)
            allowed = {
                "precio_segundo_maquina",
                "precio_kg_doble_decapada",
                "precio_kg_galvanizado",
                "precio_kg_inoxidable_430",
                "precio_kg_inoxidable_304",
                "precio_doblez_plegadora",
            }
            prices: dict = {}
            for key in allowed:
                val = payload.get(key)
                if val is not None:
                    prices[key] = float(val)
                else:
                    prices[key] = None
            DAILY_PRICES_FILE.parent.mkdir(parents=True, exist_ok=True)
            with DAILY_PRICES_FILE.open("w", encoding="utf-8") as f:
                json.dump(prices, f, indent=2, ensure_ascii=False)
            _send_json(self, {"ok": True})
        except Exception as exc:
            _send_json(self, {"ok": False, "error": str(exc)}, 500)

    def _handle_patterns_entities(self) -> None:
        """GET /api/patterns/entities?path=...

        Returns a JSON object with the list of LINE/ARC entities extracted
        from the DXF at the given path.
        """
        from urllib.parse import parse_qs, urlparse as _up
        qs = parse_qs(_up(self.path).query)
        dxf_path = (qs.get("path") or [""])[0].strip()
        if not dxf_path:
            _send_json(self, {"ok": False, "error": "path requerido"}, 400)
            return
        if not Path(dxf_path).exists():
            _send_json(self, {"ok": False, "error": f"Archivo no encontrado: {dxf_path}"}, 404)
            return
        try:
            entities = _dxf_entities_json(dxf_path)
            _send_json(self, {"entities": entities})
        except Exception as exc:
            _send_json(self, {"ok": False, "error": str(exc)}, 500)

    def _handle_finalize_edit(self) -> None:
        """POST /api/patterns/finalize_edit

        Body JSON: {"entities": [...], "name": "...", "step_x": X, "step_y": Y}
        Generates a clean DXF from the entity list, registers it as a pattern,
        and returns {"ok": true, "file_path": "..."}.
        """
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            data = json.loads(body)
        except Exception as exc:
            _send_json(self, {"ok": False, "error": f"JSON invalido: {exc}"}, 400)
            return
        try:
            entities = data.get("entities")
            if not isinstance(entities, list):
                _send_json(self, {"ok": False, "error": "entities debe ser una lista"}, 400)
                return
            name = str(data.get("name", "")).strip()
            if not name:
                _send_json(self, {"ok": False, "error": "name requerido"}, 400)
                return
            step_x = float(data.get("step_x", 84))
            step_y = float(data.get("step_y", 84))

            # Refuse overwriting an existing pattern without explicit confirmation.
            # Silently overwriting would destroy the original DXF file and its entry.
            force = bool(data.get("force", False))
            if not force:
                try:
                    lib_path = find_legacy_panel_dir() / "pattern_library.json"
                    if lib_path.exists():
                        existing = json.loads(lib_path.read_text(encoding="utf-8"))
                        if name in existing:
                            _send_json(self, {
                                "ok": False,
                                "exists": True,
                                "error": (
                                    f'"{name}" ya existe en la galería. '
                                    "Elegí un nombre diferente o confirmá el reemplazo."
                                ),
                            }, 409)
                            return
                except Exception:
                    pass  # fail-open: can't read library, proceed normally

            # Determine output directory — store alongside uploaded patterns
            out_dir = self.output_dir / "uploaded_patterns"
            out_dir.mkdir(parents=True, exist_ok=True)
            safe_name = re.sub(r"[^A-Za-z0-9_\-]", "_", name)
            out_path = str(out_dir / f"{safe_name}_editado.dxf")

            _entities_to_dxf(entities, out_path)

            # Register as pattern (unrestricted — all entities are LINE/ARC)
            add_pattern_to_library(
                name, out_path, step_x, step_y,
                restricted=False,
                restricted_reason="",
            )

            # Regenerate thumbnail asynchronously
            import threading
            pattern_data = {"file_path": out_path, "step_x": step_x, "step_y": step_y, "type": "dxf"}
            t = threading.Thread(
                target=generate_pattern_thumbnail, args=(name, pattern_data), daemon=True
            )
            t.start()

            _send_json(self, {"ok": True, "file_path": out_path})
        except Exception as exc:
            _send_json(self, {"ok": False, "error": str(exc)}, 500)

    def _handle_download_dxf(self) -> None:
        """GET /download_dxf?path=... — serve a DXF file with path validation."""
        from urllib.parse import parse_qs, urlparse as _up
        qs = parse_qs(_up(self.path).query)
        dxf_path_str = (qs.get("path") or [""])[0].strip()
        if not dxf_path_str:
            self.send_error(400)
            return
        try:
            target = Path(dxf_path_str).resolve()
            allowed_root = self.output_dir.resolve()
            if not str(target).startswith(str(allowed_root)):
                self.send_error(403)
                return
            if not target.exists() or not target.is_file():
                self.send_error(404)
                return
            payload = target.read_bytes()
            self.send_response(200)
            ctype = "application/zip" if target.suffix.lower() == ".zip" else "application/dxf"
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Disposition",
                             f'attachment; filename="{target.name}"')
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        except Exception as exc:
            logger.error("download_dxf error: %s", exc)
            self.send_error(500)

    def _handle_presupuesto_cliente(self, pres_id: str) -> None:
        """POST /api/presupuestos/:id/cliente — update cliente field in PRES_NNNN.json."""
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            payload = json.loads(body)
            cliente = str(payload.get("cliente", "")).strip()

            pfile = PRESUPUESTOS_DIR / f"PRES_{pres_id}.json"
            if not pfile.exists():
                _send_json(self, {"ok": False, "error": "Presupuesto no encontrado"}, 404)
                return
            data = json.loads(pfile.read_text(encoding="utf-8"))
            data["cliente"] = cliente
            pfile.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            _send_json(self, {"ok": True})
        except Exception as exc:
            _send_json(self, {"ok": False, "error": str(exc)}, 500)

    def _handle_presupuesto_delete(self, pres_id: str) -> None:
        """DELETE /api/presupuestos/:id — delete PRES_NNNN.json."""
        try:
            pfile = PRESUPUESTOS_DIR / f"PRES_{pres_id}.json"
            if not pfile.exists():
                _send_json(self, {"ok": False, "error": "Presupuesto no encontrado"}, 404)
                return
            pfile.unlink()
            _send_json(self, {"ok": True})
        except Exception as exc:
            _send_json(self, {"ok": False, "error": str(exc)}, 500)

    def _handle_presupuesto_del_linea(self, pres_id: str, idx: int) -> None:
        """DELETE /api/presupuestos/:id/linea/:idx — remove one line from PRES_NNNN.json."""
        try:
            pfile = PRESUPUESTOS_DIR / f"PRES_{pres_id}.json"
            if not pfile.exists():
                _send_json(self, {"ok": False, "error": "Presupuesto no encontrado"}, 404)
                return
            data = json.loads(pfile.read_text(encoding="utf-8"))
            lineas = data.get("lineas", [])
            if idx < 0 or idx >= len(lineas):
                _send_json(self, {"ok": False, "error": "Índice fuera de rango"}, 400)
                return
            lineas.pop(idx)
            data["lineas"] = lineas
            data["total"] = round(
                sum(float((ln.get("cost") or {}).get("costo_total", 0)) for ln in lineas), 2
            )
            pfile.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            _send_json(self, {"ok": True})
        except Exception as exc:
            _send_json(self, {"ok": False, "error": str(exc)}, 500)

    def _handle_plegados_perfiles(self) -> None:
        """GET /plegados/perfiles — serve the Cybelec plegado app."""
        try:
            html = PLEGADOS_PERFILES_HTML.read_text(encoding="utf-8")
            self._send_html(html)
        except FileNotFoundError:
            self.send_error(404, "plegado_app/index.html not found")

    # ------------------------------------------------------------------
    # Plegados pedidos API
    # ------------------------------------------------------------------

    def _next_pedido_id(self) -> str:
        """Generate next PL-YYYYMMDD-NNNN id (auto-incremental per day)."""
        import datetime as _dt
        today = _dt.date.today().strftime("%Y%m%d")
        PLEGADOS_PEDIDOS_DIR.mkdir(parents=True, exist_ok=True)
        existing = sorted(
            p.stem for p in PLEGADOS_PEDIDOS_DIR.glob(f"PL-{today}-*.json")
        )
        if existing:
            last_n = int(existing[-1].split("-")[-1])
        else:
            last_n = 0
        return f"PL-{today}-{last_n + 1:04d}"

    def _handle_plegados_pedido_post(self) -> None:
        """POST /api/plegados/pedido — save a plegado order as JSON."""
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            payload = json.loads(body)
            pedido_id = self._next_pedido_id()
            payload["id"] = pedido_id
            PLEGADOS_PEDIDOS_DIR.mkdir(parents=True, exist_ok=True)
            pedido_path = PLEGADOS_PEDIDOS_DIR / f"{pedido_id}.json"
            pedido_path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            _send_json(self, {"ok": True, "id": pedido_id})
        except Exception as exc:
            _send_json(self, {"ok": False, "error": str(exc)}, 500)

    def _handle_plegados_pedidos_list(self) -> None:
        """GET /api/plegados/pedidos — list saved orders, newest first (header fields only)."""
        _HEADER_FIELDS = {
            "id", "cliente", "ref", "cantidad", "material",
            "espesor_mm", "desarrollo_mm", "n_pliegues", "total", "ts",
        }
        try:
            PLEGADOS_PEDIDOS_DIR.mkdir(parents=True, exist_ok=True)
            pedidos = []
            for p in sorted(PLEGADOS_PEDIDOS_DIR.glob("PL-*.json"), reverse=True):
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                    pedidos.append({k: v for k, v in data.items() if k in _HEADER_FIELDS})
                except Exception:
                    pass
            _send_json(self, pedidos)
        except Exception as exc:
            _send_json(self, {"ok": False, "error": str(exc)}, 500)

    def _handle_plegados_pedido_get(self, pedido_id: str) -> None:
        """GET /api/plegados/pedido/<id> — return full order JSON."""
        try:
            pedido_path = PLEGADOS_PEDIDOS_DIR / f"{pedido_id}.json"
            if not pedido_path.exists():
                _send_json(self, {"ok": False, "error": "not found"}, 404)
                return
            data = json.loads(pedido_path.read_text(encoding="utf-8"))
            _send_json(self, data)
        except Exception as exc:
            _send_json(self, {"ok": False, "error": str(exc)}, 500)

    def _handle_presupuestos_list_json(self) -> None:
        """GET /api/presupuestos → JSON list of all presupuestos, newest first (header fields only)."""
        _HEADER_FIELDS = {"numero", "fecha", "customer", "cliente", "job_name", "total"}
        try:
            PRESUPUESTOS_DIR.mkdir(parents=True, exist_ok=True)
            presupuestos = []
            for p in sorted(PRESUPUESTOS_DIR.glob("PRES_*.json"), reverse=True):
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                    presupuestos.append({k: v for k, v in data.items() if k in _HEADER_FIELDS})
                except Exception:
                    pass
            _send_json(self, presupuestos)
        except Exception as exc:
            _send_json(self, {"ok": False, "error": str(exc)}, 500)

    def _handle_presupuesto_get_json(self, name: str) -> None:
        """GET /api/presupuestos/<name> → full JSON of a single presupuesto.

        Accepts both bare IDs ("0029") and prefixed names ("PRES_0029").
        """
        try:
            pres_id = name.removeprefix("PRES_").zfill(4)
            pres_path = PRESUPUESTOS_DIR / f"PRES_{pres_id}.json"
            if not pres_path.exists():
                _send_json(self, {"ok": False, "error": f"PRES_{pres_id} no encontrado"}, 404)
                return
            data = json.loads(pres_path.read_text(encoding="utf-8"))
            _send_json(self, data)
        except Exception as exc:
            _send_json(self, {"ok": False, "error": str(exc)}, 500)

    def _handle_plegados_calcular(self) -> None:
        """POST /api/plegados/calcular — calculates bandeja resources, returns JSON."""
        import sys as _sys
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            data = json.loads(body)
        except Exception as exc:
            _send_json(self, {"ok": False, "error": f"JSON inválido: {exc}"}, 400)
            return
        try:
            ancho_int = float(data["ancho_int"])
            largo_int = float(data["largo_int"])
            alto = float(data["alto"])
            espesor = float(data["espesor"])
            material = str(data.get("material", "")).strip()
        except (KeyError, ValueError) as exc:
            _send_json(self, {"ok": False, "error": f"Parámetros inválidos: {exc}"}, 400)
            return

        if alto <= espesor:
            _send_json(self, {"ok": False, "error": "El alto debe ser mayor al espesor"}, 400)
            return

        # Resolve material_row from MaterialTable
        try:
            table = MaterialTable()
            rows = [r for r in table.list() if r.get("material") == material]
            row = next((r for r in rows if abs(float(r["espesor_mm"]) - espesor) < 1e-6), None)
            if row is None:
                _send_json(self, {"ok": False, "error": f"Material/espesor no encontrado: {material} {espesor}mm"}, 404)
                return
        except Exception as exc:
            _send_json(self, {"ok": False, "error": f"Error al leer materiales: {exc}"}, 500)
            return

        # Import bandeja engine
        plegados_path = str(PLEGADOS_DIR)
        inserted = plegados_path not in _sys.path
        if inserted:
            _sys.path.insert(0, plegados_path)
        try:
            from bandeja import calcular_bandeja, calcular_recursos_bandeja  # type: ignore
            geom = calcular_bandeja(ancho_int, largo_int, alto, espesor)
            recursos = calcular_recursos_bandeja(ancho_int, largo_int, alto, espesor, row)
        except Exception as exc:
            _send_json(self, {"ok": False, "error": str(exc)}, 500)
            return
        finally:
            if inserted and plegados_path in _sys.path:
                _sys.path.remove(plegados_path)

        _send_json(self, {
            "ok": True,
            "blank_ancho": geom["blank_ancho"],
            "blank_largo": geom["blank_largo"],
            "despunte": geom["despunte"],
            "kg_chapa": recursos["kg_chapa"],
            "tiempo_laser_s": recursos["tiempo_laser_s"],
            "perforaciones": 0,
            "plegados": 4,
        })

    def _handle_plegados_dxf(self) -> None:
        """GET /api/plegados/dxf?ancho=&largo=&alto=&espesor=&material=&calibre=&familia=&cantidad="""
        import sys as _sys
        import tempfile as _tempfile
        from urllib.parse import parse_qs, urlparse as _up
        qs = parse_qs(_up(self.path).query)

        def _qf(key):
            v = (qs.get(key) or [""])[0].strip()
            return float(v) if v else None

        ancho_int = _qf("ancho")
        largo_int = _qf("largo")
        alto = _qf("alto")
        espesor = _qf("espesor")
        material = (qs.get("material") or [""])[0].strip()
        calibre = (qs.get("calibre") or [""])[0].strip()
        familia = (qs.get("familia") or [""])[0].strip()
        cantidad = int((qs.get("cantidad") or ["1"])[0].strip() or "1")

        if any(v is None for v in [ancho_int, largo_int, alto, espesor]):
            self.send_error(400)
            return
        if alto <= espesor:
            self.send_error(400)
            return

        plegados_path = str(PLEGADOS_DIR)
        inserted = plegados_path not in _sys.path
        if inserted:
            _sys.path.insert(0, plegados_path)
        try:
            from bandeja import calcular_bandeja, exportar_dxf_bandeja  # type: ignore
            geom = calcular_bandeja(ancho_int, largo_int, alto, espesor)
            with _tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as tmp:
                tmp_path = tmp.name
            exportar_dxf_bandeja(
                geom, tmp_path,
                material=material, calibre=calibre, familia=familia,
                espesor_mm=espesor, cantidad=cantidad,
            )
            payload = Path(tmp_path).read_bytes()
            Path(tmp_path).unlink(missing_ok=True)
        except Exception as exc:
            logger.error("plegados_dxf error: %s", exc)
            self.send_error(500)
            return
        finally:
            if inserted and plegados_path in _sys.path:
                _sys.path.remove(plegados_path)

        mat_safe = re.sub(r"[^A-Za-z0-9]", "_", material) if material else "mat"
        filename = f"Bandeja_{int(ancho_int)}x{int(largo_int)}x{int(alto)}_{mat_safe}_{espesor}mm.dxf"
        self.send_response(200)
        self.send_header("Content-Type", "application/dxf")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    # ------------------------------------------------------------------
    # Lista de cortes unificada
    # ------------------------------------------------------------------

    def _read_lista_corte(self) -> list[dict]:
        f = LISTA_CORTE_FILE
        if not f.exists():
            return []
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _write_lista_corte(self, items: list[dict]) -> None:
        LISTA_CORTE_FILE.parent.mkdir(parents=True, exist_ok=True)
        LISTA_CORTE_FILE.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")

    def _handle_cortes_item_post(self) -> None:
        import uuid as _uuid
        import time as _time
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            item = json.loads(body.decode("utf-8"))
        except Exception:
            self.send_error(400)
            return
        item["id"] = str(_uuid.uuid4())
        item.setdefault("ts", int(_time.time() * 1000))
        items = self._read_lista_corte()
        items.append(item)
        self._write_lista_corte(items)
        _send_json(self, {"ok": True, "id": item["id"]})

    def _handle_cortes_items_list(self) -> None:
        items = self._read_lista_corte()
        items_sorted = sorted(items, key=lambda it: it.get("ts", 0), reverse=True)
        _send_json(self, items_sorted)

    def _handle_cortes_items_clear(self) -> None:
        items = self._read_lista_corte()
        count = len(items)
        self._write_lista_corte([])
        _send_json(self, {"ok": True, "cleared": count})

    def _handle_cortes_item_delete(self, item_id: str) -> None:
        items = self._read_lista_corte()
        new_items = [it for it in items if it.get("id") != item_id]
        if len(new_items) == len(items):
            _send_json(self, {"ok": False, "error": "not found"}, 404)
            return
        self._write_lista_corte(new_items)
        _send_json(self, {"ok": True})

    def _handle_cortes_dxf(self) -> None:
        import tempfile as _tempfile
        import datetime as _dt
        items = self._read_lista_corte()
        if not items:
            _send_json(self, {"error": "lista vacía"}, 400)
            return
        try:
            from sistema_industrial.cutting.dxf_batch_compiler import compile_unified_batch
            with _tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as tmp:
                tmp_path = Path(tmp.name)
            compile_unified_batch(items, tmp_path)
            payload = tmp_path.read_bytes()
            tmp_path.unlink(missing_ok=True)
        except Exception as exc:
            logger.error("cortes_dxf error: %s", exc)
            self.send_error(500)
            return
        today = _dt.date.today().strftime("%Y%m%d")
        filename = f"Cortes_unificados_{today}.dxf"
        self.send_response(200)
        self.send_header("Content-Type", "application/dxf")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args) -> None:
        return


def create_server(host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), PanelSalesHandler)


def run_server(host: str = "127.0.0.1", port: int = 8765) -> None:
    DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _ensure_all_thumbnails()
    server = create_server(host, port)
    try:
        print(f"Nextango Paneles listo: http://{host}:{port}")
        print("Ctrl+C para cerrar.")
    except OSError:
        pass
    server.serve_forever()
