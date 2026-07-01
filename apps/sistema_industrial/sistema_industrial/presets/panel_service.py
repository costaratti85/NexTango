"""Application service for decorative panels backed by the legacy engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import json

from sistema_industrial.core.models import PendingCutPart
from sistema_industrial.presets.legacy_panel_adapter import LegacyPanelAdapter, LegacyPanelRunRequest
from sistema_industrial.pricing_sync.price_cache import PriceCache


@dataclass(frozen=True)
class LegacyPanelServiceInput:
    panel_mode: str = "tresbolillo"
    preset_code: str = "PANEL_DECORATIVO_LEGACY"
    preset_name: str = "Tresbolillo circular"
    material: str = "chapa"
    thickness_mm: float = 3.0
    width_mm: float = 300.0
    height_mm: float = 200.0
    quantity: int = 1
    customer_code: str | None = "CLIENTE-DEMO"
    order_id: str = "PED-LEGACY-DEMO-001"
    job_name: str = "Panel decorativo legacy"
    observations: str = ""
    pattern_type: str = "tresbolillo"
    cut_partial_figures: bool = True
    margin_mm: float = 20.0
    hole_diameter_mm: float = 20.0
    hole_distance_mm: float = 60.0
    hole_shape: str = "circle"
    hole_size_mm: float = 20.0
    offset_x_mm: float | None = None
    offset_y_mm: float | None = None
    pattern_dxf_path: Path | None = None
    step_x_mm: float | None = None
    step_y_mm: float | None = None
    rows: int | None = None
    columns: int | None = None
    # Optional list of (width_mm, height_mm, quantity) for multi-piece batches
    sheet_sizes: list | None = None


def legacy_pattern_type_for_panel_mode(panel_mode: str) -> str:
    if panel_mode == "tresbolillo":
        return "tresbolillo"
    if panel_mode == "dxf_pattern_grid":
        return "dxf"
    if panel_mode == "none":
        return "none"
    if panel_mode == "cuadriculado":
        return "cuadriculado"
    raise ValueError(f"Unsupported panel_mode: {panel_mode}")


def normalize_panel_input(data: LegacyPanelServiceInput) -> LegacyPanelServiceInput:
    pattern_type = legacy_pattern_type_for_panel_mode(data.panel_mode)
    if data.panel_mode == "dxf_pattern_grid":
        if data.pattern_dxf_path is None:
            raise ValueError("pattern_dxf_path is required for dxf_pattern_grid")
        if data.step_x_mm is None or data.step_y_mm is None:
            raise ValueError("step_x_mm and step_y_mm are required for dxf_pattern_grid")
    # For cuadriculado, map offset_x/y → step_x/y
    step_x_mm = data.step_x_mm
    step_y_mm = data.step_y_mm
    if data.panel_mode == "cuadriculado":
        if data.offset_x_mm is None or data.offset_y_mm is None:
            raise ValueError("offset_x_mm and offset_y_mm are required for cuadriculado")
        step_x_mm = data.offset_x_mm
        step_y_mm = data.offset_y_mm
    return LegacyPanelServiceInput(
        panel_mode=data.panel_mode,
        preset_code=data.preset_code,
        preset_name=data.preset_name,
        material=data.material,
        thickness_mm=data.thickness_mm,
        width_mm=data.width_mm,
        height_mm=data.height_mm,
        quantity=data.quantity,
        customer_code=data.customer_code,
        order_id=data.order_id,
        job_name=data.job_name,
        observations=data.observations,
        pattern_type=pattern_type,
        cut_partial_figures=data.cut_partial_figures,
        margin_mm=data.margin_mm,
        hole_diameter_mm=data.hole_diameter_mm,
        hole_distance_mm=data.hole_distance_mm,
        hole_shape=data.hole_shape,
        hole_size_mm=data.hole_size_mm,
        offset_x_mm=data.offset_x_mm,
        offset_y_mm=data.offset_y_mm,
        pattern_dxf_path=data.pattern_dxf_path,
        step_x_mm=step_x_mm,
        step_y_mm=step_y_mm,
        rows=data.rows,
        columns=data.columns,
        sheet_sizes=data.sheet_sizes,
    )


@dataclass(frozen=True)
class LegacyPanelServiceResult:
    panel_mode: str
    preset_code: str
    preset_name: str
    material: str
    thickness_mm: float
    width_mm: float
    height_mm: float
    quantity: int
    calculated_resources: list[dict]
    dxf_path: Path
    warnings: list[str]
    legacy_result_raw: dict
    cut_piece_payload: dict
    quotation_payload: dict
    # Aggregate resource totals computed from geometry
    cut_length_m: float = 0.0
    pierce_count: int = 0
    sheet_area_m2: float = 0.0

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["dxf_path"] = str(self.dxf_path)
        return payload


def _build_cut_piece_payload(data: LegacyPanelServiceInput, dxf_path: Path) -> dict:
    part = PendingCutPart(
        part_id=f"{data.order_id}-LEGACY-PANEL-{int(data.width_mm)}x{int(data.height_mm)}",
        order_id=data.order_id,
        material=data.material,
        thickness_mm=data.thickness_mm,
        quantity=data.quantity,
        dxf_path=dxf_path,
        width_mm=data.width_mm,
        height_mm=data.height_mm,
        label=f"{data.order_id} legacy panel {data.width_mm:g}x{data.height_mm:g}",
    )
    payload = asdict(part)
    payload["dxf_path"] = str(dxf_path)
    payload["status"] = part.status.value
    return payload


def _build_quotation_payload(
    data: LegacyPanelServiceInput,
    calculated_resources: list[dict],
    price_cache: PriceCache | None,
) -> dict:
    price = price_cache.get("PANEL_DECORATIVO") if price_cache else None
    return {
        "doctype": "Quotation",
        "party_name": data.customer_code,
        "customer_reference": data.customer_code,
        "title": data.job_name,
        "si_preset_name": data.preset_name,
        "si_preset_code": data.preset_code,
        "si_resources": calculated_resources,
        "items": [
            {
                "item_code": "PANEL_DECORATIVO",
                "description": f"Panel decorativo legacy - {data.preset_name}",
                "qty": data.quantity,
                "uom": "unidad",
                "rate": price.amount if price else 0,
                "currency": price.currency if price else "ARS",
                "si_metadata": {
                    "legacy_engine": True,
                    "preset_code": data.preset_code,
                    "panel_mode": data.panel_mode,
                    "width_mm": data.width_mm,
                    "height_mm": data.height_mm,
                    "material": data.material,
                    "thickness_mm": data.thickness_mm,
                    "observations": data.observations,
                    "pattern_dxf_path": str(data.pattern_dxf_path) if data.pattern_dxf_path else None,
                    "offset_x_mm": data.step_x_mm,
                    "offset_y_mm": data.step_y_mm,
                    "step_x_mm": data.step_x_mm,
                    "step_y_mm": data.step_y_mm,
                    "rows": data.rows,
                    "columns": data.columns,
                },
            }
        ],
        "si_metadata": {
            "source": "legacy_panel_engine",
            "panel_mode": data.panel_mode,
            "pattern_type": data.pattern_type,
            "cut_partial_figures": data.cut_partial_figures,
            "margin_mm": data.margin_mm,
            "job_name": data.job_name,
            "observations": data.observations,
        },
    }


class LegacyPanelService:
    def __init__(self, adapter: LegacyPanelAdapter | None = None, price_cache: PriceCache | None = None):
        self.adapter = adapter or LegacyPanelAdapter()
        self.price_cache = price_cache

    def run(self, data: LegacyPanelServiceInput, output_dir: Path) -> LegacyPanelServiceResult:
        data = normalize_panel_input(data)
        output_dir.mkdir(parents=True, exist_ok=True)
        dxf_path = output_dir / f"{data.order_id}_legacy_panel.dxf"
        legacy_result = self.adapter.run(
            LegacyPanelRunRequest(
                preset_code=data.preset_code,
                preset_name=data.preset_name,
                material=data.material,
                thickness_mm=data.thickness_mm,
                width_mm=data.width_mm,
                height_mm=data.height_mm,
                quantity=data.quantity,
                output_dxf_path=dxf_path,
                pattern_type=data.pattern_type,
                cut_partial_figures=data.cut_partial_figures,
                margin_mm=data.margin_mm,
                hole_diameter_mm=data.hole_diameter_mm,
                hole_distance_mm=data.hole_distance_mm,
                hole_shape=data.hole_shape,
                hole_size_mm=data.hole_size_mm,
                pattern_dxf_path=data.pattern_dxf_path,
                step_x_mm=data.step_x_mm,
                step_y_mm=data.step_y_mm,
                rows=data.rows,
                columns=data.columns,
                sheet_sizes=data.sheet_sizes,
            )
        )
        cut_piece_payload = _build_cut_piece_payload(data, legacy_result.dxf_path)
        quotation_payload = _build_quotation_payload(data, legacy_result.calculated_resources, self.price_cache)
        # Aggregate resource totals across all result items (quantity-weighted)
        total_cut_length_m = sum(
            r.get("cut_length_m", r.get("cut_length_mm", 0) / 1000.0) * r.get("quantity", 1)
            for r in legacy_result.calculated_resources
        )
        total_pierce_count = sum(
            r.get("pierce_count", 0) * r.get("quantity", 1)
            for r in legacy_result.calculated_resources
        )
        total_sheet_area_m2 = sum(
            r.get("sheet_area_m2", 0) * r.get("quantity", 1)
            for r in legacy_result.calculated_resources
        )
        return LegacyPanelServiceResult(
            panel_mode=data.panel_mode,
            preset_code=data.preset_code,
            preset_name=data.preset_name,
            material=data.material,
            thickness_mm=data.thickness_mm,
            width_mm=data.width_mm,
            height_mm=data.height_mm,
            quantity=data.quantity,
            calculated_resources=legacy_result.calculated_resources,
            dxf_path=legacy_result.dxf_path,
            warnings=legacy_result.warnings,
            legacy_result_raw=legacy_result.legacy_result_raw,
            cut_piece_payload=cut_piece_payload,
            quotation_payload=quotation_payload,
            cut_length_m=total_cut_length_m,
            pierce_count=total_pierce_count,
            sheet_area_m2=total_sheet_area_m2,
        )


def write_panel_service_outputs(result: LegacyPanelServiceResult, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    panel_payload = result.to_dict()
    (output_dir / "panel_result.json").write_text(json.dumps(panel_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    (output_dir / "quotation_payload.json").write_text(
        json.dumps(result.quotation_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (output_dir / "cut_piece_payload.json").write_text(
        json.dumps(result.cut_piece_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    manifest = {
        "panel_mode": result.panel_mode,
        "preset_code": result.preset_code,
        "preset_name": result.preset_name,
        "material": result.material,
        "thickness_mm": result.thickness_mm,
        "quantity": result.quantity,
        "dxf_path": str(result.dxf_path),
        "warnings": result.warnings,
        "trace": {
            "engine": "legacy_panel_engine",
            "quotation_file": str(output_dir / "quotation_payload.json"),
            "cut_piece_file": str(output_dir / "cut_piece_payload.json"),
            "panel_result_file": str(output_dir / "panel_result.json"),
        },
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest_path
