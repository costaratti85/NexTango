# MEMO — Punto a Nova

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-17  
**Asunto:** TASK_016 y TASK_018 completadas

---

## TASK_016 — Conversor splines + server crash ✓ COMPLETADA

Reporte completo en `coordination/reports/PUNTO_TASK_016_REPORT.md`.

**Resumen:**
- Thumbnail de "Philo (convertido)" corregido: la causa era que `piece.bbox()` del motor legacy usa `center ± radius` para arcos (como si fueran círculos completos), lo que hacía que el modo centrado siempre fallara para Philo. Solución: nueva función `_render_dxf_thumbnail()` que renderiza el DXF directamente con ezdxf + matplotlib, sin pasar por el motor de tiling.
- Server crash: no se encontró `sys.exit()` ni excepción descubierta. La hipótesis más probable es que `Path("//190.190.190.9/...").exists()` al arrancar bloqueó el hilo durante 30-60s. Mitigación: `do_GET` y `do_POST` ahora tienen try/except externo que captura cualquier excepción y responde 500 en lugar de matar el proceso.
- Todos los cambios de Nova validados y mantenidos (5/5 correctos).
- Fix de SyntaxWarning Python 3.14: `\s` en regex JS dentro de f-strings.

---

## TASK_018 — Resultado y presupuestos ✓ COMPLETADA

Reporte completo en `coordination/reports/PUNTO_TASK_018_REPORT.md`.

**Resumen:**
- `/presupuesto`: botón "⬇ Descargar DXF" (si el path está disponible) + campo "Cliente" editable con auto-save (blur + debounce 1500ms).
- `/presupuestos`: nueva página con lista de todos los `PRES_NNNN.json`, ordenados de nuevo a viejo, con columnas N°/Fecha/Cliente/Total/Ver/Borrar.
- 4 endpoints nuevos: `GET /presupuestos`, `GET /download_dxf`, `POST /api/presupuestos/:id/cliente`, `DELETE /api/presupuestos/:id`.
- Topbar actualizado: el link "Presupuestos" apunta a `/presupuestos` (plural).
- 3 tests nuevos. Suite total: 31 tests pasan.

---

**Estado actual:** sin tareas pendientes. Esperando nuevas instrucciones.
