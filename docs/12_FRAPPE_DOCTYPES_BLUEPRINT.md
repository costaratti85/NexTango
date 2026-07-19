> ⚠️ **CORRECCIÓN 2026-07-19 — DECISION_011.** Este documento contiene la errata **"Tango maestro de precios"** (precios a/desde Tango, sync de precios Tango, cache de precios Tango). **ES FALSO: Tango NO maneja precios.** El pricing se hace en **EXCEL**; hoy el **vendedor los carga a mano** en el sistema (ERPNext). Tango es **fiscal/facturación**. Todo tramo de este doc que diga "precios a/desde Tango", "Tango maestro/publicados de precios" o "sync/cache de precios Tango" **queda SIN EFECTO**. Ver `coordination/decisions/DECISION_011_PAGINA_PRECIOS_SOLO_LECTURA.md`.

---

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

- SI Linear Cut Plan
- SI Linear Remnant
- SI Client Piece Revision
- SI Piece Status Event
- SI Portal Access Review