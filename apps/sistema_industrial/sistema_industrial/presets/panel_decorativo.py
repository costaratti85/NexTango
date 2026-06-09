"""Panel decorativo preset v0.1.

This does not generate final manufacturing output yet. It calculates the first
commercial/industrial quantities needed to create an ERPNext quotation and a
pending cut part.
"""

from dataclasses import dataclass
from sistema_industrial.core.models import PendingCutPart, PresetQuotation, QuotationLine, ResourceQuantity


@dataclass(frozen=True)
class PanelDecorativoInput:
    width_mm: float
    height_mm: float
    quantity: int
    material: str
    thickness_mm: float
    customer_code: str | None = None
    order_id: str = "DRAFT"


def calculate_panel_metrics(data: PanelDecorativoInput) -> dict[str, float]:
    if data.width_mm <= 0 or data.height_mm <= 0:
        raise ValueError("Panel dimensions must be positive")
    if data.quantity <= 0:
        raise ValueError("Quantity must be positive")

    area_m2_one = (data.width_mm * data.height_mm) / 1_000_000
    perimeter_m_one = 2 * (data.width_mm + data.height_mm) / 1000
    return {
        "area_m2": area_m2_one * data.quantity,
        "laser_meters": perimeter_m_one * data.quantity,
        "unit_area_m2": area_m2_one,
        "unit_perimeter_m": perimeter_m_one,
    }


def build_panel_quotation(data: PanelDecorativoInput) -> PresetQuotation:
    metrics = calculate_panel_metrics(data)
    resources = [
        ResourceQuantity("CHAPA_M2", "Chapa calculada por superficie", metrics["area_m2"], "m2"),
        ResourceQuantity("LASER_M", "Metros lineales de corte laser", metrics["laser_meters"], "m"),
    ]
    lines = [
        QuotationLine("PANEL_DECORATIVO", "Panel decorativo preset", data.quantity, "unidad", metadata={
            "width_mm": data.width_mm,
            "height_mm": data.height_mm,
            "material": data.material,
            "thickness_mm": data.thickness_mm,
        })
    ]
    return PresetQuotation("panel_decorativo", data.customer_code, lines, resources, metadata=metrics)


def build_pending_cut_part(data: PanelDecorativoInput) -> PendingCutPart:
    return PendingCutPart(
        part_id=f"{data.order_id}-PANEL-{int(data.width_mm)}x{int(data.height_mm)}",
        order_id=data.order_id,
        material=data.material,
        thickness_mm=data.thickness_mm,
        quantity=data.quantity,
        width_mm=data.width_mm,
        height_mm=data.height_mm,
        label=f"{data.order_id} panel {data.width_mm:g}x{data.height_mm:g}",
    )
