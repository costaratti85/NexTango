"""File-based pending cut queue repository for weekend MVP.

In the Frappe implementation this will become DocTypes. For now it gives us a
local, testable queue that Codex can run on Monday without ERPNext internals.
"""

from dataclasses import asdict
from pathlib import Path
import json

from sistema_industrial.core.models import CutPartStatus, PendingCutPart


def _part_to_dict(part: PendingCutPart) -> dict:
    data = asdict(part)
    data["dxf_path"] = str(part.dxf_path) if part.dxf_path else None
    data["status"] = part.status.value
    return data


def _part_from_dict(data: dict) -> PendingCutPart:
    return PendingCutPart(
        part_id=data["part_id"],
        order_id=data["order_id"],
        material=data["material"],
        thickness_mm=float(data["thickness_mm"]),
        quantity=int(data["quantity"]),
        dxf_path=Path(data["dxf_path"]) if data.get("dxf_path") else None,
        width_mm=data.get("width_mm"),
        height_mm=data.get("height_mm"),
        status=CutPartStatus(data.get("status", "pending")),
        label=data.get("label"),
    )


class FileCutQueueRepository:
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> list[PendingCutPart]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return [_part_from_dict(row) for row in payload.get("parts", [])]

    def save(self, parts: list[PendingCutPart]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"parts": [_part_to_dict(p) for p in parts]}, indent=2, ensure_ascii=False), encoding="utf-8")

    def append(self, part: PendingCutPart) -> None:
        parts = self.load()
        parts.append(part)
        self.save(parts)
