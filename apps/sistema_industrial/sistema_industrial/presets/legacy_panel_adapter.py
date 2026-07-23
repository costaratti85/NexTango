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
LEGACY_PATTERN_TYPES = {"tresbolillo", "dxf", "none", "cuadriculado"}


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
    """Count perforations: closed figures (holes) PLUS each Polyline (sheet
    outline / border paths) — the contour also needs its own pierce to start
    cutting it, it isn't free. Confirmado por Constantino (2026-07-23) contra
    Delay_s real de Batería 2: la convención "agujeros + contorno" da el ajuste
    más ajustado (spread 1.5% vs 4.2% sin contorno) — ver
    tools/derivar_pierce_seconds.py.

    The legacy engine emits Figure objects (not Piece) for closed perforated
    shapes. Both share the .entities interface, so we detect closed figures by
    the presence of .entities rather than by class name. Polyline objects (the
    sheet outline, and any other border path) do NOT have .entities — each one
    counts as one additional pierce (usually exactly 1, the sheet outline; if a
    pattern ever emits more than one Polyline — e.g. extra border paths — each
    one legitimately needs its own pierce too, so it's counted, not hardcoded
    as a flat +1).
    """
    holes = sum(1 for item in geometry_items if hasattr(item, "entities"))
    contornos = sum(1 for item in geometry_items
                    if not hasattr(item, "entities") and type(item).__name__ == "Polyline")
    return holes + contornos


def calculate_sheet_area_m2(width_mm: float, height_mm: float) -> float:
    """Return the sheet area in square metres."""
    return (width_mm * height_mm) / 1_000_000.0


def _factorize_grid(pierce_count: int, usable_w: float, usable_h: float) -> tuple:
    """Factoriza pierce_count en (cols, rows) cuyo ratio se aproxima a usable_w/usable_h."""
    if pierce_count <= 0:
        return 0, 0
    aspect = usable_w / usable_h if usable_h > 0 else 1.0
    target_cols = math.sqrt(pierce_count * aspect)
    lo = max(1, int(target_cols) - 5)
    hi = min(pierce_count + 1, int(target_cols) + 6)
    best, best_err = (1, pierce_count), float("inf")
    for c in range(lo, hi):
        if pierce_count % c == 0:
            r = pierce_count // c
            err = abs(c / r - aspect) if r > 0 else float("inf")
            if err < best_err:
                best_err = err
                best = (c, r)
    return best


def compute_travel_length_mm(
    pierce_count: int,
    step_x_mm: float,
    step_y_mm: float,
    usable_w: float,
    usable_h: float,
) -> float:
    """Distancia de desplazamiento rapido para cuadriculado (secuencia abajo-arriba, col por col)."""
    cols, rows = _factorize_grid(pierce_count, usable_w, usable_h)
    if cols <= 0 or rows <= 0:
        return 0.0
    intra = cols * (rows - 1) * step_y_mm
    inter = (cols - 1) * math.sqrt(step_x_mm ** 2 + ((rows - 1) * step_y_mm) ** 2) if cols > 1 else 0.0
    return intra + inter


# Tiempo de perforación (pierce), sin flycut — DERIVADO de datos reales (2026-07-23,
# tools/derivar_pierce_seconds.py), ya NO prescripto. Constantino observó en vivo que
# el cabezal empieza a bajar ANTES de llegar al punto de perforación (el pierce se
# solapa con el posicionamiento) — el valor prescripto anterior (3.0s) era una
# sobreestimación. Regresión lineal por origen (Delay_s = gamma * pierce_count, sin
# término constante — no hay motivo físico para un delay con 0 perforaciones) contra
# los 12 paneles reales de Batería 2 (Delay_s medido por CypCut, pierce_count =
# agujeros + 1 por el contorno de cada pieza — el contorno TAMBIÉN necesita su propio
# pierce, ver calculate_pierce_count() acá abajo, confirmado por Constantino
# 2026-07-23 porque es justo la convención que da el ajuste más ajustado):
# gamma = 0.7187 s/perforación, error medio 0.54%, máximo 1.42% contra los 12 paneles
# reales. Constantino confirmó 0.72 (diferencia de 0.18% contra el valor exacto de la
# regresión — se usa 0.72 tal cual lo confirmó, no el decimal completo).
# La diferencia entre espesores es insignificante frente al tiempo de posicionamiento
# del cabezal y se IGNORA a propósito — nuestra fórmula da tiempos más altos (más
# reales) que la estimación de CypCut, intencional.
# "Apto flycut" (lo elige el vendedor en la UI) baja el tiempo: el cabezal no necesita
# bajar tanto entre agujeros cuando el panel se corta en flycut — CON_FLYCUT sigue
# siendo un valor fijado por Constantino (2026-07-23), no derivado de datos propios.
PIERCE_SECONDS_SIN_FLYCUT = 0.72
PIERCE_SECONDS_CON_FLYCUT = 0.2


