> ⚠️ **CORRECCIÓN 2026-07-19 — DECISION_011.** Este documento contiene la errata **"Tango maestro de precios"** (precios a/desde Tango, sync de precios Tango, cache de precios Tango). **ES FALSO: Tango NO maneja precios.** El pricing se hace en **EXCEL**; hoy el **vendedor los carga a mano** en el sistema (ERPNext). Tango es **fiscal/facturación**. Todo tramo de este doc que diga "precios a/desde Tango", "Tango maestro/publicados de precios" o "sync/cache de precios Tango" **queda SIN EFECTO**. Ver `coordination/decisions/DECISION_011_PAGINA_PRECIOS_SOLO_LECTURA.md`.

---

# First Slice Backlog

P0 - antes del lunes:
- Repo semilla listo.
- Contratos de agentes claros.
- Orden unica para Codex.
- Tests existentes pasando.

P1 - primer trabajo Codex:
- Limpiar repo.
- Preparar estructura Frappe app.
- Mantener dominio neutral.
- Crear stubs de DocTypes.
- Ejecutar demo panel -> lote DXF.

P2 - primera demo operativa:
- UI interna vendedor: cargar panel decorativo.
- Cotizacion ERPNext draft.
- Pieza pendiente con estado.
- UI taller: seleccionar material/espesor.
- Descargar DXF compilado.

P3 - ampliar:
- Biblioteca de piezas cliente.
- Corte lineal Gemu.
- OCR proveedor.
- Sincronizacion precios Tango.
- Portal cliente/totem solo despues de seguridad.