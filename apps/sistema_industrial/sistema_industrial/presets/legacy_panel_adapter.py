"""Adapter for the legacy decorative panel engine.

The legacy folder is treated as a black-box implementation. This module only
loads its public functions, builds the Settings object it already expects and
asks the legacy exporter to write the DXF.
"""

from __future__ import annotations

from contextlib import contextmanager, redirect_stdout
from dataclasses import dataclass, field
from importlib import import_module
from io import StringIO
from pathlib import Path
import math
import os
import sys


DEFAULT_LEGACY_DIR = Path(__file__).resolve().parents[4] / "Programas_hechos" / "Panel Decorativo"
LEGACY_PATTERN_TYPES = {"tresbolillo", "dxf", "none"}


# ---------------------------------------------------------------------------
# Geometry resource calculators
# These functions work on the geometry_items list returned by the legacy engine
# (list of Piece and Polyline objects). They use duck-typing / class name checks
# so they don't require importing the legacy classes directly.
# ---------------------------------------------------------------------------


def _arc_length_mm(entity) -> float:
    """Return the arc length of an ArcSegment in mm.

    The arc goes CCW from start_angle to end_angle (degrees).
    If end_angle < start_angle, add 360 to get the positive sweep.
    """
    sweep = entity.end_angle - entity.start_angle
    if sweep < 0:
        sweep += 360.0
    return entity.radius * math.radians(sweep)


def _line_length_mm(entity) -> float:
    """Return the Euclidean length of a LineSegment in mm."""
    dx = entity.x2 - entity.x1
    dy = entity.y2 - entity.y1
    return math.sqrt(dx * dx + dy * dy)


def _polyline_length_mm(poly) -> float:
    """Return the total length of all consecutive segments in a Polyline."""
    total = 0.0
    pts = poly.points
    for i in range(len(pts) - 1):
        dx = pts[i + 1][0] - pts[i][0]
        dy = pts[i + 1][1] - pts[i][1]
        total += math.sqrt(dx * dx + dy * dy)
    return total


def calculate_cut_length_mm(geometry_items) -> float:
    """Sum the total cut length (mm) of all geometry items.

    Handles closed figures (Piece or Figure — both have an .entities list of
    ArcSegment and LineSegment objects) and Polyline objects (sheet outline and
    border paths). Unknown types are silently ignored.

    Note: the legacy engine uses the class name "Figure" for closed perforated
    shapes, not "Piece", so we detect closed figures by the presence of the
    .entities attribute rather than by class name.
    """
    total = 0.0
    for item in geometry_items:
        cls_name = type(item).__name__
        if hasattr(item, "entities"):
            # Closed figure (Figure or Piece): sum all segment lengths
            for entity in item.entities:
                ename = type(entity).__name__
                if ename == "ArcSegment":
                    total += _arc_length_mm(entity)
                elif ename == "LineSegment":
                    total += _line_length_mm(entity)
        elif cls_name == "Polyline":
            total += _polyline_length_mm(item)
    return total


def calculate_pierce_count(geometry_items) -> int:
    """Count the number of closed figure objects (perforations).

    The legacy engine emits Figure objects (not Piece) for closed perforated
    shapes. Both share the .entities interface, so we detect closed figures by
    the presence of .entities rather than by class name.  Polyline objects (the
    sheet outline) do not have .entities and are excluded.
    """
    return sum(1 for item in geometry_items if hasattr(item, "entities"))


def calculate_sheet_area_m2(width_mm: float, height_mm: float) -> float:
    """Return the sheet area in square metres."""
    return (width_mm * height_mm) / 1_000_000.0


def validate_dxf_entities(file_path: str) -> tuple[bool, str]:
    """Validate that a DXF file only contains entities supported by the panel engine.

    Supported entity types: LINE, CIRCLE, ARC.

    Returns:
        (True, "")  — file is valid.
        (False, "mensaje detallado")  — unsupported entities found, or file
        could not be read. The message is suitable for display to the operator.
    """
    from sistema_industrial.presets.dxf_validator import (
        UnsupportedDXFEntitiesError,
        validate_dxf_entities as _validate,
    )
    try:
        _validate(Path(file_path))
        return True, ""
    except UnsupportedDXFEntitiesError as exc:
        return False, str(exc)
    except Exception as exc:
        return False, f"No se pudo leer el archivo DXF: {exc}"


@dataclass(frozen=True)
class LegacyPanelRunRequest:
    preset_code: str
    preset_name: str
    material: str
    thickness_mm: float
    width_mm: float
    height_mm: float
    quantity: int
    output_dxf_path: Path
    pattern_type: str = "tresbolillo"
    cut_partial_figures: bool = True
    margin_mm: float = 20.0
    hole_diameter_mm: float = 20.0
    hole_distance_mm: float = 60.0
    pattern_dxf_path: Path | None = None
    step_x_mm: float | None = None
    step_y_mm: float | None = None
    rows: int | None = None
    columns: int | None = None
    # Optional override: list of (width_mm, height_mm, quantity) tuples.
    # When set, overrides width_mm/height_mm/quantity for multi-piece batches.
    sheet_sizes: list | None = None


