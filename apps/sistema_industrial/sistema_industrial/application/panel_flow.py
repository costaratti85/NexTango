"""End-to-end panel preset flow.

This is the first operational trunk:
Panel input -> quotation payload for ERPNext -> pending cut part.
It stays framework-neutral so Codex can later wrap it with Frappe DocTypes/API.
"""

from dataclasses import dataclass
from pathlib import Path

from sistema_industrial.core.models import PendingCutPart
from sistema_industrial.presets.panel_decorativo import PanelDecorativoInput, build_panel_quotation, build_pending_cut_part
from sistema_industrial.pricing_sync.price_cache import PriceCache
from sistema_industrial.quoting.quotation_builder import build_erpnext_quotation_payload


@dataclass(frozen=True)
class PanelFlowResult:
    quotation_payload: dict
    pending_cut_part: PendingCutPart


def run_panel_flow(data: PanelDecorativoInput, price_cache: PriceCache) -> PanelFlowResult:
    quotation = build_panel_quotation(data)
    payload = build_erpnext_quotation_payload(quotation, price_cache)
    pending_part = build_pending_cut_part(data)
    return PanelFlowResult(payload, pending_part)


def run_panel_flow_from_price_file(data: PanelDecorativoInput, price_file: Path) -> PanelFlowResult:
    return run_panel_flow(data, PriceCache.load(price_file))
