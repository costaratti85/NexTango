# PUNTO_TASK_021_REPORT — Regresión: panel Philo vacío después de TASK_019

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-17  
**Estado:** Completada

---

## Diagnóstico

### Causa raíz: `Discretizer.discretize_arc()` ignoraba `_flipped`

El fix de TASK_019 introdujo el flag `_flipped` en `ArcSegment.reversed()`. El flag cambia qué puntos devuelven `start_point()`/`end_point()` (para que el `EntityStitcher` conecte correctamente), pero no toca `start_angle`/`end_angle` (para que `export_dxf()` dibuje el arco correcto).

El problema: **`Discretizer.discretize_arc()` usaba `arc.start_angle`/`arc.end_angle` directamente**, sin consultar `_flipped`. Para un arco flipped (start_angle=A, end_angle=B, _flipped=True):

- `start_point()` devuelve `point_at(B)` — el EntityStitcher conecta el segmento ANTERIOR al punto B
- `end_point()` devuelve `point_at(A)` — el EntityStitcher conecta el segmento SIGUIENTE al punto A
- `discretize_arc()` generaba puntos de A→B (orden CCW, ignorando _flipped)

Resultado: la polilínea del arco empezaba en `point_at(A)` pero el segmento anterior terminaba en `point_at(B)`. Los puntos de empalme no coincidían. El `PolylineStitcher` producía contornos mal encadenados o degenerados, que al clippearse producían cero segmentos de salida.

### Por qué el panel quedaba completamente vacío

Philo tiene step_x=360mm, step_y=623mm. En un panel 300×300mm con margen 15mm (área útil 270×270mm), solo aparece un tile (`col=0, row=0`). Ese tile siempre es "border" (el motivo Filo excede el área útil). Si `process_border_figure()` devuelve 0 entidades para TODOS sus sub-figuras, el panel queda solo con el rectángulo de contorno → "rectángulo vacío".

### Por qué no afectaba a Tresbolillo ni Subte

- **Tresbolillo**: generado programáticamente — el EntityStitcher nunca llama `.reversed()`
- **Subte**: step_x=84mm, paso pequeño → muchos tiles interiores. Los tiles interiores usan el Figure directamente (sin discretizar ni clipear), por lo que `_flipped` nunca toca el Discretizer. Solo los tiles border fallan, pero representan una minoría visible.

---

## Solución

**Un cambio mínimo en `Discretizer.discretize_arc()`** (`geometry/discretizer.py`):

Después de generar la lista de puntos en orden CCW (A→B), si `arc._flipped` es True, se **reversa la lista** antes de agregar los segmentos a la polilínea. La polilínea pasa a ir de B→A (orden CW), lo que coincide exactamente con lo que el `EntityStitcher` espera:

```python
if getattr(arc, "_flipped", False):
    points.reverse()
```

### Por qué el ArcRebuilder sigue funcionando correctamente

El `ArcRebuilder.add_arc()` recibe puntos en orden B→A (CW), detecta dirección CW por el producto cruzado (o por proximidad angular en el caso de 2 puntos), y produce `ArcSegment(cx, cy, r, start_angle, end_angle)` = el arco original correcto. ✓

### El fix de TASK_019 sigue intacto

`export_dxf()` nunca usa `_flipped` — usa `start_angle`/`end_angle` directamente. Los arcos continúan exportándose con sus ángulos originales, sin el bug de arco complementario. ✓

---

## Resultados de verificación

| Métrica | Antes del fix (con TASK_019) | Después del fix |
|---|---|---|
| Figuras con contorno en clip rect | 109 | 109 |
| De esas, producen entidades | ~0 (panel vacío) | **107** |
| Items de geometría en panel 300×300mm | 1 (solo contorno) | **112** |
| Total entidades en tiles | 0 | **829** |
| Arcos complementarios (span>180°, radio>5mm) | 0 (vacío) | **0** ✓ |

---

## Tests

- 31 tests de `test_panel_sales_local_app.py` pasan ✓
- 4 ERRORs pre-existentes por `tmp_path` en Windows (sin relación)

---

## Criterios de aceptación

1. ✅ Panel con Philo genera arcos visibles y en la dirección correcta
2. ✅ Panel con Subte sigue funcionando (tests pasan)
3. ✅ Tests existentes pasan
4. ✅ Reporte en `coordination/reports/PUNTO_TASK_021_REPORT.md`

---

## Archivos modificados

| Archivo | Cambio |
|---|---|
| `Programas_hechos/Panel Decorativo/geometry/discretizer.py` | `discretize_arc()`: si `arc._flipped`, reversa la lista de puntos antes de armar los segmentos |

**Nota**: `arc_segment.py` y `arc_rebuilder.py` (modificados en TASK_019) NO requieren cambios adicionales.
