# MSG_003 — TASK_022: mejora al conversor de splines

**De:** Nova  
**Fecha:** 2026-06-17

Punto, tarea nueva para el conversor de splines. **Esta va después de cerrar TASK_021 y TASK_020.**

## TASK_022 — Detectar esquinas en splines, no generar arcos espurios

Brief completo en `coordination/inbox/PUNTO_TASK_022_CORNER_KNOTS.md`.

**Resumen:** el conversor fitea arcos sin saber que algunos puntos son nodos de esquina (tangente discontinua). En esos puntos inventa arcos que cruzan la esquina. El fix es pre-detectar esquinas por ángulo entre cuerdas consecutivas, y limitar la ventana de fitting para que nunca cruce un nodo de esquina.

Prioridad media — no bloquea el sprint actual. Hacerlo cuando tengas TASK_021 y TASK_020 cerrados.

Reportar en `coordination/reports/PUNTO_TASK_022_REPORT.md`.
