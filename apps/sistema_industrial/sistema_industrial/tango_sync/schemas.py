"""Tango boundary schemas.

These are not final Tango API payloads. They define the canonical internal shape
that Tango adapters must provide/consume.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TangoArticle:
    code: str
    description: str
    barcode: str | None = None
    uom: str = "unidad"


@dataclass(frozen=True)
class TangoPrice:
    item_code: str
    price: float
    currency: str = "ARS"
    list_name: str = "default"


@dataclass(frozen=True)
class TangoInvoiceLine:
    item_code: str
    quantity: float
    description: str | None = None


@dataclass(frozen=True)
class TangoFiscalDocument:
    document_id: str
    document_type: str
    customer_code: str | None
    lines: list[TangoInvoiceLine]
    is_credit_note: bool = False
