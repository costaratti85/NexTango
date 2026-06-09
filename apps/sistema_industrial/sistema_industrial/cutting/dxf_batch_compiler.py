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


def _layout_rectangles(parts: list[PendingCutPart], margin_mm: float, max_row_width_mm: float) -> list[DxfRect]:
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
        rectangles.append(DxfRect(x=x, y=y, width=width, height=height, label=part.label or part.part_id))
        x += width + margin_mm
        row_height = max(row_height, height)
    return rectangles


def compile_cut_batch(request: CutBatchRequest) -> CutBatchResult:
    if not request.parts:
        raise ValueError("Cannot compile an empty cut batch")
    expanded = expand_quantities(request.parts)
    rectangles = _layout_rectangles(expanded, request.margin_mm, request.max_row_width_mm)
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
