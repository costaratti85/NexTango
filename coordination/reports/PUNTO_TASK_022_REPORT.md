# PUNTO_TASK_022_REPORT — Conversor splines: eliminar arcos espurios en esquinas

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-17  
**Estado:** Completada

---

## Causa raíz confirmada

El sliding window de fitting en `discretize_and_convert_spline()` no tenía conocimiento de discontinuidades de tangente. En una esquina (ángulo entre cuerdas consecutivas > umbral), puntos a ambos lados caen casualmente sobre un mismo círculo → `fit_arc_to_points()` los acepta → arco espurio que cruza la esquina.

---

## Solución implementada

### Función nueva: `_find_corner_indices(points, corner_threshold_deg=20.0)`

Definida antes de `discretize_and_convert_spline()` en [`tools/dxf_spline_to_arcs.py`](tools/dxf_spline_to_arcs.py). Recorre los puntos discretizados y detecta como "esquina" cualquier índice donde el ángulo entre la cuerda entrante y la saliente supera el umbral:

```
cos_a = dot(chord_in, chord_out) / (|chord_in| · |chord_out|)
angle = acos(cos_a)
if angle > corner_threshold_deg → esquina
```

Umbral elegido: **20°** (el propuesto en el brief). Ángulos menores quedan dentro de la tolerancia normal del arc fitter.

### Cambio en el loop de fitting

Dos líneas antes del while, y una modificación en el `for end`:

```python
corners = _find_corner_indices(points)
sorted_corners = sorted(corners)

# ... dentro del while:
idx = bisect.bisect_right(sorted_corners, i)
corner_limit = sorted_corners[idx] if idx < len(sorted_corners) else len(points)

for end in range(i + 2, min(i + 50, corner_limit, len(points))):
    ...
```

`bisect_right` encuentra en O(log n) el primer corner index > i. La ventana nunca pasa de `corner_limit - 1`, por lo que ningún segmento cruza una esquina.

Cuando la ventana queda vacía (corner inmediatamente adyacente), `best_result = None` y el loop emite una LINE al punto siguiente, avanzando naturalmente hasta pasar la esquina.

---

## Tests funcionales

| Test | Resultado |
|---|---|
| L-shape 90° (esquina en índice 5) | Corner detectado en {5} ✓ |
| Semicírculo suave (180°) | 0 corners detectados ✓ |
| Curva suave 10°/punto | 0 corners detectados ✓ |
| Ventana nunca cruza índice 5 en L-shape | Verificado ✓ |

Todos los tests de regresión existentes: **31 pasan** ✓

---

## Criterios de aceptación

1. ✅ DXF con esquinas explícitas: los arcos terminan antes del corner, no lo cruzan
2. ✅ Splines continuas (Philo, Subte): comportamiento idéntico al anterior (0 corners detectados para curvas suaves)
3. ✅ No se cambia la interfaz gráfica ni los tests de integración
4. ✅ Reporte en `coordination/reports/PUNTO_TASK_022_REPORT.md`

### Umbral elegido: 20°

- Falso positivo (curva suave marcada como corner): no observado con 20° en tests
- Si aparecen en producción, subir a 30°
- Si arcos espurios subsisten con esquinas leves, bajar a 10°

---

## Archivos modificados

| Archivo | Cambio |
|---|---|
| `tools/dxf_spline_to_arcs.py` | `import bisect` agregado; función `_find_corner_indices()` nueva (línea 104); loop de fitting usa `corner_limit` (bisect sobre `sorted_corners`) |
