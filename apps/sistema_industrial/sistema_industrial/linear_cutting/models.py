from dataclasses import dataclass


@dataclass(frozen=True)
class LinearCutRequest:
    item_code: str
    material: str
    profile: str
    required_length_mm: float
    quantity: int


@dataclass(frozen=True)
class LinearStockPiece:
    stock_id: str
    material: str
    profile: str
    length_mm: float
    is_remnant: bool = False


@dataclass(frozen=True)
class LinearCutPlanLine:
    request_item_code: str
    source_stock_id: str
    cut_length_mm: float
    quantity: int
