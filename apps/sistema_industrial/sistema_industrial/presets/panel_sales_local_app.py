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
        # Normalise numeric fields
        normalised = {
            "material": str(entry["material"]).strip(),
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

def generate_pattern_thumbnail(pattern_name: str, pattern_data: dict) -> "Path | None":
    """Generate a 300x300px PNG thumbnail for a library pattern.

    Uses a fixed 500x500mm panel with 20mm margin and cut_partial_figures=False.
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
            settings.margin = 10.0
            settings.cut_partial_figures = True

            pattern_type = pattern_data.get("type", "dxf")
            if pattern_type == "tresbolillo" or pattern_name.lower() == "tresbolillo":
                settings.pattern_type = "tresbolillo"
                settings.pattern_name = "Tresbolillo"
                settings.hole_diameter = 20.0
                settings.hole_distance = 60.0
            else:
                file_path = pattern_data.get("file_path", "")
                if not file_path or not Path(file_path).exists():
                    return None
                settings.pattern_type = "dxf"
                settings.pattern_name = pattern_name
                settings.input_file = str(file_path)
                step_x = pattern_data.get("step_x", 84.0)
                step_y = pattern_data.get("step_y", 84.0)
                settings.step_x = float(step_x)
                settings.step_y = float(step_y)

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
                span = geom.end_angle - geom.start_angle
                if span < 0:
                    span += 360  # arcos DXF son siempre CCW
                full_circle = abs(span) >= 359.9
                a0 = _math.radians(geom.start_angle)
                if full_circle:
                    n, total = 64, 2 * _math.pi
                else:
                    rad_span = _math.radians(span) % (2 * _math.pi)
                    n = max(8, int(abs(rad_span) / (2 * _math.pi) * 64))
                    total = _math.radians(span)
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
    return "PANEL_DECORATIVO_LEGACY_TRESBOLILLO"


# ---------------------------------------------------------------------------
# Build input from form (single batch + header) — used for tests
# ---------------------------------------------------------------------------

def build_sales_input(form: dict[str, list[str]]) -> LegacyPanelServiceInput:
    """Build a LegacyPanelServiceInput from a flat HTML form dict (legacy single-batch path)."""
    customer = _first(form, "customer_reference", "CLIENTE-DEMO")
    job_name = _first(form, "job_name", "Panel decorativo")
    panel_mode = _first(form, "panel_mode", "tresbolillo")
    if panel_mode not in ("tresbolillo", "dxf_pattern_grid", "none"):
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

        for batch in batches:
            settings = settings_module.Settings()
            panel_mode = batch["panel_mode"]
            settings.pattern_name = batch["preset_name"]
            settings.material = batch["material"]
            settings.thickness = float(batch["thickness_mm"])
            settings.margin = float(batch["margin_mm"])
            settings.cut_partial_figures = bool(batch["cut_partial_figures"])
            settings.sheet_sizes = [
                (float(w), float(h), int(q))
                for w, h, q in batch["sheet_sizes"]
            ]

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
            else:  # dxf_pattern_grid
                settings.pattern_type = "dxf"
                settings.input_file = batch["pattern_dxf_path"]
                settings.step_x = float(batch["step_x_mm"])
                settings.step_y = float(batch["step_y_mm"])

            stdout = StringIO()
            with redirect_stdout(stdout):
                batch_items = legacy_main.create_cad_result_items_from_batch(settings)
            all_result_items.extend(batch_items)

        arranged = layout_module.arrange_cad_result_items(all_result_items)
        output_dir.mkdir(parents=True, exist_ok=True)
        dxf_path = output_dir / f"{order_id}_legacy_panel.dxf"
        exporter_module.MixedDXFExporter().save(arranged, str(dxf_path))

    finally:
        os.chdir(prev_cwd)
        if inserted:
            try:
                sys.path.remove(legacy_path)
            except ValueError:
                pass

    first_batch = batches[0]
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

    # Look up the material entry for consumed-resource calculations.
    # Material and thickness come from the first batch (all batches share the same
    # material in V1; a per-item lookup could be done if that changes later).
    _mat_table = MaterialTable()
    _mat_key_material = first_input.material
    _mat_key_espesor = first_input.thickness_mm
    _mat_entry = next(
        (
            e for e in _mat_table.list()
            if e["material"] == _mat_key_material
            and float(e["espesor_mm"]) == _mat_key_espesor
        ),
        None,
    )
    _consumed_resources_warning: str | None = (
        None
        if _mat_entry is not None
        else (
            f"Material '{_mat_key_material}' con espesor {_mat_key_espesor} mm "
            f"no está en la tabla de materiales. "
            f"Agregar la entrada en /admin para obtener recursos consumidos."
        )
    )

    all_resources = []
    for item in all_result_items:
        cut_length_mm = calculate_cut_length_mm(item.geometry_items)
        pierce_count = calculate_pierce_count(item.geometry_items)
        sheet_area_m2 = calculate_sheet_area_m2(item.occupied_width, item.occupied_height)
        if _mat_entry is not None:
            consumed = calculate_consumed_resources(
                cut_length_m=cut_length_mm / 1000.0,
                pierce_count=pierce_count,
                sheet_area_m2=sheet_area_m2,
                material_entry=_mat_entry,
            )
        else:
            consumed = None
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
                "pierce_count": pierce_count,
                "bend_count": item.bend_count,
                "consumed_resources": consumed,
                "consumed_resources_warning": _consumed_resources_warning,
            }
        )

    warnings: list[str] = []
    if any(r["cut_length_mm"] == 0 for r in all_resources):
        warnings.append("Legacy engine returned cut_length_mm=0; preserving legacy value.")
    if any(r["pierce_count"] == 0 for r in all_resources):
        warnings.append("Legacy engine returned pierce_count=0; preserving legacy value.")
    if _consumed_resources_warning:
        warnings.append(_consumed_resources_warning)

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
        legacy_result_raw={"batches": len(batches), "total_items": len(all_result_items)},
        cut_piece_payload=cut_piece_payload,
        quotation_payload=quotation_payload,
    )

    manifest_path = write_panel_service_outputs(service_result, output_dir)
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
  .admin-badge { background:rgba(255,255,255,.15); border:1px solid rgba(255,255,255,.3); color:rgba(255,255,255,.9); font-size:11px; font-weight:700; letter-spacing:1px; text-transform:uppercase; padding:3px 10px; border-radius:12px; }
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
"""

_TOPBAR_MAIN_HTML = """
<header class="topbar">
  <div class="logo">SistemaIndustrial</div>
  <nav><a href="/" class="active">Paneles Decorativos</a></nav>
  <div class="spacer"></div>
  <a href="/admin" class="admin-link">Administrar patrones</a>
</header>
"""

_TOPBAR_ADMIN_HTML = """
<header class="topbar">
  <div class="logo">SistemaIndustrial</div>
  <nav><a href="/">Paneles Decorativos</a></nav>
  <div class="spacer"></div>
  <span class="admin-badge">Admin</span>
  <a href="/materiales" class="admin-link">Tabla de materiales</a>
  <a href="/" class="back-link">Volver al catalogo</a>
</header>
"""


# ---------------------------------------------------------------------------
# render_form — main gallery page (Steps 1-3 + batch list + generate)
# ---------------------------------------------------------------------------

def render_form(error: str = "", result: SalesRunResult | None = None) -> str:
    """Render the main gallery page."""

    result_section = ""
    if result is not None:
        data = result.service_result
        resources_html = "".join(
            "<tr>"
            f"<td>{escape(str(row['name']))}</td>"
            f"<td>{escape(str(row['quantity']))}</td>"
            f"<td>{escape(str(row['occupied_width_mm']))} x {escape(str(row['occupied_height_mm']))}</td>"
            f"<td>{escape(str(row['geometry_item_count']))}</td>"
            "</tr>"
            for row in data.calculated_resources
        )
        warnings_html = (
            "".join(f"<li>{escape(w)}</li>" for w in data.warnings)
            or "<li>Sin advertencias.</li>"
        )
        dxf_rel = escape(data.dxf_path.name)

        # ---- Consumed-resources panel ----------------------------------------
        # Show resources per-panel-type (one section per item in calculated_resources).
        # consumed_resources values are TOTALS for the batch — divide by quantity for per-piece.
        _grand_kg = 0.0
        _grand_seconds = 0.0
        _grand_pierces = 0
        _grand_consumibles = 0.0
        _any_with_data = False
        _any_null = False

        _type_sections: list[str] = []
        for row in data.calculated_resources:
            cr = row.get("consumed_resources")
            qty = max(int(row.get("quantity", 1)), 1)
            panel_name = escape(str(row.get("name", "Panel")))
            w_mm = row.get("occupied_width_mm", "?")
            h_mm = row.get("occupied_height_mm", "?")
            dims = f"{w_mm}×{h_mm} mm"

            if cr is None:
                _any_null = True
                _type_sections.append(
                    f'<div class="consumed-type-block consumed-warn" style="margin-bottom:10px">'
                    f'<span class="consumed-warn-icon">&#9888;</span>'
                    f'<span><strong>{panel_name}</strong> &mdash; {escape(dims)}'
                    f' <span style="color:#999">(x{qty})</span><br>'
                    f'Carga los datos de <strong>{escape(str(row.get("material","?")))}'
                    f' {escape(str(row.get("thickness_mm","?")))}&nbsp;mm</strong>'
                    f' en <a href="/materiales" style="color:inherit;font-weight:700">/materiales</a>'
                    f' para ver los recursos consumidos.</span>'
                    f'</div>'
                )
            else:
                _any_with_data = True
                kg_total = float(cr.get("material_kg", 0.0))
                sec_total = float(cr.get("machine_seconds", 0.0))
                prc_total = int(cr.get("pierce_count", 0))
                con_total = float(cr.get("consumibles_used", 0.0))

                kg_pp = kg_total / qty
                sec_pp = sec_total / qty
                prc_pp = prc_total / qty
                con_pp = con_total / qty

                _grand_kg += kg_total
                _grand_seconds += sec_total
                _grand_pierces += prc_total
                _grand_consumibles += con_total

                _m = int(sec_pp) // 60
                _s = int(sec_pp) % 60
                time_pp_str = f"{_m} min {_s:02d} s"

                _type_sections.append(
                    f'<div class="consumed-type-block" style="margin-bottom:14px">'
                    f'<div class="consumed-type-header">'
                    f'<strong>{panel_name}</strong>'
                    f' &mdash; {escape(dims)}'
                    f' <span class="consumed-qty-badge">x{qty} unidades</span>'
                    f'</div>'
                    f'<table class="consumed-table" style="margin-top:6px">'
                    f'<tr><td class="consumed-label">Material</td>'
                    f'<td class="consumed-val">{kg_pp:.3f} kg / pieza</td></tr>'
                    f'<tr><td class="consumed-label">Tiempo maq.</td>'
                    f'<td class="consumed-val">{time_pp_str} / pieza</td></tr>'
                    f'<tr><td class="consumed-label">Perforaciones</td>'
                    f'<td class="consumed-val">{prc_pp:.0f} / pieza</td></tr>'
                    f'</table>'
                    f'</div>'
                )

        _sections_html = "\n".join(_type_sections)

        # Grand total footer — only show when there are multiple items with data
        _footer_html = ""
        if _any_with_data and len([r for r in data.calculated_resources if r.get("consumed_resources") is not None]) > 1:
            _gm = int(_grand_seconds) // 60
            _gs = int(_grand_seconds) % 60
            _footer_html = (
                f'<div class="consumed-total-row">'
                f'Total del pedido: <strong>{_grand_kg:.2f} kg</strong>'
                f' &mdash; <strong>{_gm} min {_gs:02d} s</strong>'
                f' &mdash; <strong>{_grand_pierces} perforaciones</strong>'
                f'</div>'
            )

        if not _any_with_data and _any_null:
            # All items lack material data — compact warning only
            consumed_panel_html = (
                f'<div class="consumed-panel consumed-warn">\n'
                f'{_sections_html}\n'
                f'</div>'
            )
        else:
            consumed_panel_html = (
                f'<div class="consumed-panel">\n'
                f'<div class="consumed-title">Recursos consumidos — por pieza</div>\n'
                f'{_sections_html}\n'
                f'{_footer_html}\n'
                f'</div>'
            )
        # ---- end consumed-resources panel -----------------------------------

        result_section = f"""
  <div class="card" id="result-card">
    <div class="card-title">Resultado generado</div>
    <div style="margin-bottom:14px">
      <a href="/outputs/{dxf_rel}" target="_blank"
         style="display:inline-block;padding:8px 16px;background:var(--accent2);color:#fff;border-radius:6px;text-decoration:none;font-weight:700;font-size:13px">
        Descargar DXF
      </a>
    </div>
    {consumed_panel_html}
    <table class="batch-table" style="margin-top:16px">
      <thead><tr><th>Recurso</th><th>Cantidad</th><th>Ocupacion mm</th><th>Geometria</th></tr></thead>
      <tbody>{resources_html}</tbody>
    </table>
    <h3 style="margin:14px 0 6px;font-size:13px">Advertencias</h3>
    <ul style="padding-left:18px;font-size:13px">{warnings_html}</ul>
  </div>"""

    error_html = f'<div class="error-box">{escape(error)}</div>' if error else ""

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
    .pattern-grid {{ display:flex; flex-wrap:wrap; gap:16px; }}
    .pattern-card {{ display:flex; flex-direction:column; align-items:center; cursor:pointer; border-radius:8px; border:2px solid #e0e0e0; padding:10px; background:#fafafa; transition:border-color .18s,box-shadow .18s; width:170px; user-select:none; }}
    .pattern-card:hover {{ border-color:var(--brand); box-shadow:0 2px 12px rgba(23,107,135,.18); }}
    .pattern-card.selected {{ border-color:var(--brand); background:#e8f4f8; box-shadow:0 0 0 3px rgba(23,107,135,.15); }}
    .pattern-thumb {{ width:150px; height:150px; background:#d0d8e0; border-radius:6px; display:flex; align-items:center; justify-content:center; overflow:hidden; }}
    .pattern-thumb img {{ width:150px; height:150px; object-fit:cover; border-radius:6px; }}
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
    /* Material dropdown */
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
  </style>
</head>
<body>
{_TOPBAR_MAIN_HTML}
<div class="page-wrapper">
  <h1 class="page-title">Nuevo pedido — Paneles Decorativos</h1>
  {error_html}

  <!-- Stepper indicator -->
  <div class="stepper" id="stepper">
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
  <div class="card" id="step1">
    <div class="card-title">1 — Elegi un patron</div>
    <div class="pattern-grid" id="pattern-grid">
      <!-- Tresbolillo — always first, built-in -->
      <div class="pattern-card" id="pcard-tresbolillo"
           onclick="selectPattern('tresbolillo','Tresbolillo','tresbolillo',null,null,null)">
        <div class="pattern-thumb thumb-tres">
          <svg width="100" height="100" viewBox="0 0 100 100" opacity=".5">
            <circle cx="20" cy="20" r="7" fill="#7a9aaa"/>
            <circle cx="50" cy="20" r="7" fill="#7a9aaa"/>
            <circle cx="80" cy="20" r="7" fill="#7a9aaa"/>
            <circle cx="35" cy="44" r="7" fill="#7a9aaa"/>
            <circle cx="65" cy="44" r="7" fill="#7a9aaa"/>
            <circle cx="20" cy="68" r="7" fill="#7a9aaa"/>
            <circle cx="50" cy="68" r="7" fill="#7a9aaa"/>
            <circle cx="80" cy="68" r="7" fill="#7a9aaa"/>
            <circle cx="35" cy="92" r="7" fill="#7a9aaa"/>
            <circle cx="65" cy="92" r="7" fill="#7a9aaa"/>
          </svg>
        </div>
        <div class="pattern-name">Tresbolillo</div>
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

    <!-- Margen -->
    <div class="form-row">
      <div class="form-group">
        <label for="p-margen">Margen mm <span style="font-weight:400;color:#888">(borde sin perforar)</span></label>
        <input type="number" id="p-margen" placeholder="ej. 20" min="0" value="20">
        <div class="field-hint">La zona sin agujeros alrededor de todo el contorno.</div>
      </div>
      <div class="form-group"></div>
    </div>

    <!-- Modo de distribucion -->
    <div class="form-row">
      <div class="form-group">
        <label>Modo de distribucion</label>
        <div class="radio-group" id="dist-group">
          <label class="checked-option" id="lbl-centradas" onclick="setDist('centradas')">
            <input type="radio" name="distrib" value="centradas" checked>
            Figuras completas centradas
          </label>
          <label id="lbl-cortar" onclick="setDist('cortar')">
            <input type="radio" name="distrib" value="cortar">
            Cortar en borde
          </label>
        </div>
        <div class="field-hint">"Figuras completas": ningun agujero queda cortado por el borde. "Cortar en borde": agujeros a medio corte en extremos.</div>
      </div>
    </div>

    <!-- Material y Espesor — dropdown poblado desde /api/materials -->
    <div class="mat-dropdown-row">
      <div class="form-group">
        <label for="p-mat-combo">Material / Espesor</label>
        <select id="p-mat-combo" onchange="onMatComboChange(this)">
          <option value="" disabled selected>Cargando materiales...</option>
        </select>
      </div>
      <button class="btn-refresh" title="Actualizar lista de materiales" onclick="loadMaterialDropdown()">&#8635;</button>
    </div>
    <!-- Hidden fields used by addBatch() to build the batch object -->
    <input type="hidden" id="p-material" value="">
    <input type="hidden" id="p-espesor" value="">

    <!-- Cantidad / Ancho / Alto en una fila -->
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
    </div>

    <!-- Offset DXF: oculto, tomado de la librería al seleccionar el patrón -->
    <div style="display:none" id="block-dxf-offset">
      <input type="hidden" id="p-offset-x" value="84">
      <input type="hidden" id="p-offset-y" value="84">
    </div>

    <div id="batch-error" class="error-box hidden" style="margin-top:8px"></div>
    <button class="btn-add" onclick="addBatch()">+ AGREGAR A LA LISTA</button>
  </div>

  <!-- Lista de lotes + GENERAR (oculto hasta agregar al menos un lote) -->
  <div class="card hidden" id="section-batches">
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
var batches = [];

// ---- Load material dropdown from /api/materials ----
function loadMaterialDropdown() {{
  var sel = document.getElementById('p-mat-combo');
  var btnAdd = document.querySelector('.btn-add');
  sel.innerHTML = '<option value="" disabled selected>Cargando...</option>';
  fetch('/api/materials')
    .then(function(r) {{ return r.json(); }})
    .then(function(data) {{
      sel.innerHTML = '';
      if (!data || data.length === 0) {{
        var opt = document.createElement('option');
        opt.value = '';
        opt.disabled = true;
        opt.selected = true;
        opt.textContent = '— Carga materiales en /materiales —';
        sel.appendChild(opt);
        if (btnAdd) {{ btnAdd.disabled = true; btnAdd.title = 'Carga materiales en /materiales primero'; }}
        document.getElementById('p-material').value = '';
        document.getElementById('p-espesor').value = '';
        return;
      }}
      var placeholder = document.createElement('option');
      placeholder.value = '';
      placeholder.disabled = true;
      placeholder.selected = true;
      placeholder.textContent = 'Selecciona material y espesor...';
      sel.appendChild(placeholder);
      data.forEach(function(entry) {{
        var opt = document.createElement('option');
        opt.value = JSON.stringify({{material: entry.material, espesor_mm: entry.espesor_mm}});
        opt.textContent = entry.material + ' — ' + entry.espesor_mm + ' mm';
        sel.appendChild(opt);
      }});
      if (btnAdd) {{ btnAdd.disabled = false; btnAdd.title = ''; }}
      // Clear hidden fields until user picks
      document.getElementById('p-material').value = '';
      document.getElementById('p-espesor').value = '';
    }})
    .catch(function() {{
      sel.innerHTML = '<option value="" disabled selected>Error al cargar materiales</option>';
      if (btnAdd) {{ btnAdd.disabled = true; }}
    }});
}}

function onMatComboChange(sel) {{
  if (!sel.value) return;
  try {{
    var parsed = JSON.parse(sel.value);
    document.getElementById('p-material').value = parsed.material;
    document.getElementById('p-espesor').value = parsed.espesor_mm;
  }} catch(e) {{
    document.getElementById('p-material').value = '';
    document.getElementById('p-espesor').value = '';
  }}
}}

// Load dropdown on page mount
loadMaterialDropdown();

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
    setTimeout(function() {{
      document.getElementById('tres-inline').scrollIntoView({{behavior:'smooth', block:'nearest'}});
    }}, 60);
  }} else {{
    // DXF pattern: save state and advance to step 2 directly
    selectedPattern = {{mode:mode, name:name, ptype:ptype, file_path:file_path, step_x:step_x, step_y:step_y}};
    if (step_x) document.getElementById('p-offset-x').value = step_x;
    if (step_y) document.getElementById('p-offset-y').value = step_y;
    document.getElementById('tres-inline').style.display = 'none';
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
    var patDesc = b.panel_mode === 'tresbolillo'
      ? b.preset_name + ' <span style="color:#aaa;font-size:11px">d=' + b.hole_diameter_mm + ' sep=' + b.hole_distance_mm + '</span>'
      : b.preset_name + ' <span style="color:#aaa;font-size:11px">DXF ' + b.step_x_mm + ',' + b.step_y_mm + '</span>';
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

    # Material table rows
    try:
        mat_entries = MaterialTable().list()
    except Exception:
        mat_entries = []

    mat_rows_html = ""
    if not mat_entries:
        mat_rows_html = (
            '<tr><td colspan="7" style="text-align:center;color:#aaa;font-style:italic;padding:18px">'
            "Sin materiales cargados.</td></tr>"
        )
    else:
        for entry in mat_entries:
            mat_json = json.dumps({"material": entry["material"], "espesor_mm": entry["espesor_mm"]})
            mat_rows_html += f"""
      <tr>
        <td>{escape(str(entry['material']))}</td>
        <td style="text-align:right">{escape(str(entry['espesor_mm']))}</td>
        <td style="text-align:right">{escape(str(entry['densidad_kg_m2']))}</td>
        <td style="text-align:right">{escape(str(entry['velocidad_corte_mm_s']))}</td>
        <td style="text-align:right">{escape(str(entry['tiempo_perforacion_s']))}</td>
        <td style="text-align:right">{escape(str(entry['consumible_por_perforacion']))}</td>
        <td>
          <button class="btn-action btn-del" onclick="deleteMaterial({mat_json}, this)">Borrar</button>
        </td>
      </tr>"""

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
        rows_html += f"""
    <tr>
      <td>{thumb_html}</td>
      <td><strong>{safe_name}</strong>{restricted_badge_html}<br>
          <span style="font-size:11px;color:#aaa">offset {step_x} &times; {step_y} mm</span>{restricted_note_html}</td>
      <td><span class="type-badge type-dxf">DXF</span></td>
      <td>
        <button class="btn-action btn-del" data-pattern-name="{safe_name}" onclick="deletePattern(this.dataset.patternName, this)">Borrar</button>
      </td>
    </tr>"""

    total = len(patterns) + 1  # +1 for Tresbolillo
    mat_count = len(mat_entries)

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
{_TOPBAR_ADMIN_HTML}
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
        <input type="number" id="admin-offset-x" placeholder="84" step="0.1" value="84">
      </div>
      <div class="form-group">
        <label for="admin-offset-y">Offset Y mm</label>
        <input type="number" id="admin-offset-y" placeholder="84" step="0.1" value="84">
      </div>
      <div class="form-group"></div>
    </div>
    <div style="margin-top:-10px;margin-bottom:16px">
      <span class="field-hint">Distancia entre la celda DXF y la siguiente repeticion en cada eje.</span>
    </div>

    <hr class="form-divider">
    <button class="btn-upload" onclick="uploadPattern()">CARGAR Y GENERAR PREVIEW</button>

    <div id="admin-feedback" class="hidden"></div>
  </div>

  <!-- ================================================================== -->
  <!-- TABLA DE MATERIALES                                                  -->
  <!-- ================================================================== -->
  <div class="card" style="margin-top:32px">
    <div class="card-title" style="display:flex;justify-content:space-between">
      <span>Tabla de materiales</span>
      <span style="font-size:12px;color:#888;font-weight:400;letter-spacing:0;text-transform:none">{mat_count} material(es)</span>
    </div>
    <table class="patterns-table" id="materials-table">
      <thead>
        <tr>
          <th>Material</th>
          <th style="text-align:right">Espesor mm</th>
          <th style="text-align:right">Densidad kg/m²</th>
          <th style="text-align:right">Vel. corte mm/s</th>
          <th style="text-align:right">T. perforación s</th>
          <th style="text-align:right">Consumible/perf.</th>
          <th>Acciones</th>
        </tr>
      </thead>
      <tbody id="materials-tbody">{mat_rows_html}</tbody>
    </table>
  </div>

  <!-- Formulario: agregar material -->
  <div class="card">
    <div class="card-title">Agregar material</div>
    <div class="form-row">
      <div class="form-group">
        <label for="mat-material">Material</label>
        <input type="text" id="mat-material" placeholder="ej. Acero negro">
      </div>
      <div class="form-group">
        <label for="mat-espesor">Espesor mm</label>
        <input type="number" id="mat-espesor" placeholder="ej. 2" min="0.01" step="0.01">
      </div>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label for="mat-densidad">Densidad kg/m²</label>
        <input type="number" id="mat-densidad" placeholder="ej. 15.7" min="0" step="0.01">
        <div class="field-hint">kg por metro cuadrado de chapa.</div>
      </div>
      <div class="form-group">
        <label for="mat-velocidad">Vel. corte mm/s</label>
        <input type="number" id="mat-velocidad" placeholder="ej. 83.3" min="0.01" step="0.01">
        <div class="field-hint">Velocidad de corte en mm por segundo.</div>
      </div>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label for="mat-pierce">T. perforación s</label>
        <input type="number" id="mat-pierce" placeholder="ej. 0.5" min="0" step="0.01">
        <div class="field-hint">Segundos por perforación (pierce delay).</div>
      </div>
      <div class="form-group">
        <label for="mat-consumible">Consumible/perf.</label>
        <input type="number" id="mat-consumible" placeholder="ej. 0.05" min="0" step="0.001">
        <div class="field-hint">Factor de desgaste de boquilla por perforación.</div>
      </div>
    </div>
    <div id="mat-feedback" class="hidden"></div>
    <button class="btn-upload" onclick="addMaterial()">AGREGAR MATERIAL</button>
  </div>

</div><!-- /page-wrapper -->

<script>
function browseAdminDxf() {{
  fetch('/api/browse-dxf')
    .then(function(r) {{ return r.json(); }})
    .then(function(d) {{ if (d.path) document.getElementById('admin-dxf-path').value = d.path; }})
    .catch(function() {{}});
}}

function uploadPattern() {{
  var nombre  = document.getElementById('admin-nombre').value.trim();
  var dxfPath = document.getElementById('admin-dxf-path').value.trim();
  var ox = document.getElementById('admin-offset-x').value;
  var oy = document.getElementById('admin-offset-y').value;
  if (!nombre)  {{ showFeedback('error','Campo requerido','El nombre del patron es obligatorio.'); return; }}
  if (!dxfPath) {{ showFeedback('error','Campo requerido','Selecciona un archivo DXF.'); return; }}
  showFeedback('loading','Generando preview...','Validando y procesando el archivo DXF. Puede tardar unos segundos.');
  var fd = new FormData();
  fd.append('name', nombre); fd.append('file_path', dxfPath);
  fd.append('step_x', ox);   fd.append('step_y', oy);
  fetch('/api/patterns/add', {{method:'POST', body:fd}})
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
    }})
    .catch(function(e) {{ showFeedback('error','Error de red', String(e)); }});
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
<header class="topbar">
  <div class="logo">SistemaIndustrial</div>
  <nav><a href="/">Paneles Decorativos</a></nav>
  <div class="spacer"></div>
  <a href="/admin" class="back-link">Volver a Admin</a>
</header>
<div class="page-wrapper">
  <h1 class="page-title">Tabla de materiales</h1>
  <div class="card">
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
// Init
// ---------------------------------------------------------------------------
loadMaterials();
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
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self._send_html(render_form())
            return

        if parsed.path == "/admin":
            self._send_html(render_admin())
            return

        if parsed.path == "/materiales":
            self._send_html(render_materiales())
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

        if parsed.path.startswith("/outputs/"):
            rel = parsed.path.removeprefix("/outputs/")
            path = self.output_dir / Path(rel)
            if not path.exists() or not path.is_file():
                self.send_error(404)
                return
            payload = path.read_bytes()
            content_type = "application/json" if path.suffix == ".json" else "application/octet-stream"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        self.send_error(404)

    def do_POST(self) -> None:
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

        self.send_error(404)

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/api/materials":
            self._handle_material_delete()
            return

        self.send_error(404)

    def _handle_generate(self) -> None:
        try:
            form = _parse_post_form(self)
            batches_json = _first(form, "batches_json", "")
            customer = _first(form, "customer_reference", "CLIENTE-DEMO")
            job_name = _first(form, "job_name", "Panel decorativo")
            observations = _first(form, "observations", "")

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
