from sistema_industrial.presets.panel_decorativo import PanelDecorativoInput, build_panel_quotation, build_pending_cut_part
from sistema_industrial.pricing_sync.price_cache import PriceCache, PriceRecord
from sistema_industrial.quoting.quotation_builder import build_erpnext_quotation_payload


def test_panel_preset_builds_quotation_payload():
    data = PanelDecorativoInput(width_mm=1000, height_mm=500, quantity=2, material="chapa", thickness_mm=3.0, customer_code="C001")
    quotation = build_panel_quotation(data)
    cache = PriceCache({"PANEL_DECORATIVO": PriceRecord("PANEL_DECORATIVO", 1234.5)})
    payload = build_erpnext_quotation_payload(quotation, cache)
    assert payload["doctype"] == "Quotation"
    assert payload["party_name"] == "C001"
    assert payload["items"][0]["rate"] == 1234.5
    assert payload["si_resources"][0]["code"] == "CHAPA_M2"


def test_panel_preset_builds_pending_cut_part():
    data = PanelDecorativoInput(width_mm=1000, height_mm=500, quantity=2, material="chapa", thickness_mm=3.0, order_id="SO-1")
    part = build_pending_cut_part(data)
    assert part.order_id == "SO-1"
    assert part.material == "chapa"
    assert part.thickness_mm == 3.0
    assert part.quantity == 2
