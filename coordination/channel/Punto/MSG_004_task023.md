# MSG_004 — TASK_023: cierre incorrecto de figuras de borde

**De:** Nova  
**Fecha:** 2026-06-18

Punto, bug nuevo reportado por Constantino en producción.

## TASK_023 — Figuras de borde: cierre con 2 líneas en vez de 1

Brief completo en `coordination/inbox/PUNTO_TASK_023_CLOSING_LINE.md`.

**El problema en una línea:** cuando una figura se corta sobre el margen y queda con dos nodos libres en el borde, debería cerrarse con UNA línea recta. En cambio, en algunos casos se cierra con DOS líneas pasando por un nodo intermedio (que coincide con un nodo existente del patrón).

**El código responsable:** `boundary_path()` en `Programas_hechos/Panel Decorativo/geometry/polyline_closer.py` (línea 66). Cuando los dos extremos caen en lados adyacentes del margen, la función inserta la esquina del rectángulo como punto intermedio.

**Fix probable:** simplificar `boundary_path` para que siempre devuelva una línea directa (`return [end]`). El brief tiene el detalle completo de qué verificar antes.

Reportar en `coordination/reports/PUNTO_TASK_023_REPORT.md`.
