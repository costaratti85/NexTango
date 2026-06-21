"""DXF batch compiler by material/thickness.

MVP responsibility: collect pending parts of one material/thickness and generate
one ordered DXF. It must NOT do nesting, kerf, leads, cut sequence or G-code.
CypCut and the existing postprocessor own those steps.
"""

from dataclasses import dataclass, asdict
from pathlib import Path
import json

from sistema_industrial.core.models import PendingCutPart
from sistema_industrial.cutting.cut_queue import expand_quantities
from sistema_industrial.cutting.dxf_writer import DxfRect, write_rectangles_dxf


_MATERIAL_TABLE_FILE = (
    Path(__file__).resolve().parents[4]
    / "Programas_hechos"
    / "Panel Decorativo"
    / "material_table.json"
)


def _abbreviated_label(material: str, thickness_mm: float) -> str:
    """Return the abbreviated material label for DXF row annotations.

    Reads familia from material_table.json:
      hierro      → N°{calibre}
      galvanizada → Galv N°{calibre}
      inox304     → Inox 304 {espesor}mm
      inox430     → Inox 430 {espesor}mm
    Falls back to '{thickness_mm}mm' when the table is unavailable or the
    material is not found.
    """
    try:
        with _MATERIAL_TABLE_FILE.open("r", encoding="utf-8") as f:
            table = json.load(f)
    except Exception:
        return f"{thickness_mm:g}mm"
    entry = next(
        (
            e for e in table
            if e["material"] == material
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
    mn = material.lower()
    if "galvaniz" in mn:
        return f"Galv N°{calibre}" if calibre and calibre != "-" else f"Galv {espesor:g}mm"
    if "304" in mn:
        return f"Inox 304 {espesor:g}mm"
    if "430" in mn:
        return f"Inox 430 {espesor:g}mm"
    return f"N°{calibre}" if calibre and calibre != "-" else f"{espesor:g}mm"


@dataclass(frozen=True)
class CutBatchRequest:
    material: str
    thickness_mm: float
    parts: list[PendingCutPart]
    output_path: Path
    margin_mm: float = 30
    max_row_width_mm: float = 3000


@dataclass(frozen=True)
class CutBatchResult:
    dxf_path: Path
    manifest_path: Path
    part_count: int
    material: str
    thickness_mm: float


def _layout_rectangles(
    parts: list[PendingCutPart],
    margin_mm: float,
    max_row_width_mm: float,
    row_label: str | None = None,
) -> list[DxfRect]:
    x = margin_mm
    y = margin_mm
    row_height = 0.0
    rectangles: list[DxfRect] = []
    for part in parts:
        width = part.width_mm or 100
        height = part.height_mm or 100
        if x + width + margin_mm > max_row_width_mm and rectangles:
            x = margin_mm
            y += row_height + margin_mm
            row_height = 0
        label = row_label if row_label is not None else (part.label or part.part_id)
        rectangles.append(DxfRect(x=x, y=y, width=width, height=height, label=label))
        x += width + margin_mm
        row_height = max(row_height, height)
    return rectangles


def compile_cut_batch(request: CutBatchRequest) -> CutBatchResult:
    if not request.parts:
        raise ValueError("Cannot compile an empty cut batch")
    expanded = expand_quantities(request.parts)
    row_label = _abbreviated_label(request.material, request.thickness_mm)
    rectangles = _layout_rectangles(expanded, request.margin_mm, request.max_row_width_mm, row_label)
    dxf_path = write_rectangles_dxf(request.output_path, rectangles)
    manifest_path = dxf_path.with_suffix(".manifest.json")
    manifest = {
        "material": request.material,
        "thickness_mm": request.thickness_mm,
        "part_count": len(expanded),
        "parts": [asdict(p) | {"dxf_path": str(p.dxf_path) if p.dxf_path else None, "status": str(p.status.value)} for p in expanded],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return CutBatchResult(dxf_path, manifest_path, len(expanded), request.material, request.thickness_mm)
