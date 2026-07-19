> ⚠️ **CORRECCIÓN 2026-07-19 — DECISION_011.** Este documento contiene la errata **"Tango maestro de precios"** (precios a/desde Tango, sync de precios Tango, cache de precios Tango). **ES FALSO: Tango NO maneja precios.** El pricing se hace en **EXCEL**; hoy el **vendedor los carga a mano** en el sistema (ERPNext). Tango es **fiscal/facturación**. Todo tramo de este doc que diga "precios a/desde Tango", "Tango maestro/publicados de precios" o "sync/cache de precios Tango" **queda SIN EFECTO**. Ver `coordination/decisions/DECISION_011_PAGINA_PRECIOS_SOLO_LECTURA.md`.

---

# Project North Star

SistemaIndustrial no reemplaza herramientas buenas: las integra.

## Stack

- ERPNext/Frappe: columna vertebral del sistema, operación.
- Tango Gestión: fiscal, contable, artículos, clientes, proveedores y precios publicados — integrado via API.
- Excel: pricing humano.
- OCR: ingreso de facturas de proveedor.
- CypCut: nesting (externo, no reimplementar).
- Postprocesador propio: G-code y secuencia de corte (externo, no reimplementar).
- SistemaIndustrial: lógica industrial, presets, generación DXF, integración y trazabilidad.

El sistema genera y compila archivos DXF con las piezas a cortar y/o plegar.
Nesting, G-code y secuencia de máquina son responsabilidad de herramientas externas y están fuera del scope del sistema.

## Documentos de referencia vinculantes

- `docs/00_BRUJULA_DOCUMENT_FUNDACIONAL.md` — **norte completo del proyecto a largo plazo**, escrito por Brújula. Ningún agente puede contradecirlo.
- `docs/00_BRUJU_MESSAGE_TO_TEAM.md` — mensaje al equipo. Binding context para toda decisión técnica.
- `docs/01_ARCHITECTURE.md` — app Frappe sobre ERPNext, regla de módulos.
- `docs/03_TANGO_BOUNDARY.md` — lo que Tango posee y cómo se integra.
- `coordination/decisions/` — decisiones técnicas vinculantes.

## Primera meta concreta (rebanada activa)

Panel decorativo → cotización real en ERPNext, con recursos calculados, precios consultados, DXF generado y trazabilidad lista para taller.

Después se ensancha siguiendo el orden de flujos del documento fundacional.