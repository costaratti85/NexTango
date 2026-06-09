from sistema_industrial.core.models import PendingCutPart
from sistema_industrial.cutting.repository import FileCutQueueRepository


def test_file_cut_queue_repository_roundtrip(tmp_path):
    repo = FileCutQueueRepository(tmp_path / "queue.json")
    part = PendingCutPart("P1", "O1", "chapa", 3, 2, width_mm=100, height_mm=50)
    repo.append(part)
    loaded = repo.load()
    assert len(loaded) == 1
    assert loaded[0].part_id == "P1"
    assert loaded[0].thickness_mm == 3
