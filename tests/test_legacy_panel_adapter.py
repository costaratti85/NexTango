from pathlib import Path
import hashlib

from sistema_industrial.presets.legacy_panel_adapter import (
    LegacyPanelAdapter,
    LegacyPanelRunRequest,
    find_legacy_panel_dir,
)
from sistema_industrial.presets.panel_service import LegacyPanelService, LegacyPanelServiceInput
from sistema_industrial.pricing_sync.price_cache import PriceCache, PriceRecord


def _legacy_file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_legacy_panel_adapter_finds_program():
    legacy_dir = find_legacy_panel_dir()
    assert legacy_dir.name == "Panel Decorativo"
    assert (legacy_dir / "main.py").exists()


def test_legacy_panel_adapter_runs_and_returns_normalized_result(tmp_path: Path):
    output_dxf = tmp_path / "legacy_panel.dxf"
    result = LegacyPanelAdapter().run(
        LegacyPanelRunRequest(
            preset_code="PANEL_DECORATIVO_LEGACY_TRESBOLILLO",
            preset_name="Tresbolillo circular",
            material="chapa",
            thickness_mm=3.0,
            width_mm=300.0,
            height_mm=200.0,
            quantity=1,
            output_dxf_path=output_dxf,
        )
    )

    assert result.dxf_path.exists()
    assert result.dxf_path.read_text(encoding="utf-8", errors="ignore").startswith("  0")
    assert result.calculated_resources[0]["material"] == "chapa"
    assert result.calculated_resources[0]["thickness_mm"] == 3.0
    assert result.legacy_result_raw["items"]


def test_legacy_panel_adapter_runs_dxf_pattern_grid_without_modifying_legacy(tmp_path: Path):
    legacy_dir = find_legacy_panel_dir()
    legacy_main = legacy_dir / "main.py"
    legacy_hash_before = _legacy_file_hash(legacy_main)
    output_dxf = tmp_path / "legacy_dxf_pattern_panel.dxf"

    result = LegacyPanelAdapter().run(
        LegacyPanelRunRequest(
            preset_code="PANEL_DECORATIVO_LEGACY_DXF_PATTERN",
            preset_name="Patron DXF repetido",
            material="chapa",
            thickness_mm=3.0,
            width_mm=300.0,
            height_mm=200.0,
            quantity=1,
            output_dxf_path=output_dxf,
            pattern_type="dxf",
            pattern_dxf_path=legacy_dir / "input.dxf",
            step_x_mm=84.0,
            step_y_mm=84.0,
            rows=1,
            columns=1,
        )
    )

    assert result.dxf_path.exists()
    assert result.calculated_resources[0]["name"].startswith("Patron DXF repetido")
    assert result.legacy_result_raw["request"]["pattern_type"] == "dxf"
    assert result.legacy_result_raw["request"]["pattern_dxf_path"].endswith("input.dxf")
    assert result.legacy_result_raw["request"]["offset_x_mm"] == 84.0
    assert result.legacy_result_raw["request"]["offset_y_mm"] == 84.0
    assert _legacy_file_hash(legacy_main) == legacy_hash_before


def test_legacy_panel_service_returns_nextango_payloads(tmp_path: Path):
    service = LegacyPanelService(
        price_cache=PriceCache({"PANEL_DECORATIVO": PriceRecord("PANEL_DECORATIVO", 1234.5)})
    )
    result = service.run(LegacyPanelServiceInput(), tmp_path)

    assert result.preset_code == "PANEL_DECORATIVO_LEGACY"
    assert result.panel_mode == "tresbolillo"
    assert result.dxf_path.exists()
    assert result.quotation_payload["doctype"] == "Quotation"
    assert result.quotation_payload["items"][0]["rate"] == 1234.5
    assert result.cut_piece_payload["status"] == "pending"
    assert result.cut_piece_payload["dxf_path"].endswith("_legacy_panel.dxf")