@dataclass(frozen=True)
class LegacyPanelRunResult:
    dxf_path: Path
    calculated_resources: list[dict]
    warnings: list[str] = field(default_factory=list)
    legacy_result_raw: dict = field(default_factory=dict)


def find_legacy_panel_dir(repo_root: Path | None = None) -> Path:
    """Locate the Panel Decorativo engine directory.

    Searches in priority order:
    1. Explicit repo_root argument
    2. parents[4] of this file (normal repo layout)
    3. Any ancestor of parents[4] that contains Programas_hechos (covers git
       worktrees where the file lives in a subdirectory of the real repo root)
    """
    if repo_root is not None:
        candidate = repo_root / "Programas_hechos" / "Panel Decorativo"
        if candidate.exists() and (candidate / "main.py").exists():
            return candidate
        raise FileNotFoundError(f"Legacy panel engine not found under repo_root: {candidate}")

    # Walk up from the file location to find the engine
    start = Path(__file__).resolve().parents[4]
    search_path = start
    for _ in range(6):  # Walk up at most 6 more levels
        candidate = search_path / "Programas_hechos" / "Panel Decorativo"
        if candidate.exists() and (candidate / "main.py").exists():
            return candidate
        parent = search_path.parent
        if parent == search_path:
            break
        search_path = parent

    raise FileNotFoundError(
        f"Legacy panel engine 'Programas_hechos/Panel Decorativo' not found. "
        f"Searched from: {start}"
    )


@contextmanager
def _legacy_import_context(legacy_dir: Path):
    previous_cwd = Path.cwd()
    legacy_path = str(legacy_dir)
    inserted = False
    if legacy_path not in sys.path:
        sys.path.insert(0, legacy_path)
        inserted = True
    os.chdir(legacy_dir)
    try:
        yield
    finally:
        os.chdir(previous_cwd)
        if inserted:
            try:
                sys.path.remove(legacy_path)
            except ValueError:
                pass


def _build_settings(settings_class, request: LegacyPanelRunRequest):
    settings = settings_class()
    if request.pattern_type not in LEGACY_PATTERN_TYPES:
        raise ValueError(f"Unsupported legacy panel pattern_type: {request.pattern_type}")
    settings.pattern_name = request.preset_name
    settings.material = request.material
    settings.thickness = request.thickness_mm
    settings.margin = request.margin_mm
    settings.cut_partial_figures = request.cut_partial_figures
    settings.output_file = str(request.output_dxf_path)

    # Multi-piece batch support: sheet_sizes overrides single width/height/quantity
    if request.sheet_sizes:
        settings.sheet_sizes = list(request.sheet_sizes)
    else:
        settings.sheet_sizes = [(request.width_mm, request.height_mm, request.quantity)]

    if request.pattern_type == "none":
        # No-perforate mode: produce only the rectangular outline.
        # Strategy: set cut_partial_figures=False so the engine calls
        # generate_centered_full_mode_geometry, then use an enormous hole
        # diameter so the pattern is larger than the usable area — the engine
        # returns early with only the sheet outline.
        settings.pattern_type = "tresbolillo"
        settings.cut_partial_figures = False
        max_dim = max(
            max(w for w, h, _ in settings.sheet_sizes),
            max(h for w, h, _ in settings.sheet_sizes),
        )
        settings.hole_diameter = max_dim * 2
        settings.hole_distance = max_dim * 4
        return settings

    settings.pattern_type = request.pattern_type

    if request.pattern_type == "tresbolillo":
        settings.hole_diameter = request.hole_diameter_mm
        settings.hole_distance = request.hole_distance_mm
        return settings

    if request.pattern_type == "dxf":
        if request.pattern_dxf_path is None:
            raise ValueError("pattern_dxf_path is required for legacy DXF patterns")
        if not request.pattern_dxf_path.exists():
            raise FileNotFoundError(f"Pattern DXF not found: {request.pattern_dxf_path}")
        if request.step_x_mm is None or request.step_y_mm is None:
            raise ValueError("step_x_mm and step_y_mm are required for legacy DXF patterns")
        settings.input_file = str(request.pattern_dxf_path)
        settings.step_x = request.step_x_mm
        settings.step_y = request.step_y_mm
        return settings

    raise ValueError(f"Unsupported legacy panel pattern_type: {request.pattern_type}")


def _resource_payload(item) -> dict:
    # Always recalculate from geometry — the legacy engine hard-codes 0 for
    # cut_length_mm and pierce_count, so we override them here.
    computed_cut_length_mm = calculate_cut_length_mm(item.geometry_items)
    computed_pierce_count = calculate_pierce_count(item.geometry_items)
    computed_sheet_area_m2 = calculate_sheet_area_m2(item.occupied_width, item.occupied_height)
    return {
        "name": item.name,
        "material": item.material,
        "thickness_mm": item.thickness,
        "quantity": item.quantity,
        "occupied_width_mm": item.occupied_width,
        "occupied_height_mm": item.occupied_height,
        "geometry_item_count": len(item.geometry_items),
        "cut_length_mm": computed_cut_length_mm,
        "cut_length_m": computed_cut_length_mm / 1000.0,
        "pierce_count": computed_pierce_count,
        "sheet_area_m2": computed_sheet_area_m2,
        "bend_count": item.bend_count,
    }


