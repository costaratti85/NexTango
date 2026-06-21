# PUNTO_TASK_024_REPORT — Cierre de borde: bug persiste post TASK_023

**Agente:** Punto  
**Fecha:** 2026-06-18  
**Estado:** COMPLETADO

---

## Causa raíz real

TASK_023 corrigió `boundary_path()` (corner routing → 1 línea directa). El bug persistía por una causa **completamente distinta y más profunda**: el merge del `PolylineClipper` nunca se activaba.

### Por qué no se activaba el merge

El `PolylineClipper.clip_polyline()` tiene un mecanismo de merge para contornos cerrados: cuando el punto inicial/final del contorno queda en el borde del clip rect, el clipper une el último y primer fragmento en uno solo, produciendo un cierre correcto de borde-a-borde.

La condición de merge requiere `is_closed(polyline) = True`. Pero para el Philo convertido (splines→arcos), la figura tiene un **gap de ~0.0002mm** entre el primer y último punto del contorno stitcheado:

```
points[0] = (44.22073318979164, 54.76103256409036)
points[-1] = (44.22065900277153, 54.76122719898035)
```

`is_closed()` usaba `EPSILON = 1e-6`. El gap de ~2e-4 → **is_closed devolvía False** → merge nunca se activaba.

### Efecto del merge no activado

Con 2 fragmentos separados:
- **Fragmento 0**: `[P0_first=(44.22, 54.76), ..., (15.0, 39.243)]`  
  → cierre: `(15.0, 39.243) → P0_first` = línea de 41mm del borde al interior ← **INCORRECTO**
- **Fragmento 1**: `[(15.0, 33.956), ..., P0_last=(44.22, 54.76)]`  
  → cierre: `P0_last → (15.0, 33.956)` = línea del interior al borde ← **INCORRECTO**

El usuario veía en el margen izquierdo: la línea de LINE entity del DXF terminando en (15.0, 39.243) + el cierre diagonal de 41mm al interior → **"2 vectores en un nodo existente"**.

Con el merge correcto:
- **Merged**: `[(15.0, 33.956), ..., P0_last, P0_first, ..., (15.0, 39.243)]`  
  → cierre: `(15.0, 39.243) → (15.0, 33.956)` = línea corta de 5.3mm en el borde izquierdo ← **CORRECTO**

---

## Fix aplicado

**Archivo:** `Programas_hechos/Panel Decorativo/geometry/polyline_clipper.py`

```python
# Antes:
def is_closed(polyline):
    if len(polyline.points) < 3:
        return False
    return points_close(polyline.points[0], polyline.points[-1])
    # EPSILON = 1e-6 → gap de 0.0002mm fallaba el test

# Después:
_CLOSE_THRESHOLD = 0.01  # tolera gaps de conversión spline→arcos (<10 micrones)

def is_closed(polyline):
    if len(polyline.points) < 3:
        return False
    p0 = polyline.points[0]
    pl = polyline.points[-1]
    return (
        abs(p0[0] - pl[0]) <= _CLOSE_THRESHOLD
        and abs(p0[1] - pl[1]) <= _CLOSE_THRESHOLD
    )
```

---

## Verificación cuantitativa

Philo 300×300mm, margen 15mm:

| Métrica | Antes del fix | Después del fix |
|---|---|---|
| Figuras de salida | 112 | 108 (-4 por merges correctos) |
| Cierres boundary→boundary | — | 43 |
| Cierres boundary→interior (>5mm) | varios | **0** |
| Tests pasando | 31 | **31** |

---

## Cadena de bugs resuelta

| Task | Causa | Fix |
|---|---|---|
| TASK_023 | `boundary_path()` insertaba esquina del clip rect como punto intermedio | `return [end]` siempre |
| **TASK_024** | `is_closed()` rechazaba contornos con gap <0.01mm → merge sin activar → cierre boundary→interior | Elevar threshold de `is_closed` a 0.01mm |

Ambas causas producían el mismo síntoma visual: 2 vectores en un nodo del margen.
