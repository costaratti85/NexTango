from dataclasses import dataclass


@dataclass(frozen=True)
class ClientPieceReference:
    customer_code: str
    piece_code: str
    description: str
    material: str
    thickness_mm: float | None = None
    source_kind: str = "preset_or_dxf"
    revision: str = "A"
