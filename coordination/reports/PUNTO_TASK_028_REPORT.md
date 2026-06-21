# PUNTO_TASK_028_REPORT — Líneas de cierre fuera del margen

**Agente:** Punto  
**Fecha:** 2026-06-18  
**Estado:** COMPLETADO  
**Fuente de diagnóstico:** Constantino (observación directa del DXF de "philo")

---

## Síntoma reportado

Constantino verifica en el DXF del patrón **"philo"** que las líneas de cierre conectan el **segundo y el último** nodo (o el primero y el anteúltimo), en lugar del **primero y el último**. El patrón "subte" no tiene el problema.

---

## Causa raíz

### `add_arc()` en `arc_rebuilder.py`

Cuando un arco tiene dirección CW en el polyline, `add_arc()` crea `ArcSegment(cx, cy, r, a2, a1)` (ángulos invertidos para que el export DXF sea correcto). Pero sin `_flipped=True`, los métodos de conectividad devuelven los endpoints en **orden inverso al del polyline**:

```
Para un arc CW con a1=angle(points[0]), a2=angle(points[-1]):
  ArcSegment(cx, cy, r, a2, a1) con _flipped=False:
    start_point() = _point_at(a2) ≈ points[-1]   ← INCORRECTO
    end_point()   = _point_at(a1) ≈ points[0]    ← INCORRECTO
```

En `rebuild_polyline()`:
```python
p_last = fig.entities[0].start_point()  # ← tomaba points[-1] del primer grupo, no points[0]
```

La línea de cierre conectaba desde el endpoint correcto hasta el **punto equivocado** — un nodo interior del arco, no el nodo libre en el margen.

### Por qué "philo" y no "subte"

- **philo**: tiene arcos que el `Discretizer` puede invertir (dirección CW en el polyline) → bug activo
- **subte**: tiene solo líneas rectas → `add_arc()` nunca se llama → bug inactivo

### El flag `_flipped` ya existía para esto

El `ArcSegment._flipped` fue diseñado exactamente para este escenario (docstring: *"keeps start_point()/end_point() connectivity correct while export_dxf still draws the original arc"*). Solo faltaba usarlo en `add_arc()`.

---

## Fix aplicado

### `geometry/arc_rebuilder.py` — función `add_arc()`

```python
# Antes:
else:
    fig.add(ArcSegment(cx, cy, r, a2, a1))

# Después:
else:
    cw_arc = ArcSegment(cx, cy, r, a2, a1)
    cw_arc._flipped = True
    fig.add(cw_arc)
```

Resultado para CW arc:
| | Antes | Después |
|---|---|---|
| `start_point()` | `_point_at(a2)` ≈ `points[-1]` | `_point_at(a1)` ≈ `points[0]` ✓ |
| `end_point()` | `_point_at(a1)` ≈ `points[0]` | `_point_at(a2)` ≈ `points[-1]` ✓ |
| `export_dxf()` (start_angle) | `a2` (sin cambio) | `a2` (sin cambio) ✓ |

---

## Verificación

```
Caso CW: arco de 208.96° → 151.04° (dirección CW, puntos en el polyline de abajo-arriba):
  [0] ArcSegment: (15.0000,30.6351) -> (15.0000,69.3649)   ← p[0] a p[-1], correcto
  [1] LineSegment: (15.0000,69.3649) -> (15.0000,30.6351)  ← exactamente sobre el margen x=15

Gap máximo entre entidades: 0.0000000000 mm  ← figura cerrada perfectamente
```

49 tests pasan. Errores pre-existentes (PermissionError Windows) no cambian.

---

## Cadena de bugs (actualizada)

| Task | Causa | Fix |
|---|---|---|
| TASK_023 | `boundary_path()` insertaba esquina incorrectamente | `return [end]` siempre (overcorrección) |
| TASK_024 | `is_closed()` rechazaba contornos con gap <0.01mm | Threshold 1e-6 → 0.01mm |
| TASK_026 | Closing usaba chord-boundary en vez de arc endpoint | Closing toma endpoints de entidades reconstruidas |
| **TASK_028** | `add_arc()` no seteaba `_flipped=True` en arcos CW → endpoints invertidos | `cw_arc._flipped = True` en el branch CW de `add_arc()` |
