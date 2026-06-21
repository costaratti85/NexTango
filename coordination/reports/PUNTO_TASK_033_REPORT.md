# PUNTO_TASK_033 — Arco complementario aislado en panel Philo

**Fecha:** 2026-06-19  
**Estado:** Completada

---

## Bug encontrado

Panel Philo 600×650mm generaba un arco con span=**356.12°** en lugar de 3.88°.

- center=(312.57, 605.75), r=73.288
- DXF emitido: start=196.57°, end=192.69° → CCW = 356.12°
- Correcto: start=196.57°, end=199.74° → CCW = 3.17°

---

## Causa raíz

**`PolylineClipper.clip_polyline()` — desincronización de sources por gap entre puntos de clip.**

La figura de Philo contiene un contorno cerrado de 6 entidades. Al clippearlo en el borde superior (y_max=630mm), se generan dos puntos de clip distintos:

- `clip_pt1 = (248.731, 630.0)` → fin del segmento LINE clipeado (inside→outside)
- `clip_pt2 = (247.433, 630.0)` → inicio del segmento ARC clipeado (outside→inside)

El clipper NO ponía `current=None` entre ambos recortes (el fragmento activo persistía). Llamaba:
```python
current.add_segment(clip_pt2.x, clip_pt2.y, ...)
```
con `current.points[-1] = clip_pt1 ≠ clip_pt2`.

`Polyline.add_segment()` insertaba `clip_pt2` como punto extra **sin agregar source correspondiente**. Resultado:

| Posición | Points | segment_sources (esperado) | segment_sources (real) |
|----------|--------|---------------------------|------------------------|
| [12] | arc[2]@190.966° | arc[2] | **BAD_ARC** ← shifted |
| [13] | arc[2]@195.669° | BAD_ARC | LINE |

`ArcRebuilder.add_arc()` recibió:
- `p_start` = (241.177, 589.681) — ángulo 192.69° desde centro del arco malo
- `p_end`   = (242.318, 584.858) — ángulo 196.57° (el start_angle real del arco)

Con `src_start = 196.57°`: `_angle_distance(192.69, 196.57) = 3.88 > 0 = _angle_distance(196.57, 196.57)` → dirección="cw" → `ArcSegment(196.57, 192.69)` con `_flipped=True` → export DXF: start=196.57, end=192.69, span=356.12°.

---

## Fix

**`Programas_hechos/Panel Decorativo/geometry/polyline_clipper.py`**

En `clip_polyline()`, antes de `add_segment()`, detectar el gap entre el último punto del fragmento actual y el inicio del nuevo segmento recortado. Si hay gap → cerrar el fragmento actual y abrir uno nuevo:

```python
elif not points_close(current.points[-1], (clipped.x1, clipped.y1)):
    if len(current.points) >= 2:
        result.append(current)
    current = Polyline()
```

Con el fix, el clipper produce correctamente dos fragmentos (A y B), el merge de polilínea cerrada los ensambla, y `add_arc()` recibe:
- `a1 = 196.565°` (start real del arco)
- `a2 = 199.739°` (end real del arco)
- direction = "ccw" → `ArcSegment(196.565, 199.739)` → 3.17° ✓

---

## Verificación

1. **Debug dirigido**: `add_arc` para el arco malo ahora recibe `a1=196.565, a2=199.739, dir=ccw` ✓
2. **Pipeline completo**: panel Philo 600×650 regenerado → `Total arcs: 1774`, `Arcs with span > 200: 0` ✓ (antes: 1 arco de 356.12°)

---

## Impacto

- Solo afecta figuras en borde que se clip en la geometría del panel.
- Los paneles "cortar en borde" (cut_partial_figures=True) son los únicos afectados.
- El fix es seguro: el gap detectado es un salto en el borde del panel, nunca un segmento interior legítimo.
