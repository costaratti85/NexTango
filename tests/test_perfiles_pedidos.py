"""Tests de los helpers de persistencia de api/perfiles.py (sin frappe)."""
import importlib.util
import sys
from datetime import date
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "apps" / "sistema_industrial" / "sistema_industrial" / "api" / "perfiles.py"
)

spec = importlib.util.spec_from_file_location("si_api_perfiles", MODULE_PATH)
perfiles = importlib.util.module_from_spec(spec)
sys.modules["si_api_perfiles"] = perfiles
spec.loader.exec_module(perfiles)


def test_next_id_arranca_en_0001(tmp_path):
    pid = perfiles._next_pedido_id(tmp_path, today=date(2026, 7, 2))
    assert pid == "PL-20260702-0001"


def test_next_id_incrementa_por_dia(tmp_path):
    (tmp_path / "PL-20260702-0007.json").write_text("{}", encoding="utf-8")
    (tmp_path / "PL-20260701-0099.json").write_text("{}", encoding="utf-8")
    assert perfiles._next_pedido_id(tmp_path, today=date(2026, 7, 2)) == "PL-20260702-0008"


def test_save_y_get_roundtrip(tmp_path):
    data = {"cliente": "ACME", "ref": "Zócalo", "segs": [{"len": 50, "ang": 90}], "total": 1234.5}
    res = perfiles._save_pedido(data, base_dir=tmp_path)
    assert res["ok"] and res["id"].startswith("PL-")
    full = perfiles._get_pedido(res["id"], base_dir=tmp_path)
    assert full["cliente"] == "ACME"
    assert full["segs"] == [{"len": 50, "ang": 90}]
    assert full["id"] == res["id"]


def test_list_solo_cabecera_orden_desc(tmp_path):
    perfiles._save_pedido({"cliente": "A", "total": 1, "plan": {"x": 1}}, base_dir=tmp_path)
    perfiles._save_pedido({"cliente": "B", "total": 2, "plan": {"x": 2}}, base_dir=tmp_path)
    rows = perfiles._list_pedidos(base_dir=tmp_path)
    assert [r["cliente"] for r in rows] == ["B", "A"]
    assert all("plan" not in r for r in rows)


def test_get_inexistente(tmp_path):
    assert perfiles._get_pedido("PL-20260101-9999", base_dir=tmp_path) == {
        "ok": False, "error": "not found",
    }
    assert perfiles._get_pedido("../../etc/passwd", base_dir=tmp_path)["ok"] is False
