# Frappe DocTypes blueprint

Initial DocTypes for the SistemaIndustrial app:

- SI Preset: configurable industrial preset, starting with panel_decorativo.
- SI Client Piece: customer-owned reusable piece reference and revision marker.
- SI Cut Piece: part waiting for batching and shop-floor status tracking.
- SI Cut Batch: selected material/thickness batch exported to DXF and manifest.
- SI Tango Price Cache: synchronized prices from Tango.
- SI Linear Cut Request: future neutral request for linear cutting work.

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
- SI Client Piece Revision
- SI Piece Status Event
- SI Portal Access Review
