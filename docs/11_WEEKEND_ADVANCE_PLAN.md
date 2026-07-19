> ⚠️ **CORRECCIÓN 2026-07-19 — DECISION_011.** Este documento contiene la errata **"Tango maestro de precios"** (precios a/desde Tango, sync de precios Tango, cache de precios Tango). **ES FALSO: Tango NO maneja precios.** El pricing se hace en **EXCEL**; hoy el **vendedor los carga a mano** en el sistema (ERPNext). Tango es **fiscal/facturación**. Todo tramo de este doc que diga "precios a/desde Tango", "Tango maestro/publicados de precios" o "sync/cache de precios Tango" **queda SIN EFECTO**. Ver `coordination/decisions/DECISION_011_PAGINA_PRECIOS_SOLO_LECTURA.md`.

---

# Weekend advance plan

The weekend goal is to leave Codex/engineers with a clean runway for Monday.

## Build now

1. Frappe app skeleton.
2. Neutral domain models.
3. Preset panel calculation.
4. ERPNext quotation payload builder.
5. Tango price cache abstraction.
6. Stock movement events from Tango invoices/credit notes.
7. Cut batch compiler by material/thickness.
8. Tests proving the trunk flow.

## Do not build yet

- Full Tango API implementation.
- Full Frappe DocTypes.
- CypCut nesting.
- G-code generation.
- ERPNext core modifications.