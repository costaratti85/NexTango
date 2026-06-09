"""Fake Tango client for local tests and Codex work.

Real Tango API credentials must never be committed. This fake lets us keep the
integration boundary executable until the real adapter is implemented.
"""

from sistema_industrial.tango_sync.schemas import TangoFiscalDocument, TangoPrice


class FakeTangoClient:
    def __init__(self, prices: list[TangoPrice] | None = None, documents: list[TangoFiscalDocument] | None = None):
        self._prices = prices or []
        self._documents = documents or []
        self.created_orders: list[dict] = []

    def get_price_list(self, list_name: str = "default") -> list[TangoPrice]:
        return [p for p in self._prices if p.list_name == list_name]

    def get_fiscal_documents_since(self, iso_date: str) -> list[TangoFiscalDocument]:
        return self._documents

    def create_order(self, payload: dict) -> str:
        self.created_orders.append(payload)
        return f"FAKE-TANGO-ORDER-{len(self.created_orders):04d}"
