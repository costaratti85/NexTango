# MSG_006_PUNTO_response

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-17  
**Re:** TASK_022 completada — Arcos espurios en esquinas del conversor

---

## Resumen

TASK_022 completada. El conversor ya no genera arcos que cruzan esquinas.

## Qué cambié

**`tools/dxf_spline_to_arcs.py`**:

1. Nueva función `_find_corner_indices(points, corner_threshold_deg=20.0)`: recorre los puntos discretizados y marca como "esquina" cualquier índice donde el ángulo entre la cuerda entrante y la saliente supera el umbral (20°).

2. En el loop de fitting: antes de cada ventana, se calcula `corner_limit` (primer corner después del `i` actual, via bisect). El `for end` usa `min(i+50, corner_limit, len(points))` como cota superior → la ventana nunca cruza una discontinuidad de tangente.

Umbral elegido: **20°** (propuesto en el brief). Splines suaves como Philo y Subte producen 0 corners detectados (comportamiento idéntico al anterior).

## Tests

- `_find_corner_indices`: L-shape 90° detecta corner, semicírculo suave detecta 0
- Ventana con L-shape: nunca cruza índice 5 — verificado
- 31 tests de regresión pasan

Reporte: `coordination/reports/PUNTO_TASK_022_REPORT.md`

---

**TASK_019, TASK_020, TASK_021, TASK_022 completadas. Sin tareas pendientes.**
