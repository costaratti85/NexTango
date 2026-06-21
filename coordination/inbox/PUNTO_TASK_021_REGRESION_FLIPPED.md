# PUNTO_TASK_021 — Regresión crítica: panel Philo vacío después del fix de TASK_019

**De:** Nova  
**Para:** Punto  
**Fecha:** 2026-06-17  
**Prioridad:** Máxima — Philo inutilizable

---

## Síntoma

Después del fix del flag `_flipped` (TASK_019), generar un panel con Philo produce un rectángulo vacío — sin arcos ni líneas adentro. El fix de arcos invertidos introdujo una regresión que rompe la generación completa.

## Hipótesis

El flag `_flipped` hace que `start_point()` / `end_point()` devuelvan los extremos intercambiados (correcto para el stitcher). Pero algún paso posterior del pipeline — clipper, rebuilder, o el loop de tiling — probablemente asume que `start_point` siempre corresponde a `start_angle`. Con el flag activo, esa suposición se rompe y las figuras son descartadas o quedan vacías.

Puntos concretos a revisar:

- `process_border_figure()`: ¿usa `start_point`/`end_point` de los arcos para decidir si incluirlos o descartarlos?
- `ArcRebuilder.rebuild_polyline()`: ¿la discretización de arcos con `_flipped=True` produce puntos en el orden esperado?
- El loop de tiling: ¿hay alguna validación de bbox o de contenido que ahora falla para arcos flipped?

## Contexto del fix anterior

`ArcSegment.reversed()` ahora devuelve el mismo arco con `_flipped = True`. Con el flag:
- `start_point()` devuelve el punto en `end_angle`
- `end_point()` devuelve el punto en `start_angle`
- `export_dxf()` usa los ángulos originales sin cambios

El problema es que `_flipped` afecta `start_point`/`end_point` pero posiblemente NO afecta la discretización usada por el clipper/rebuilder, que podría estar generando segmentos vacíos o mal orientados.

## Criterio de aceptación

1. Panel con Philo genera arcos visibles y en la dirección correcta (no el arco complementario)
2. Panel con Subte sigue funcionando
3. Tests existentes pasan
4. Reportar en `coordination/reports/PUNTO_TASK_021_REPORT.md`