def calculate_consumed_resources(
    cut_length_m: float,
    pierce_count: int,
    sheet_area_m2: float,
    material_entry: dict,
    travel_length_mm: float = 0.0,
    apto_flycut: bool = False,
) -> dict:
    """Convierte outputs del motor a recursos fisicos usando la tabla de materiales.

    Si laser_a_s_per_mm > 0 usa la formula calibrada (modelo fisico):
        T = alpha*cut_mm + beta*travel_mm + gamma*pierce_count + delta
    donde alpha (laser_a_s_per_mm) y beta (laser_b_s_per_hole) salen de la calibración
    (Batería 2, ver tools/calibrar_laser.py) y NO se re-ajustan; delta (laser_d_base_s)
    también viene de esa calibración. gamma (pierce) NO se lee de material_entry — es
    universal y prescripto (PIERCE_SECONDS_*), no un coeficiente ajustado.

    De lo contrario usa la formula legacy (velocidad nominal de tabla + pierce prescripto).

    apto_flycut: True → pierce = PIERCE_SECONDS_CON_FLYCUT (1s); False (default) →
    PIERCE_SECONDS_SIN_FLYCUT (3s). Aplica en ambas ramas por igual.
    """
    densidad = float(material_entry.get("densidad_kg_m2", 0))
    consumible = float(material_entry.get("consumible_por_perforacion", 0))

    material_kg = sheet_area_m2 * densidad
    consumibles_used = pierce_count * consumible

    cut_length_mm = cut_length_m * 1000.0
    gamma = PIERCE_SECONDS_CON_FLYCUT if apto_flycut else PIERCE_SECONDS_SIN_FLYCUT

    laser_a = float(material_entry.get("laser_a_s_per_mm", 0))
    if laser_a > 0:
        laser_b = float(material_entry.get("laser_b_s_per_hole", 0))
        laser_d = float(material_entry.get("laser_d_base_s", 0))
        machine_seconds = (
            laser_a * cut_length_mm
            + laser_b * travel_length_mm
            + gamma * pierce_count
            + laser_d
        )
    else:
        velocidad = float(material_entry.get("velocidad_corte_mm_s", 0))
        cutting_seconds = (cut_length_mm / velocidad) if velocidad > 0 else 0.0
        pierce_seconds = pierce_count * gamma
        machine_seconds = cutting_seconds + pierce_seconds

    return {
        "material_kg": round(material_kg, 3),
        "machine_seconds": round(max(machine_seconds, 0.0), 1),
        "pierce_count": pierce_count,
        "consumibles_used": round(consumibles_used, 4),
    }


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
    hole_shape: str = "circle"
    hole_size_mm: float = 20.0
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

    if request.pattern_type == "cuadriculado":
        if request.step_x_mm is None or request.step_y_mm is None:
            raise ValueError("step_x_mm and step_y_mm are required for cuadriculado patterns")
        settings.hole_shape = request.hole_shape
        settings.hole_size = request.hole_size_mm
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


# CypCut levanta hasta 14 canales/capas desde un DXF (límite real confirmado
# empíricamente con test_20_capas_xdata.dxf) → canales 1..14, tope 14 áreas por lado.
NUM_CAPAS_CYPCUT = 14

# Application ID del XDATA que CypCut usa para asignar el canal de flycut de cada entidad.
CYPCUT_APPID = "FS_CYPCUT"

# Lado máximo deseado de cada zona de flycut (mm). Constantino: áreas < 200.
ZONE_TARGET_MM = 200.0


