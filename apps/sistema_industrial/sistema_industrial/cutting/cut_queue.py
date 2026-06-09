"""Cut queue operations for pending parts."""

from sistema_industrial.core.models import CutPartStatus, PendingCutPart


def filter_pending_by_material_thickness(parts: list[PendingCutPart], material: str, thickness_mm: float) -> list[PendingCutPart]:
    return [
        p for p in parts
        if p.status == CutPartStatus.PENDING
        and p.material == material
        and abs(p.thickness_mm - thickness_mm) < 0.0001
    ]


def expand_quantities(parts: list[PendingCutPart]) -> list[PendingCutPart]:
    expanded: list[PendingCutPart] = []
    for part in parts:
        for index in range(part.quantity):
            expanded.append(PendingCutPart(
                part_id=f"{part.part_id}#{index + 1}",
                order_id=part.order_id,
                material=part.material,
                thickness_mm=part.thickness_mm,
                quantity=1,
                dxf_path=part.dxf_path,
                width_mm=part.width_mm,
                height_mm=part.height_mm,
                status=part.status,
                label=part.label,
            ))
    return expanded
