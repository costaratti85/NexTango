"""Stock movement events produced from Tango fiscal documents."""

from dataclasses import dataclass
from sistema_industrial.tango_sync.schemas import TangoFiscalDocument


@dataclass(frozen=True)
class StockMovement:
    item_code: str
    quantity_delta: float
    reason: str
    source_document_id: str


def fiscal_document_to_stock_movements(doc: TangoFiscalDocument) -> list[StockMovement]:
    sign = 1 if doc.is_credit_note else -1
    reason = "tango_credit_note" if doc.is_credit_note else "tango_invoice"
    return [
        StockMovement(
            item_code=line.item_code,
            quantity_delta=sign * line.quantity,
            reason=reason,
            source_document_id=doc.document_id,
        )
        for line in doc.lines
    ]