def _raw_request_payload(request: LegacyPanelRunRequest) -> dict:
    return {
        "preset_code": request.preset_code,
        "preset_name": request.preset_name,
        "material": request.material,
        "thickness_mm": request.thickness_mm,
        "width_mm": request.width_mm,
        "height_mm": request.height_mm,
        "quantity": request.quantity,
        "pattern_type": request.pattern_type,
        "margin_mm": request.margin_mm,
        "cut_partial_figures": request.cut_partial_figures,
        "pattern_dxf_path": str(request.pattern_dxf_path) if request.pattern_dxf_path else None,
        "offset_x_mm": request.step_x_mm,
        "offset_y_mm": request.step_y_mm,
        "step_x_mm": request.step_x_mm,
        "step_y_mm": request.step_y_mm,
        "rows": request.rows,
        "columns": request.columns,
        "sheet_sizes": request.sheet_sizes,
    }


def get_pattern_library_patterns(legacy_dir: Path | None = None) -> dict:
    """Return the current contents of the pattern library as a dict."""
    engine_dir = legacy_dir or find_legacy_panel_dir()
    with _legacy_import_context(engine_dir):
        lib_module = import_module("config.pattern_library")
        lib = lib_module.PatternLibrary()
        return dict(lib.patterns)


def add_pattern_to_library(
    name: str,
    file_path: str,
    step_x: float,
    step_y: float,
    legacy_dir: Path | None = None,
    restricted: bool = False,
    restricted_reason: str = "",
) -> None:
    """Add a DXF pattern to the pattern library.

    When *restricted* is False (default), validates the DXF for unsupported
    entities before registering it and raises UnsupportedDXFEntitiesError if
    splines, ellipses, or other non-supported types are found.

    When *restricted* is True the validation step is skipped — the caller has
    already detected the unsupported entities and decided to accept the pattern
    in restricted mode.  *restricted_reason* is stored alongside the pattern so
    the UI can display a meaningful warning.
    """
    if not restricted:
        from sistema_industrial.presets.dxf_validator import validate_dxf_entities
        validate_dxf_entities(Path(file_path))

    engine_dir = legacy_dir or find_legacy_panel_dir()
    with _legacy_import_context(engine_dir):
        lib_module = import_module("config.pattern_library")
        lib = lib_module.PatternLibrary()
        lib.add_pattern(name, file_path, step_x, step_y, restricted=restricted, restricted_reason=restricted_reason)


def delete_pattern_from_library(name: str, legacy_dir: Path | None = None) -> None:
    """Delete a pattern from the pattern library."""
    engine_dir = legacy_dir or find_legacy_panel_dir()
    with _legacy_import_context(engine_dir):
        lib_module = import_module("config.pattern_library")
        lib = lib_module.PatternLibrary()
        lib.delete_pattern(name)


class LegacyPanelAdapter:
    def __init__(self, legacy_dir: Path | None = None):
        self.legacy_dir = legacy_dir or find_legacy_panel_dir()

    def run(self, request: LegacyPanelRunRequest) -> LegacyPanelRunResult:
        request.output_dxf_path.parent.mkdir(parents=True, exist_ok=True)

        with _legacy_import_context(self.legacy_dir):
            legacy_main = import_module("main")
            settings_module = import_module("config.settings")
            layout_module = import_module("layout.cad_result_layout")
            exporter_module = import_module("dxf.mixed_exporter")

            settings = _build_settings(settings_module.Settings, request)
            stdout = StringIO()
            with redirect_stdout(stdout):
                result_items = legacy_main.create_cad_result_items_from_batch(settings)
                arranged_items = layout_module.arrange_cad_result_items(result_items)
                exporter_module.MixedDXFExporter().save(arranged_items, str(request.output_dxf_path))

        if not request.output_dxf_path.exists():
            raise FileNotFoundError(f"Legacy DXF was not generated: {request.output_dxf_path}")

        resources = [_resource_payload(item) for item in result_items]
        warnings = []
        if any(resource["cut_length_mm"] == 0 for resource in resources):
            warnings.append("cut_length_mm is 0 for one or more items; panel may have no geometry.")
        if any(resource["pierce_count"] == 0 for resource in resources):
            warnings.append("pierce_count is 0 for one or more items; panel may have no perforations.")

        return LegacyPanelRunResult(
            dxf_path=request.output_dxf_path,
            calculated_resources=resources,
            warnings=warnings,
            legacy_result_raw={
                "stdout": stdout.getvalue(),
                "legacy_dir": str(self.legacy_dir),
                "request": _raw_request_payload(request),
                "items": resources,
            },
        )
