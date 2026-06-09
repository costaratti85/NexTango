from sistema_industrial.stock_sync.events import fiscal_document_to_stock_movements
from sistema_industrial.tango_sync.schemas import TangoFiscalDocument, TangoInvoiceLine


def test_invoice_decreases_stock():
    doc = TangoFiscalDocument("F1", "FACTURA", "C001", [TangoInvoiceLine("A1", 3)])
    movements = fiscal_document_to_stock_movements(doc)
    assert movements[0].quantity_delta == -3


def test_credit_note_restores_stock():
    doc = TangoFiscalDocument("NC1", "NOTA_CREDITO", "C001", [TangoInvoiceLine("A1", 3)], is_credit_note=True)
    movements = fiscal_document_to_stock_movements(doc)
    assert movements[0].quantity_delta == 3
