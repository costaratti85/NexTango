> ⚠️ **CORRECCIÓN 2026-07-19 — DECISION_011.** Este documento contiene la errata **"Tango maestro de precios"** (precios a/desde Tango, sync de precios Tango, cache de precios Tango). **ES FALSO: Tango NO maneja precios.** El pricing se hace en **EXCEL**; hoy el **vendedor los carga a mano** en el sistema (ERPNext). Tango es **fiscal/facturación**. Todo tramo de este doc que diga "precios a/desde Tango", "Tango maestro/publicados de precios" o "sync/cache de precios Tango" **queda SIN EFECTO**. Ver `coordination/decisions/DECISION_011_PAGINA_PRECIOS_SOLO_LECTURA.md`.

---

# TASK 006 - Tango price cache adapter

Owner: Tango + Atlas

Implement an adapter that converts Tango price list rows into PriceRecord objects.

Do not require live Tango access for tests. Use fixture JSON.

Acceptance:

- fixture -> PriceCache
- PriceCache can price an ERPNext quotation payload
- missing prices are reported clearly