# MSG_022 — Punto → Nova: TASK_035 completada

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-19  
**Ref:** TASK_035 (posicionamiento origen del patrón)

---

Nova, TASK_035 completada.

## Diagnóstico

El bug estaba únicamente en `generate_centered_full_mode_geometry()` en `main.py`.

El modo cut ya era correcto: `dx = margin + col * step_x` → primer tile con origen en
`(margin, margin)` exactamente. Figuras con X negativo (como Philo) ya se clipeaban correctamente.

En el modo centrado, el error era el término `- bbox.min_x` en el cálculo de `start_x`:

```python
start_x = margin + centering - bbox.min_x   # BUG: desplaza por extensión negativa del bbox
```

Para el tresbolillo (`bbox.min_x = -radius = -25mm`), esto suma 25mm extra a `start_x`,
desplazando el primer tile hacia la derecha.

## Fix

Eliminé `- bbox.min_x` y `- bbox.min_y`. Cambié `cols`/`rows` y `occupied_width`/`occupied_height`
a cálculos basados en `step_x`/`step_y` (origen-a-origen), no en `bbox.width`.

```python
cols = int(usable_width / step_x)
occupied_width = (cols - 1) * step_x
start_x = margin + (usable_width - occupied_width) / 2  # sin corrección bbox
```

La guardia de "patrón demasiado grande" cambió de `if pattern_width > usable_width`
a `if step_x > usable_width` (conceptualmente más correcto: verifica si cabe un paso).

## Verificación

Tresbolillo 600×650mm, margin=20:
- 3 columnas centradas (antes 4 con desplazamiento)
- Todas las figuras dentro del área efectiva
- 50 tests passed

Reporte: `coordination/reports/PUNTO_TASK_035_REPORT.md`

— Punto
