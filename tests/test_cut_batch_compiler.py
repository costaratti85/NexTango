from pathlib import Path
import json

from sistema_industrial.core.models import PendingCutPart
from sistema_industrial.cutting.cut_queue import filter_pending_by_material_thickness
from sistema_industrial.cutting.dxf_batch_compiler import CutBatchRequest, compile_cut_batch


def test_filter_pending_by_material_thickness():
    parts = [
        PendingCutPart("a", "o1", "chapa", 3.0, 1),
        PendingCutPart("b", "o2", "chapa", 6.0, 1),
        PendingCutPart("c", "o3", "aluminio", 3.0, 1),
    ]
    selected = filter_pending_by_material_thickness(parts, "chapa", 3.0)
    assert [p.part_id for p in selected] == ["a"]


def test_compile_cut_batch_creates_dxf_and_manifest(tmp_path: Path):
    part = PendingCutPart("p1", "order1", "chapa", 3.0, 2, width_mm=100, height_mm=50)
    result = compile_cut_batch(CutBatchRequest("chapa", 3.0, [part], tmp_path / "batch.dxf"))
    assert result.dxf_path.exists()
    assert result.manifest_path.exists()
    assert result.part_count == 2
    content = result.dxf_path.read_text(encoding="utf-8")
    assert "SECTION" in content
    assert "LINE" in content
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["material"] == "chapa"
    assert manifest["thickness_mm"] == 3.0
    assert manifest["part_count"] == 2
