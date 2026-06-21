# MSG_004_PUNTO_response

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-17  
**Re:** TASK_020 completada — Thumbnails de panel 300×300mm

---

## Resumen

TASK_020 completada. Los thumbnails de patrones DXF ahora muestran el panel tileado de 300×300mm con margen 15mm en lugar del patrón crudo.

## Qué cambió

Agregué `_render_panel_thumbnail()` en `panel_sales_local_app.py` — usa el motor legacy en cut mode (igual que Tresbolillo ya hacía) con `sheet_sizes=[(300.0, 300.0, 1)]` y `margin=15.0`. `generate_pattern_thumbnail()` lo llama primero para patrones DXF; si el motor falla, hace fallback al render directo del DXF.

Borré los 6 thumbnails cacheados (Philo, Philo_convertido, Subte, Subte_3, Subte4, subte_2) para que se regeneren en el próximo start.

31 tests pasan.

## Estado de tareas

- TASK_019 — Arcos invertidos Philo: ✅ completada
- TASK_020 — Thumbnails panel 300×300mm: ✅ completada

Reporte completo: `coordination/reports/PUNTO_TASK_020_REPORT.md`

---

**Sin tareas pendientes. Esperando próximas instrucciones.**
