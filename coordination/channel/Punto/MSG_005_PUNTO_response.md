# MSG_005_PUNTO_response

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-17  
**Re:** TASK_021 completada — Regresión panel Philo vacío

---

## Diagnóstico confirmado

La causa raíz era `Discretizer.discretize_arc()` — ignoraba el flag `_flipped` del fix de TASK_019.

Con `_flipped=True`, `start_point()` devuelve el punto en `end_angle` (para el stitcher). Pero el Discretizer seguía generando puntos de `start_angle` → `end_angle` (orden normal). Los puntos de empalme no coincidían, el PolylineStitcher producía contornos mal encadenados, y el clipper producía cero segmentos.

Para Philo esto era catastrófico: step_x=360mm, step_y=623mm → en un panel 300×300mm hay exactamente **un tile**, y ese tile es siempre "border" (usa `process_border_figure`). Si ese proceso devuelve vacío, el panel queda solo con el rectángulo.

## Fix

Un cambio mínimo en `discretizer.py`: después de generar los puntos CCW normales, si `arc._flipped` es True, se reversa la lista. La polilínea va de `end_angle` → `start_angle`, coincidiendo con lo que el PolylineStitcher espera. El ArcRebuilder ve dirección CW y reconstruye el arco original correcto.

## Resultados

- Panel Philo: **112 items, 829 entidades** (antes: 0, solo rectángulo)
- Arcos complementarios: **0** (fix de TASK_019 intacto)
- 31 tests pasan

Reporte completo: `coordination/reports/PUNTO_TASK_021_REPORT.md`

---

**TASK_019, TASK_020, TASK_021 completadas. Sin tareas pendientes.**
