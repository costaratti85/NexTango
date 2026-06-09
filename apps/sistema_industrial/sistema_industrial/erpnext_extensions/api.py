"""Frappe API facade placeholders.

These functions are intentionally thin. Codex/Forge can later add @frappe.whitelist
and DocType persistence once the app is installed in ERPNext.
"""

try:
    import frappe  # type: ignore
except Exception:  # pragma: no cover - local non-Frappe test environment
    frappe = None

from pathlib import Path
from sistema_industrial.presets.panel_decorativo import PanelDecorativoInput
from sistema_industrial.application.panel_flow import run_panel_flow_from_price_file
from sistema_industrial.cutting.api import compile_batch_from_queue


def create_panel_quotation_preview(input_payload: dict, price_file: str) -> dict:
    data = PanelDecorativoInput(**input_payload)
    result = run_panel_flow_from_price_file(data, Path(price_file))
    return {
        "quotation_payload": result.quotation_payload,
        "pending_cut_part": result.pending_cut_part.__dict__,
    }


def compile_cut_batch_preview(queue_path: str, material: str, thickness_mm: float, output_path: str) -> dict:
    result = compile_batch_from_queue(Path(queue_path), material, float(thickness_mm), Path(output_path))
    return result.__dict__