def calcular_zonas(w_mm: float, h_mm: float, target: float = ZONE_TARGET_MM):
    """Divide el área del panel en n_cols × n_rows zonas de flycut.

    Por cada lado: la MENOR cantidad de áreas que deje cada una < target (200mm),
    con TOPE de NUM_CAPAS_CYPCUT (14) áreas por lado:
        N_lado = min(14, ceil(lado / target))
    Si para bajar de 200 harían falta más de 14 áreas, se queda en 14 y esas áreas
    quedan > 200 (límite de CypCut). Cada dimensión se calcula independiente.

    Las áreas de un lado son de igual tamaño (lado/N); la última fila/columna
    absorbe el sobrante de redondeo vía el clamp de zona_de_agujero.

    Cada zona se asigna a una capa de CypCut con esquema de CUADRADO LATINO
    (ver zona_a_capa): con ambos lados ≤ 9 y módulo 9, dos zonas de la misma
    fila o columna nunca comparten capa.

    Devuelve (n_cols, n_rows, zone_w, zone_h, total_zonas).
    """
    n_cols = min(NUM_CAPAS_CYPCUT, math.ceil(w_mm / target))
    n_rows = min(NUM_CAPAS_CYPCUT, math.ceil(h_mm / target))
    zone_w = w_mm / n_cols
    zone_h = h_mm / n_rows
    return n_cols, n_rows, zone_w, zone_h, n_cols * n_rows


def zona_de_agujero(
    x: float, y: float,
    n_cols: int, n_rows: int,
    zone_w: float, zone_h: float,
) -> int:
    """Número de zona (0-indexed) para un agujero en (x, y) relativo al origen del panel."""
    col_zona = min(int(x / zone_w), n_cols - 1)
    row_zona = min(int(y / zone_h), n_rows - 1)
    return row_zona * n_cols + col_zona


def _xdata_fs_cypcut(channel: int) -> list:
    """XDATA FS_CYPCUT para una entidad de flycut, con su canal.

    CypCut asigna el canal de proceso por este XDATA (no por el nombre de capa ni
    el color). Formato validado byte-idéntico contra un export nativo de CypCut
    (ver test_14_capas_xdata.dxf / Prueba definitiva.dxf). Todos los parámetros de
    corte van en cero salvo IsFill=1; sólo `Channel` varía por entidad.
    """
    return [
        (1000, "Channel"), (1070, channel),
        (1000, "LeadIn"), (1002, "{"),
        (1070, 0), (1040, 0.0), (1040, 0.0), (1040, 0.0), (1040, 0.0), (1070, 0), (1040, 0.0), (1070, 0),
        (1002, "}"),
        (1000, "LeadOut"), (1002, "{"),
        (1070, 0), (1040, 0.0), (1040, 0.0), (1040, 0.0), (1070, 0),
        (1002, "}"),
        (1000, "IsFill"), (1070, 1),
        (1000, "PathStart"), (1040, 0.0),
        (1000, "ToolCompensation"), (1002, "{"),
        (1070, 0), (1040, 0.0), (1070, 0),
        (1002, "}"),
    ]


def asegurar_capas_flycut(doc, num_capas: int = NUM_CAPAS_CYPCUT) -> None:
    """Declara en la tabla LAYER del DXF las capas de flycut (0..num_capas-1) + CONTORNO.

    Sin esto, ezdxf asigna el atributo `layer` a cada entidad pero NO crea la
    entrada en la tabla de capas → CypCut puede no reconocerlas como capas de
    flycut separadas. Cada capa recibe un color ACI distinto (1..num_capas) para
    que se distingan visualmente; CONTORNO va en un color aparte.

    Capas de flycut nombradas "1".."num_capas" (CypCut arranca en 1; la "0" no se
    usa para flycut — ver zona_a_capa y el DXF de referencia cypcut_capas.dxf).
    Registra además el APPID FS_CYPCUT, requerido para escribir el XDATA que CypCut
    usa para asignar el canal de cada agujero (ver _xdata_fs_cypcut).

    Idempotente: si la capa/appid ya existe, la deja como está.
    """
    if CYPCUT_APPID not in doc.appids:
        doc.appids.add(CYPCUT_APPID)
    for i in range(1, num_capas + 1):
        name = str(i)
        if name not in doc.layers:
            doc.layers.add(name, color=(i % 9) + 1)  # ACI, color distinto por capa
    if "CONTORNO" not in doc.layers:
        doc.layers.add("CONTORNO", color=7)


