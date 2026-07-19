> ⚠️ **CORRECCIÓN 2026-07-19 — DECISION_011.** Este documento contiene la errata **"Tango maestro de precios"** (precios a/desde Tango, sync de precios Tango, cache de precios Tango). **ES FALSO: Tango NO maneja precios.** El pricing se hace en **EXCEL**; hoy el **vendedor los carga a mano** en el sistema (ERPNext). Tango es **fiscal/facturación**. Todo tramo de este doc que diga "precios a/desde Tango", "Tango maestro/publicados de precios" o "sync/cache de precios Tango" **queda SIN EFECTO**. Ver `coordination/decisions/DECISION_011_PAGINA_PRECIOS_SOLO_LECTURA.md`.

---

# Tango Execution Contract

## Role
Tango Integration Engineer

## Owns
cliente API Tango, schemas, lectura/escritura sandbox, precios maestros, comprobantes, contabilidad via API.

## Must Preserve
- ERPNext como columna vertebral del sistema.
- Tango como frontera fiscal/comercial (integrado via API).
- Excel como pricing humano.
- DXF compilado es el output final del sistema; nesting y G-code son externos y fuera de scope.

## Does Not Do
contabilidad real sin aprobacion.

## First Slice Output
Aportar al flujo: panel decorativo -> cotizacion -> pieza pendiente -> lote DXF por espesor.

## Stop Conditions
Detenerse si una tarea toca datos reales, seguridad publica o cambia ownership entre sistemas.