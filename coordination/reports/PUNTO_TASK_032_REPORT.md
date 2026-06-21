# PUNTO_TASK_032 — Soporte LWPOLYLINE en validador e importer

**Fecha:** 2026-06-19  
**Estado:** Completada

---

## Cambios realizados

### 1. `apps/sistema_industrial/sistema_industrial/presets/dxf_validator.py`

```python
# Antes:
SUPPORTED_TYPES = {"LINE", "ARC", "CIRCLE"}

# Después:
SUPPORTED_TYPES = {"LINE", "ARC", "CIRCLE", "LWPOLYLINE"}
```

**Nota técnica:** No se necesitó verificación de flags de spline/mesh porque `LWPOLYLINE` no puede tener esos flags — son exclusivos de `POLYLINE` heavyweight. Todos los `LWPOLYLINE` son explotables de forma exacta. `POLYLINE` heavyweight sigue sin soportar (queda en modo restringido).

---

### 2. `Programas_hechos/Panel Decorativo/dxf/importer.py`

Se agregó:
- `import math` en el módulo
- Función `_bulge_to_arc(x1, y1, x2, y2, bulge)` — convierte un segmento de LWPOLYLINE con bulge en `(cx, cy, radius, start_angle, end_angle, is_cw)`
- Branch `elif dxftype == "LWPOLYLINE":` en `DXFImporter.load()`

La función `_bulge_to_arc` usa la misma fórmula matemática que `dxf_spline_to_arcs.process_lwpolyline()` (la que ya estaba validada y funcionando en el conversor), adaptada para devolver objetos internos en vez de entidades DXF:

```python
radius = abs(chord / (2 * sin(2 * atan(bulge))))
sagitta = radius * cos(2 * atan(bulge))
center = midpoint + perp * sagitta
```

Para arcos CW (`bulge < 0`): se almacenan con `start_angle, end_angle` intercambiados y `seg._flipped = True`, consistente con `arc_rebuilder.add_arc()`.

El branch de LWPOLYLINE:
- Usa `entity.get_points(format='xyseb')` para leer `(x, y, sw, ew, bulge)` por vértice
- Itera los `n-1` segmentos normales + el de cierre si `is_closed=True`
- `bulge ≈ 0` → `LineSegment`; `bulge != 0` → `ArcSegment` (con `_flipped` si CW)

---

## Verificación

### Test 1 — Validator: LWPOLYLINE aceptado
DXF con 3 `LWPOLYLINE` (cuadrado cerrado, círculo de 4 arcos, trazo mixto) → `validate_dxf_entities` no lanzó excepción → modo completo ✓

### Test 2 — Importer: segmentos correctos
- 3 LWPOLYLINE → 6 `LineSegments` + 5 `ArcSegments` (conteos esperados) ✓
- Cuadrado: 4 LineSegments con start/end en los vértices correctos ✓
- Círculo de 4 arcos: conectividad perfecta (gap = 0.000000 mm en los 4 pares) ✓
- Trazo mixto: el arco con bulge=0.5 produjo `start=(30,30) end=(60,30)` correcto ✓

### Test 3 — Pipeline completo con el motor
DXF con LWPOLYLINE como patrón, 400×400mm, step 120×150mm, margen 20mm, `cut_partial_figures=True`:
```
FIGURAS DETECTADAS: 2
Motor output: result_items=1, arranged=33
Output DXF: LINE:74, ARC:39, LWPOLYLINE:1 (contorno), TEXT:2
```
El patrón se tiló correctamente → no es un rectángulo vacío ✓

### Test 4 — POLYLINE heavyweight: sin cambios
`POLYLINE` no está en `SUPPORTED_TYPES` → sigue en modo restringido ✓

---

## Efecto en el pipeline de G-code

Sin impacto. La conversión LWPOLYLINE→ArcSegment/LineSegment ocurre dentro del importer (memoria interna). El output del motor (`MixedDXFExporter`) produce ARC+LINE+LWPOLYLINE exactamente igual que antes.
