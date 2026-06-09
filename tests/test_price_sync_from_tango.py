from sistema_industrial.pricing_sync.sync_from_tango import sync_price_cache_from_tango
from sistema_industrial.tango_sync.fake_client import FakeTangoClient
from sistema_industrial.tango_sync.schemas import TangoPrice


def test_sync_price_cache_from_fake_tango(tmp_path):
    client = FakeTangoClient([TangoPrice("PANEL_DECORATIVO", 1234)])
    cache = sync_price_cache_from_tango(client, tmp_path / "prices.json")
    assert cache.require("PANEL_DECORATIVO").amount == 1234
    assert (tmp_path / "prices.json").exists()
