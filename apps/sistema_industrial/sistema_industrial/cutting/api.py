"""Cut batch application API."""

from pathlib import Path

from sistema_industrial.cutting.cut_queue import filter_pending_by_material_thickness
from sistema_industrial.cutting.dxf_batch_compiler import CutBatchRequest, CutBatchResult, compile_cut_batch
from sistema_industrial.cutting.repository import FileCutQueueRepository


def compile_batch_from_queue(queue_path: Path, material: str, thickness_mm: float, output_path: Path) -> CutBatchResult:
    repo = FileCutQueueRepository(queue_path)
    selected = filter_pending_by_material_thickness(repo.load(), material, thickness_mm)
    return compile_cut_batch(CutBatchRequest(material=material, thickness_mm=thickness_mm, parts=selected, output_path=output_path))