def zona_a_capa(col_zona: int, row_zona: int, num_capas: int = NUM_CAPAS_CYPCUT) -> int:
    """Capa de CypCut para la zona (col, fila) según cuadrado latino.

    capa = (col + fila) % num_capas + 1   →  capas 1..num_capas.

    CypCut nombra las capas de flycut arrancando en "1" (la capa "0" es la default
    de CAD y NO se usa para flycut — confirmado con el DXF de referencia
    cypcut_capas.dxf). Por eso el "+1".

    Propiedad: en una misma fila (row fijo) la capa recorre valores consecutivos
    al variar col, y lo mismo por columna → como n_cols y n_rows ≤ num_capas (14)
    por construcción (calcular_zonas topea en 14 áreas por lado), ninguna fila ni
    columna repite capa (cuadrado latino). Además zonas adyacentes (Δcol=1 o
    Δfila=1) siempre caen en capas distintas, por lo que el flycut nunca corta
    dos áreas contiguas de forma consecutiva y el calor no desplaza la chapa
    entre pasadas.
    """
    return (col_zona + row_zona) % num_capas + 1


def capa_de_punto(x_rel: float, y_rel: float, n_cols: int, n_rows: int,
                  zone_w: float, zone_h: float) -> int:
    """Capa de flycut (cuadrado latino, 1..NUM_CAPAS_CYPCUT) para un punto del panel.

    GENÉRICO — sirve para cualquier patrón (cuadriculado cuadrado, tresbolillo
    hexagonal, etc.). Combina zona_de_agujero + zona_a_capa. El punto es relativo
    al origen del panel; las zonas se obtienen con calcular_zonas(sheet_w, sheet_h).
    """
    zona = zona_de_agujero(x_rel, y_rel, n_cols, n_rows, zone_w, zone_h)
    return zona_a_capa(zona % n_cols, zona // n_cols)


def escribir_figura_flycut(msp, puntos, capa: int) -> None:
    """Dibuja una figura cerrada (LWPOLYLINE) en su capa de flycut + XDATA FS_CYPCUT.

    GENÉRICO — cualquier generador de patrón usa esto para que la figura quede en
    la capa correcta y con el Channel que CypCut necesita. `puntos` = lista de
    (x, y) de los vértices (sin repetir el primero; close=True lo cierra).
    """
    fig = msp.add_lwpolyline(puntos, close=True, dxfattribs={"layer": str(capa)})
    fig.set_xdata(CYPCUT_APPID, _xdata_fs_cypcut(capa))


def _write_cuadriculado_square_to_doc(
    doc,
    msp,
    hole_size_mm: float,
    step_x_mm: float,
    step_y_mm: float,
    sheet_width_mm: float,
    sheet_height_mm: float,
    margin_mm: float,
    offset_x: float = 0.0,
    offset_y: float = 0.0,
    zone_size_mm: float = ZONE_TARGET_MM,
) -> dict:
    """Write cuadriculado square entities into an *existing* ezdxf doc/msp.

    Cada agujero se asigna a la capa de CypCut de su zona con esquema de CUADRADO
    LATINO: ``capa = (col_zona + fila_zona) % 9`` (ver zona_a_capa). Así el
    flycut nunca corta dos áreas contiguas de forma consecutiva → evita el
    desfase por calor. Todo el panel va en UN solo archivo (9 capas alcanzan
    para cualquier tamaño; ya no se divide en bloques).

    Returns {pierce_count, cut_length_mm, travel_length_mm, zone_cols, zone_rows,
             total_zones, n_files}.
    """
    half = hole_size_mm / 2.0
    usable_w = sheet_width_mm - 2.0 * margin_mm
    usable_h = sheet_height_mm - 2.0 * margin_mm

    cols = int(usable_w / step_x_mm) if step_x_mm > 0 else 0
    rows = int(usable_h / step_y_mm) if step_y_mm > 0 else 0

    while cols > 0 and (cols - 1) * step_x_mm + hole_size_mm > usable_w:
        cols -= 1
    while rows > 0 and (rows - 1) * step_y_mm + hole_size_mm > usable_h:
        rows -= 1

    # Declarar las capas de flycut en la tabla LAYER (CypCut las necesita ahí).
    asegurar_capas_flycut(doc)

    ox, oy = offset_x, offset_y
    msp.add_lwpolyline(
        [(ox, oy), (ox + sheet_width_mm, oy),
         (ox + sheet_width_mm, oy + sheet_height_mm), (ox, oy + sheet_height_mm)],
        close=True,
        dxfattribs={"layer": "CONTORNO"},
    )

    n_cols, n_rows, zone_w, zone_h, total_zones = calcular_zonas(
        sheet_width_mm, sheet_height_mm, zone_size_mm
    )
    # Cuadrado latino: todo en un solo archivo, 14 capas alcanzan para cualquier tamaño.
    n_files = 1

    if cols == 0 or rows == 0:
        return {
            "pierce_count": 0, "cut_length_mm": 0.0,
            "zone_cols": n_cols, "zone_rows": n_rows,
            "total_zones": total_zones, "n_files": n_files,
        }

    visual_w = (cols - 1) * step_x_mm + hole_size_mm
    visual_h = (rows - 1) * step_y_mm + hole_size_mm
    start_x = ox + margin_mm + (usable_w - visual_w) / 2.0 + half
    start_y = oy + margin_mm + (usable_h - visual_h) / 2.0 + half

    for r in range(rows):
        for c in range(cols):
            cx = start_x + c * step_x_mm
            cy = start_y + r * step_y_mm
            # Position relative to sheet origin for zone lookup
            rx, ry = cx - ox, cy - oy
            capa = capa_de_punto(rx, ry, n_cols, n_rows, zone_w, zone_h)
            escribir_figura_flycut(msp, [
                (cx - half, cy - half), (cx + half, cy - half),
                (cx + half, cy + half), (cx - half, cy + half),
            ], capa)

    pierce_count = cols * rows
    contorno_mm = 2.0 * (sheet_width_mm + sheet_height_mm)
    usable_w = sheet_width_mm - 2.0 * margin_mm
    usable_h = sheet_height_mm - 2.0 * margin_mm
    travel_mm = compute_travel_length_mm(pierce_count, step_x_mm, step_y_mm, usable_w, usable_h)
    return {
        "pierce_count": pierce_count,
        "cut_length_mm": pierce_count * 4.0 * hole_size_mm + contorno_mm,
        "travel_length_mm": travel_mm,
        "zone_cols": n_cols,
        "zone_rows": n_rows,
        "total_zones": total_zones,
        "n_files": n_files,
    }


def _generate_cuadriculado_square_dxf(
    hole_size_mm: float,
    step_x_mm: float,
    step_y_mm: float,
    sheet_width_mm: float,
    sheet_height_mm: float,
    margin_mm: float,
    output_path,
    zone_size_mm: float = ZONE_TARGET_MM,
) -> dict:
    """Generate a single DXF for a cuadriculado square pattern.

    El panel entero va en UN solo bloque. Las zonas de flycut se reparten en las
    14 capas de CypCut con esquema de cuadrado latino (ver zona_a_capa), así el
    láser nunca corta áreas contiguas de forma consecutiva y el calor no
    desplaza la chapa entre pasadas. Ya no se divide en bloques a unir a mano.

    Returns dict: {pierce_count, cut_length_mm, travel_length_mm, zone_cols,
                   zone_rows, total_zones, n_files}.
    """
    import ezdxf as _ezdxf

    doc = _ezdxf.new("R2010")
    msp = doc.modelspace()
    result = _write_cuadriculado_square_to_doc(
        doc, msp,
        hole_size_mm=hole_size_mm,
        step_x_mm=step_x_mm,
        step_y_mm=step_y_mm,
        sheet_width_mm=sheet_width_mm,
        sheet_height_mm=sheet_height_mm,
        margin_mm=margin_mm,
        zone_size_mm=zone_size_mm,
    )
    doc.saveas(str(output_path))
    return result


# Rotación de cada hexágono sobre su propio centro (decisión Constantino,
# 2026-07-14): 0° da flat-top (2 lados horizontales); 30° da pointy-top (un
# vértice arriba). Constantino confirmó que con 30° se pierde la pasada
# horizontal de flycut (queda vertical + 2 inclinadas) y no hay problema.
HEX_ROTATION_DEG = 30.0


def _hexagon_vertices(cx: float, cy: float, across_flats: float,
                      rotation_deg: float = HEX_ROTATION_DEG) -> list:
    """Vértices de un hexágono regular centrado en (cx, cy).

    across_flats = distancia entre lados opuestos del hexágono (medida
    intrínseca, no depende de la rotación global) — se toma = diámetro del
    agujero. Radio (centro→vértice) = across_flats / sqrt(3), constante para
    cualquier rotación. rotation_deg=0 → flat-top (2 lados horizontales);
    rotation_deg=30 (default) → pointy-top (vértice arriba). Cada hexágono se
    gira sobre su propio centro, así al tilear toda la grilla (tresbolillo,
    columnas par/impar) queda con la misma orientación.
    """
    R = across_flats / math.sqrt(3.0)
    return [
        (cx + R * math.cos(math.radians(k * 60 + rotation_deg)),
         cy + R * math.sin(math.radians(k * 60 + rotation_deg)))
        for k in range(6)
    ]


def _write_tresbolillo_hex_to_doc(
    doc,
    msp,
    hole_diameter_mm: float,
    hole_distance_mm: float,
    sheet_width_mm: float,
    sheet_height_mm: float,
    margin_mm: float,
    offset_x: float = 0.0,
    offset_y: float = 0.0,
    zone_size_mm: float = ZONE_TARGET_MM,
) -> dict:
    """Escribe un panel de tresbolillo hexagonal en un doc/msp existente.

    Hexágonos pointy-top (rotados 30° sobre su propio centro, HEX_ROTATION_DEG —
    decisión Constantino) en grilla tresbolillo (filas separadas por dy =
    distancia·√3/2; filas impares desplazadas medio paso). Cada hexágono va en su
    capa de flycut (Channel por XDATA FS_CYPCUT), con la división por áreas
    genérica → el flycut de 3 pasadas (vertical / inclinada der / inclinada izq)
    nunca corta áreas contiguas de forma consecutiva (evita el desfase por calor).
    `offset_x/y` posiciona el panel (para combinarlo con otros en el mismo DXF).

    Returns: {pierce_count, cut_length_mm, travel_length_mm, zone_cols, zone_rows,
              total_zones, n_files}.
    """
    asegurar_capas_flycut(doc)
    ox, oy = offset_x, offset_y

    msp.add_lwpolyline(
        [(ox, oy), (ox + sheet_width_mm, oy),
         (ox + sheet_width_mm, oy + sheet_height_mm), (ox, oy + sheet_height_mm)],
        close=True, dxfattribs={"layer": "CONTORNO"},
    )

    n_cols, n_rows, zone_w, zone_h, total_zones = calcular_zonas(
        sheet_width_mm, sheet_height_mm, zone_size_mm
    )
    usable_w = sheet_width_mm - 2.0 * margin_mm
    usable_h = sheet_height_mm - 2.0 * margin_mm
    R = hole_diameter_mm / math.sqrt(3.0)          # radio centro→vértice
    half_w = R                                     # medio ancho del hexágono (horizontal)
    half_h = hole_diameter_mm / 2.0                # medio alto (across_flats/2)
    d = hole_distance_mm
    dy = d * math.sqrt(3.0) / 2.0                  # separación vertical de filas

    if d <= 0 or usable_w <= 0 or usable_h <= 0 or dy <= 0:
        return {"pierce_count": 0, "cut_length_mm": 0.0, "travel_length_mm": 0.0,
                "zone_cols": n_cols, "zone_rows": n_rows, "total_zones": total_zones, "n_files": 1}

    pierce_count = 0
    x0 = ox + margin_mm
    y0 = oy + margin_mm
    n_filas = int(usable_h // dy) + 1
    for r in range(n_filas):
        cy = y0 + half_h + r * dy
        if cy + half_h > oy + margin_mm + usable_h:
            break
        row_offset = (d / 2.0) if (r % 2) else 0.0
        c = 0
        while True:
            cx = x0 + half_w + row_offset + c * d
            c += 1
            if cx + half_w > ox + margin_mm + usable_w:
                break
            # capa por posición RELATIVA al origen del panel
            capa = capa_de_punto(cx - ox, cy - oy, n_cols, n_rows, zone_w, zone_h)
            escribir_figura_flycut(msp, _hexagon_vertices(cx, cy, hole_diameter_mm), capa)
            pierce_count += 1

    lado = R                                        # lado del hexágono regular = R
    contorno_mm = 2.0 * (sheet_width_mm + sheet_height_mm)
    cut_length_mm = pierce_count * 6.0 * lado + contorno_mm
    travel_mm = compute_travel_length_mm(pierce_count, d, dy, usable_w, usable_h)

    return {
        "pierce_count": pierce_count,
        "cut_length_mm": cut_length_mm,
        "travel_length_mm": travel_mm,
        "zone_cols": n_cols,
        "zone_rows": n_rows,
        "total_zones": total_zones,
        "n_files": 1,
    }


def _generate_tresbolillo_hex_dxf(
    hole_diameter_mm: float,
    hole_distance_mm: float,
    sheet_width_mm: float,
    sheet_height_mm: float,
    margin_mm: float,
    output_path,
    zone_size_mm: float = ZONE_TARGET_MM,
) -> dict:
    """DXF standalone de tresbolillo hexagonal (un solo panel). Ver _write_tresbolillo_hex_to_doc."""
    import ezdxf as _ezdxf

    doc = _ezdxf.new("R2010")
    msp = doc.modelspace()
    result = _write_tresbolillo_hex_to_doc(
        doc, msp,
        hole_diameter_mm=hole_diameter_mm,
        hole_distance_mm=hole_distance_mm,
        sheet_width_mm=sheet_width_mm,
        sheet_height_mm=sheet_height_mm,
        margin_mm=margin_mm,
        zone_size_mm=zone_size_mm,
    )
    doc.saveas(str(output_path))
    return result


class LegacyPanelAdapter:
    def __init__(self, legacy_dir: Path | None = None):
        self.legacy_dir = legacy_dir or find_legacy_panel_dir()

    def run(self, request: LegacyPanelRunRequest) -> LegacyPanelRunResult:
        request.output_dxf_path.parent.mkdir(parents=True, exist_ok=True)

        # Cuadriculado + square → dedicated generator: LWPOLYLINE per hole + DXF GROUP per zone
        if request.pattern_type == "cuadriculado" and request.hole_shape == "square":
            return self._run_cuadriculado_square(request)

        # Tresbolillo + hexágono → generador directo con división por áreas + XDATA flycut
        if request.pattern_type == "tresbolillo" and request.hole_shape == "hexagon":
            return self._run_tresbolillo_hex(request)

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
        if (request.pattern_type == "cuadriculado"
                and request.step_x_mm is not None and request.step_y_mm is not None):
            for res in resources:
                uw = res["occupied_width_mm"] - 2.0 * request.margin_mm
                uh = res["occupied_height_mm"] - 2.0 * request.margin_mm
                res["travel_length_mm"] = compute_travel_length_mm(
                    res["pierce_count"], request.step_x_mm, request.step_y_mm, uw, uh
                )
        else:
            for res in resources:
                res["travel_length_mm"] = 0.0
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

    def _run_cuadriculado_square(self, request: LegacyPanelRunRequest) -> LegacyPanelRunResult:
        """Direct DXF generation for cuadriculado+square: LWPOLYLINE + flycut zone groups."""
        sheet_sizes = request.sheet_sizes or [(request.width_mm, request.height_mm, request.quantity)]
        sheet_width, sheet_height, quantity = sheet_sizes[0]

        geo = _generate_cuadriculado_square_dxf(
            hole_size_mm=request.hole_size_mm,
            step_x_mm=request.step_x_mm,
            step_y_mm=request.step_y_mm,
            sheet_width_mm=sheet_width,
            sheet_height_mm=sheet_height,
            margin_mm=request.margin_mm,
            output_path=request.output_dxf_path,
        )

        if not request.output_dxf_path.exists():
            raise FileNotFoundError(f"DXF was not generated: {request.output_dxf_path}")

        sheet_area_m2 = calculate_sheet_area_m2(sheet_width, sheet_height)
        resource = {
            "name": f"{request.preset_name} {sheet_width}x{sheet_height}",
            "material": request.material,
            "thickness_mm": request.thickness_mm,
            "quantity": quantity,
            "occupied_width_mm": sheet_width,
            "occupied_height_mm": sheet_height,
            "geometry_item_count": geo["pierce_count"] + 1,  # +1 for outline
            "cut_length_mm": geo["cut_length_mm"],
            "cut_length_m": geo["cut_length_mm"] / 1000.0,
            "pierce_count": geo["pierce_count"],
            "travel_length_mm": geo.get("travel_length_mm", 0.0),
            "sheet_area_m2": sheet_area_m2,
            "bend_count": 0,
        }

        zone_info = f"{geo['zone_cols']} col × {geo['zone_rows']} fila"
        capas_usadas = min(NUM_CAPAS_CYPCUT, geo["zone_cols"] + geo["zone_rows"] - 1)
        w_msg = (
            f"Flycut cuadrado latino: {geo['pierce_count']} cuadrados en {zone_info} "
            f"áreas (≤200mm; máx 14 por lado), repartidas en {capas_usadas} capas de "
            f"CypCut. Seleccionar todo y aplicar flycut — no se cortan áreas "
            f"contiguas de forma consecutiva (evita el desfase por calor)."
        )
        return LegacyPanelRunResult(
            dxf_path=request.output_dxf_path,
            calculated_resources=[resource],
            warnings=[w_msg] if geo["pierce_count"] > 0 else [],
            legacy_result_raw={
                "generator": "cuadriculado_square_direct",
                "zone_cols": geo["zone_cols"],
                "zone_rows": geo["zone_rows"],
                "request": _raw_request_payload(request),
                "items": [resource],
            },
        )

    def _run_tresbolillo_hex(self, request: LegacyPanelRunRequest) -> LegacyPanelRunResult:
        """Direct DXF generation for tresbolillo+hexágono: hexágonos + flycut por áreas."""
        sheet_sizes = request.sheet_sizes or [(request.width_mm, request.height_mm, request.quantity)]
        sheet_width, sheet_height, quantity = sheet_sizes[0]

        geo = _generate_tresbolillo_hex_dxf(
            hole_diameter_mm=request.hole_diameter_mm,
            hole_distance_mm=request.hole_distance_mm,
            sheet_width_mm=sheet_width,
            sheet_height_mm=sheet_height,
            margin_mm=request.margin_mm,
            output_path=request.output_dxf_path,
        )

        if not request.output_dxf_path.exists():
            raise FileNotFoundError(f"DXF was not generated: {request.output_dxf_path}")

        sheet_area_m2 = calculate_sheet_area_m2(sheet_width, sheet_height)
        resource = {
            "name": f"{request.preset_name} {sheet_width}x{sheet_height}",
            "material": request.material,
            "thickness_mm": request.thickness_mm,
            "quantity": quantity,
            "occupied_width_mm": sheet_width,
            "occupied_height_mm": sheet_height,
            "geometry_item_count": geo["pierce_count"] + 1,  # +1 for outline
            "cut_length_mm": geo["cut_length_mm"],
            "cut_length_m": geo["cut_length_mm"] / 1000.0,
            "pierce_count": geo["pierce_count"],
            "travel_length_mm": geo.get("travel_length_mm", 0.0),
            "sheet_area_m2": sheet_area_m2,
            "bend_count": 0,
        }

        zone_info = f"{geo['zone_cols']} col × {geo['zone_rows']} fila"
        capas_usadas = min(NUM_CAPAS_CYPCUT, geo["zone_cols"] + geo["zone_rows"] - 1)
        w_msg = (
            f"Flycut cuadrado latino: {geo['pierce_count']} hexágonos en {zone_info} "
            f"áreas (≤200mm; máx 14 por lado), repartidas en {capas_usadas} capas de "
            f"CypCut. Hexágonos rotados 30° (pointy-top); las 3 pasadas (vertical / "
            f"inclinada der / inclinada izq) no cortan áreas contiguas de forma "
            f"consecutiva (evita el desfase por calor)."
        )
        return LegacyPanelRunResult(
            dxf_path=request.output_dxf_path,
            calculated_resources=[resource],
            warnings=[w_msg] if geo["pierce_count"] > 0 else [],
            legacy_result_raw={
                "generator": "tresbolillo_hex_direct",
                "zone_cols": geo["zone_cols"],
                "zone_rows": geo["zone_rows"],
                "request": _raw_request_payload(request),
                "items": [resource],
            },
        )
