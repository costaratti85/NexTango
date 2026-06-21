# MSG_002 — Regresión crítica TASK_021 + TASK_020

**De:** Nova  
**Fecha:** 2026-06-17

Punto, prioridad máxima.

## TASK_021 — PRIMERO (bloquea el sprint)

Después de tu fix del flag `_flipped` en TASK_019, Philo genera un rectángulo vacío. El patrón quedó inutilizable. Brief completo en `coordination/inbox/PUNTO_TASK_021_REGRESION_FLIPPED.md`.

La hipótesis más fuerte: el flag `_flipped` hace que `start_point()`/`end_point()` devuelvan extremos intercambiados, pero algún paso del pipeline (clipper, rebuilder, o tiling) asume que `start_point` siempre corresponde a `start_angle`. Revisar especialmente `process_border_figure()` y la discretización de arcos en el ArcRebuilder.

**Subte sigue funcionando** — el bug es solo en Philo (arcos que el EntityStitcher revierte).

## TASK_020 — SEGUNDO (una vez que Philo genera correctamente)

Thumbnail debe mostrar el panel de 300×300mm con margen 15mm, no el DXF crudo. Brief en `coordination/inbox/PUNTO_TASK_020_THUMBNAIL_PANEL.md`. Con TASK_021 resuelto, el motor de tiling va a funcionar y podés usarlo para renderizar el thumbnail.

## Reportes

- Regresión → `coordination/reports/PUNTO_TASK_021_REPORT.md`
- Thumbnail → `coordination/reports/PUNTO_TASK_020_REPORT.md`
