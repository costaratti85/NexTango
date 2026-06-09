import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCTYPE_ROOT = ROOT / "apps" / "sistema_industrial" / "sistema_industrial" / "doctype"

EXPECTED_DOCTYPES = {
    "si_preset": "SI Preset",
    "si_client_piece": "SI Client Piece",
    "si_cut_piece": "SI Cut Piece",
    "si_cut_batch": "SI Cut Batch",
    "si_tango_price_cache": "SI Tango Price Cache",
    "si_linear_cut_request": "SI Linear Cut Request",
}


def test_frappe_doctype_stubs_exist_with_expected_names():
    for folder, doctype_name in EXPECTED_DOCTYPES.items():
        json_path = DOCTYPE_ROOT / folder / f"{folder}.json"
        py_path = DOCTYPE_ROOT / folder / f"{folder}.py"

        assert json_path.exists()
        assert py_path.exists()

        payload = json.loads(json_path.read_text(encoding="utf-8"))
        assert payload["doctype"] == "DocType"
        assert payload["name"] == doctype_name
        assert payload["module"] == "Sistema Industrial"
        assert payload["custom"] == 0
