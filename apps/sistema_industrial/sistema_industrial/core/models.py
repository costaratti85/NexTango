"""Neutral domain models for SistemaIndustrial.

These models are deliberately independent from Frappe, Tango and Excel.
Adapters may convert them into ERPNext documents, Tango payloads or files.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class SourceOfTruth(str, Enum):
    TANGO = "tango"
    ERPNEXT = "erpnext"
    EXCEL = "excel"
    SISTEMA_INDUSTRIAL = "sistema_industrial"


class CutPartStatus(str, Enum):
    PENDING = "pending"
    BATCHED = "batched"
    SENT_TO_CYPCUT = "sent_to_cypcut"
    CUT = "cut"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class Money:
    amount: float
    currency: str = "ARS"


@dataclass(frozen=True)
class ResourceQuantity:
    code: str
    description: str
    quantity: float
    uom: str


@dataclass(frozen=True)
class QuotationLine:
    item_code: str
    description: str
    quantity: float
    uom: str
    unit_price: Money | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PresetQuotation:
    preset_name: str
    customer_code: str | None
    lines: list[QuotationLine]
    resources: list[ResourceQuantity]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PendingCutPart:
    part_id: str
    order_id: str
    material: str
    thickness_mm: float
    quantity: int
    dxf_path: Path | None = None
    width_mm: float | None = None
    height_mm: float | None = None
    status: CutPartStatus = CutPartStatus.PENDING
    label: str | None = None


@dataclass(frozen=True)
class IntegrationEvent:
    event_type: str
    source: SourceOfTruth
    payload: dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)
