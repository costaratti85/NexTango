from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_codex_one_shot_order_exists():
    text = (ROOT / "docs" / "24_MONDAY_CODEX_SINGLE_ORDER.md").read_text(encoding="utf-8")
    assert "No implementar nesting" in text
    assert "No implementar CAM" in text
    assert "ERPNext/Frappe" in text


def test_agent_zoo_has_first_slice_agents():
    text = (ROOT / "docs" / "29_AGENT_ZOO.md").read_text(encoding="utf-8")
    for agent in ["Atlas", "Forge", "Tango", "Punto", "Nido", "Gemu", "Vega", "Orbit", "Prisma", "Security"]:
        assert agent in text
