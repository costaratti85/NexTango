"""Run the legacy decorative panel engine through the Nextango adapter.

From repo root:
    PYTHONPATH=apps/sistema_industrial python tools/run_panel_legacy_demo.py
"""

from pathlib import Path
import json

from sistema_industrial.presets.panel_service import (
    LegacyPanelService,
    LegacyPanelServiceInput,
    write_panel_service_outputs,
)
from sistema_industrial.pricing_sync.price_cache import PriceCache


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs" / "panel_legacy_demo"
PRICE_FILE = ROOT / "fixtures" / "prices" / "tango_price_list_sample.json"


def main() -> None:
    price_cache = PriceCache.load(PRICE_FILE)
    service = LegacyPanelService(price_cache=price_cache)
    data = LegacyPanelServiceInput(
        preset_code="PANEL_DECORATIVO_LEGACY_TRESBOLILLO",
        preset_name="Tresbolillo circular",
        material="chapa",
        thickness_mm=3.0,
        width_mm=300.0,
        height_mm=200.0,
        quantity=1,
        customer_code="CLIENTE-DEMO",
        order_id="PED-LEGACY-DEMO-001",
        pattern_type="tresbolillo",
        margin_mm=20.0,
        hole_diameter_mm=20.0,
        hole_distance_mm=60.0,
    )
    result = service.run(data, OUTPUT_DIR)
    manifest_path = write_panel_service_outputs(result, OUTPUT_DIR)
    print(
        json.dumps(
            {
                "panel_result": str(OUTPUT_DIR / "panel_result.json"),
                "quotation_payload": str(OUTPUT_DIR / "quotation_payload.json"),
                "cut_piece_payload": str(OUTPUT_DIR / "cut_piece_payload.json"),
                "dxf": str(result.dxf_path),
                "manifest": str(manifest_path),
                "warnings": result.warnings,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
