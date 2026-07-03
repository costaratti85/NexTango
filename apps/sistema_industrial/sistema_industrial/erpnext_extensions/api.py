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


def send_quotation(payload: dict) -> dict:
    """Envía un payload ya construido por quotation_builder al ERPNext real."""
    from sistema_industrial.erpnext_extensions.client import ERPNextClient
    return ERPNextClient().post_quotation(payload)


def list_presupuestos(customer: str | None = None, limit: int = 50) -> list[dict]:
    """Lista Quotations de Panel Decorativo desde ERPNext.

    Filtra por ítems PANEL-DEC. Opcionalmente, si se pasa customer,
    restringe además por party_name.
    """
    from sistema_industrial.erpnext_extensions.client import ERPNextClient
    client = ERPNextClient()
    filters: list = [["Quotation Item", "item_code", "=", "PANEL-DEC"]]
    if customer:
        filters.append(["party_name", "=", customer])
    return client.list_docs(
        "Quotation",
        filters=filters,
        fields=["name", "party_name", "status", "grand_total", "transaction_date", "currency"],
        limit=limit,
    )


def get_presupuesto(name: str) -> dict:
    """Devuelve una Quotation de ERPNext por nombre (e.g. SAL-QTN-2026-00001).

    Lanza KeyError si no existe.
    """
    from sistema_industrial.erpnext_extensions.client import ERPNextClient
    doc = ERPNextClient().get_doc("Quotation", name)
    if doc is None:
        raise KeyError(f"Quotation {name!r} no encontrado en ERPNext")
    return doc
