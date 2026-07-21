"""Local cache of Tango price list for ERPNext quotations.

Tango remains the master of published prices. ERPNext/SistemaIndustrial may use
this cache to quote without calling Tango live on every quotation.
"""

from dataclasses import dataclass, asdict
from pathlib import Path
import json
from sistema_industrial.core.models import Money


@dataclass(frozen=True)
class PriceRecord:
    item_code: str
    unit_price: float
    currency: str = "ARS"
    source: str = "tango"
    list_name: str = "default"


class PriceCache:
    def __init__(self, records: dict[str, PriceRecord] | None = None):
        self.records = records or {}

    def get(self, item_code: str) -> Money | None:
        record = self.records.get(item_code)
        if record is None:
            return None
        return Money(record.unit_price, record.currency)

    def require(self, item_code: str) -> Money:
        price = self.get(item_code)
        if price is None:
            raise KeyError(f"Missing price for item {item_code!r}")
        return price

    def upsert(self, record: PriceRecord) -> None:
        self.records[record.item_code] = record

    @classmethod
    def load(cls, path: Path) -> "PriceCache":
        data = json.loads(path.read_text(encoding="utf-8"))
        # FALLA RUIDOSA (MSG_165 / MSG_019): un JSON sin la clave "prices" NO es
        # un PriceCache. Antes se hacía data.get("prices", []) -> cache VACÍO en
        # silencio; ese fue el bug del $0 (daily_prices.json, dict plano, se
        # cargaba como PriceCache y devolvía 0 sin un solo error). Si el esquema
        # no es el esperado, gritamos en vez de tragárnoslo.
        if not isinstance(data, dict) or "prices" not in data:
            claves = sorted(data.keys()) if isinstance(data, dict) else type(data).__name__
            raise ValueError(
                f"PriceCache.load: {path} no es un PriceCache válido. "
                f"Se esperaba {{'prices': [...]}}; se recibió: {claves}"
            )
        return cls({row["item_code"]: PriceRecord(**row) for row in data["prices"]})

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"prices": [asdict(record) for record in self.records.values()]}
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
