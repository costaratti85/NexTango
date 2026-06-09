# Frappe DocTypes blueprint

Initial DocTypes for the SistemaIndustrial app:

- SI Preset Order: preset-generated commercial request.
- SI Pending Cut Part: part waiting for cutting.
- SI Cut Batch: selected material/thickness batch exported to DXF.
- SI Tango Price Cache: synchronized prices from Tango.
- SI Tango Fiscal Document: invoices/credit notes mirrored from Tango.
- SI OCR Supplier Intake: supplier invoice OCR validation record.

ERPNext standard documents remain in use:

- Quotation
- Sales Order
- Item
- Warehouse
- Stock Entry

Rule: extend ERPNext, do not fork or rewrite ERPNext core.


## Future DocTypes to Preserve

- SI Linear Cut Request
- SI Linear Cut Plan
- SI Linear Remnant
- SI Client Piece
- SI Client Piece Revision
- SI Piece Status Event
- SI Portal Access Review
