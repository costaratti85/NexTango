"""Tango API client placeholder.

Real implementation must be adapter-based because Tango endpoints available in
the company may differ: pedidos import API, Nexo notification API, price list
update API, etc.
"""

from dataclasses import dataclass
from typing import Protocol
from sistema_industrial.tango_sync.schemas import TangoFiscalDocument, TangoPrice


class TangoClient(Protocol):
    def get_price_list(self, list_name: str = "default") -> list[TangoPrice]: ...
    def get_fiscal_documents_since(self, iso_date: str) -> list[TangoFiscalDocument]: ...
    def create_order(self, payload: dict) -> str: ...


@dataclass
class TangoClientConfig:
    base_url: str
    token: str
    company_id: str | None = None
