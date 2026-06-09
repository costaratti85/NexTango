"""Local demo: panel preset -> quotation payload -> queue -> cut batch DXF.

Run from repo root:
PYTHONPATH=apps/sistema_industrial python tools/demo_panel_to_cut_batch.py
"""

from pathlib import Path
import json

from sistema_industrial.application.panel_flow import run_panel_flow_from_price_file
from sistema_industrial.cutting.repository import FileCutQueueRepository
from sistema_industrial.cutting.api import compile_batch_from_queue
from sistema_industrial.presets.panel_decorativo import PanelDecorativoInput

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "local_output"
PRICE_FILE = ROOT / "fixtures/prices/tango_price_list_sample.json"
QUEUE_FILE = OUT / "cut_queue.json"


def main() -> None:
    OUT.mkdir(exist_ok=True)
    data = PanelDecorativoInput(
        width_mm=1200,
        height_mm=600,
        quantity=2,
        material="chapa",
        thickness_mm=3,
        customer_code="CLIENTE-DEMO",
        order_id="PED-DEMO-001",
    )
    result = run_panel_flow_from_price_file(data, PRICE_FILE)
    (OUT / "quotation_payload.json").write_text(json.dumps(result.quotation_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    repo = FileCutQueueRepository(QUEUE_FILE)
    repo.save([])
    repo.append(result.pending_cut_part)

    batch = compile_batch_from_queue(QUEUE_FILE, "chapa", 3, OUT / "CUT_BATCH_CHAPA_3MM_DEMO.dxf")
    print(json.dumps({
        "quotation": str(OUT / "quotation_payload.json"),
        "queue": str(QUEUE_FILE),
        "dxf": str(batch.dxf_path),
        "manifest": str(batch.manifest_path),
        "part_count": batch.part_count,
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
