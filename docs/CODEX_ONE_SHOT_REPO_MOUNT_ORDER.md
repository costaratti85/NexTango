> ⚠️ **CORRECCIÓN 2026-07-19 — DECISION_011.** Este documento contiene la errata **"Tango maestro de precios"** (precios a/desde Tango, sync de precios Tango, cache de precios Tango). **ES FALSO: Tango NO maneja precios.** El pricing se hace en **EXCEL**; hoy el **vendedor los carga a mano** en el sistema (ERPNext). Tango es **fiscal/facturación**. Todo tramo de este doc que diga "precios a/desde Tango", "Tango maestro/publicados de precios" o "sync/cache de precios Tango" **queda SIN EFECTO**. Ver `coordination/decisions/DECISION_011_PAGINA_PRECIOS_SOLO_LECTURA.md`.

---

# Monday Codex Single Order

Copiar y pegar esta orden completa a Codex al iniciar el repo nuevo.

```text
Codex, vas a montar el nuevo repositorio Sistema_Industrial_Nextango desde esta semilla.

Contexto obligatorio:
- Leer README.md.
- Leer docs/00_PROJECT_NORTH_STAR.md.
- Leer docs/00_BRUJU_MESSAGE_TO_TEAM.md.
- Leer docs/22_FIRST_SLICE_TEAM.md.
- Leer docs/23_AGENT_PERMISSIONS_MATRIX.md.

Objetivo de esta sesion:
Dejar el repo listo para trabajo real, sin tocar ERPNext core, sin tocar Tango real y sin romper los tests existentes.

Reglas inviolables:
1. ERPNext/Frappe es columna operativa.
2. SistemaIndustrial sera una app Frappe propia llamada sistema_industrial.
3. Tango es frontera fiscal/comercial/precios maestros.
4. Excel sigue siendo motor humano de pricing.
5. CypCut hace nesting.
6. El postprocesador existente hace entradas, secuencia y G-code.
7. No implementar nesting.
8. No implementar CAM/G-code.
9. Mantener dominio neutral testeable fuera de adaptadores.
10. Todo cambio debe tener test o justificacion.

Tareas concretas:
1. Inspeccionar la estructura actual.
2. Eliminar caches, archivos generados y cualquier basura accidental.
3. Verificar que corra:
   PYTHONPATH=apps/sistema_industrial pytest -q
4. Verificar demo:
   PYTHONPATH=apps/sistema_industrial python tools/demo_panel_to_cut_batch.py
5. Reorganizar solo si hace falta, manteniendo compatibilidad.
6. Crear o mejorar estructura de app Frappe sin requerir bench todavia.
7. Preparar DocTypes JSON/stubs para:
   - SI Preset
   - SI Client Piece
   - SI Cut Piece
   - SI Cut Batch
   - SI Tango Price Cache
   - SI Linear Cut Request
8. Crear issues o archivos de tarea internos para Atlas, Forge, Tango, Punto, Nido, Prisma, Vega, Orbit, Gemu y Security.
9. No conectar con Tango real.
10. No instalar en ERPNext real hasta que tests y demo pasen.

Criterio de exito:
- Repo limpio.
- Tests pasan.
- Demo genera quotation_payload.json, cut_queue.json, DXF y manifest.
- Primer MVP queda claro:
  panel decorativo -> cotizacion estilo ERPNext -> pieza pendiente -> cola -> lote DXF por espesor.
- Se entrega reporte con archivos modificados, comandos corridos y proximos pasos.
```