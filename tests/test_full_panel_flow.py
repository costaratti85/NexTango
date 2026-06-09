from pathlib import Path

from sistema_industrial.application.panel_flow import run_panel_flow_from_price_file
from sistema_industrial.presets.panel_decorativo import PanelDecorativoInput


def test_panel_flow_builds_quotation_and_pending_part():
    price_file = Path("fixtures/prices/tango_price_list_sample.json")
    result = run_panel_flow_from_price_file(
        PanelDecorativoInput(1000, 500, 2, "chapa", 3, "C001", "P001"),
        price_file,
    )
    assert result.quotation_payload["doctype"] == "Quotation"
    assert result.quotation_payload["items"][0]["rate"] > 0
    assert result.pending_cut_part.material == "chapa"
    assert result.pending_cut_part.quantity == 2
