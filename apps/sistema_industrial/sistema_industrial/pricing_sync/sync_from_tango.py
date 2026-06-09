"""Sync Tango published prices into the local ERPNext/SI price cache."""

from pathlib import Path
from typing import Protocol

from sistema_industrial.pricing_sync.price_cache import PriceCache, PriceRecord
from sistema_industrial.tango_sync.schemas import TangoPrice


class TangoPriceProvider(Protocol):
    def get_price_list(self, list_name: str = "default") -> list[TangoPrice]: ...


def sync_price_cache_from_tango(provider: TangoPriceProvider, output_path: Path, list_name: str = "default") -> PriceCache:
    cache = PriceCache()
    for price in provider.get_price_list(list_name=list_name):
        cache.upsert(PriceRecord(price.item_code, price.price, price.currency, "tango", price.list_name))
    cache.save(output_path)
    return cache
