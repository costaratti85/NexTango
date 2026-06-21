# PUNTO_TASK_026_REPORT — Endpoints de línea de cierre desplazados

**Agente:** Punto  
**Fecha:** 2026-06-18  
**Estado:** COMPLETADO (con aclaración de Constantino incorporada)

---

## Causa raíz

El gap entre el arco recortado y la línea de cierre surgía de una inconsistencia entre dos sistemas de coordenadas:

### Paso 1 — Discretizer produce puntos sobre el círculo

```
(cx + cos(a) * r, cy + sin(a) * r)
```
Estos puntos están matemáticamente sobre la circunferencia.

### Paso 2 — PolylineClipper clipea chords, no arcos

El Cohen-Sutherland clipea el segmento recto (chord) entre dos puntos discretizados consecutivos. El punto de intersección con el borde del clip rect **NO está sobre la circunferencia** — es una interpolación lineal en el chord.

```
Ejemplo medido:
  Punto clipeado (chord-boundary): (15.00000000, 43.22489260)
  Radio desde centro: sqrt((15-30)² + (43.22-30)²) ≠ 20.0  → off-circle
```

### Paso 3 — ArcRebuilder mapea ese punto de vuelta al círculo

```python
a2 = angle_from_point(cx, cy, p_clipped)
arc_endpt = (cx + cos(a2)*r, cy + sin(a2)*r)  # ON the circle
```

**Gap resultante: ~2.5 micrones** — pequeño pero visible en el visor DXF como entidades desconectadas.

---

## Aclaración de Constantino (incorporada al fix)

El cierre de figuras clipeadas tiene dos variantes válidas:

| Caso | Trigger | Cierre |
|---|---|---|
| **Normal** | Ambos nodos libres en el mismo margen (ej: ambos en LEFT) | 1 línea directa A → B |
| **Esquina** | Un nodo en margen vertical, el otro en margen horizontal | 2 líneas: cada una al vértice de la esquina — A → corner, corner → B |

La variante esquina estuvo rota en dos momentos:
- **Pre-TASK_023**: se activaba incorrectamente cuando ambos nodos estaban en el MISMO margen
- **Post-TASK_023**: se eliminó por completo (always `return [end]`), rompiendo el caso legítimo

---

## Fix aplicado

### Archivo 1: `polyline_closer.py` — `boundary_path()`

Restaura la lógica de corner routing pero SOLO para nodos en márgenes de orientación diferente:

```python
def boundary_path(self, start, end):
    side_start = self.point_side(start)
    side_end = self.point_side(end)
    corner = self.corner_between(side_start, side_end)
    if corner is not None:
        return [corner, end]
    return [end]
```

`corner_between(LEFT, LEFT) = None` → 1 línea directa (same margin)  
`corner_between(LEFT, BOTTOM) = (xmin, ymin)` → 2 líneas por esquina (cross margin)

### Archivo 2: `arc_rebuilder.py` — `rebuild_polyline()`

Detecta el grupo completo de segmentos de cierre al final (1 o 2) y reconstruye con endpoints corregidos. Los puntos intermedios (el corner) se pasan tal cual — son vértices exactos del clip rect, no interpolaciones de chord:

```python
# Detectar todos los segmentos "closing" al final
closing_start_idx = len(metas)
while closing_start_idx > 0 and metas[closing_start_idx-1].get("source_type") == "closing":
    closing_start_idx -= 1

# ... procesar segmentos no-closing ...

if has_closing and fig.entities:
    p_first = fig.entities[-1].end_point()   # endpoint real del último arco
    p_last  = fig.entities[0].start_point()  # startpoint real del primer arco
    intermediate = points[closing_start_idx + 1 : len(metas)]  # corner si existe
    current = p_first
    for pt in intermediate:
        add_line(fig, current, pt)
        current = pt
    add_line(fig, current, p_last)
```

---

## Verificación cuantitativa

```
Gap ANTES del fix:  2.5556 micrones
Gap DESPUÉS del fix: 0.0000 mm (exacto)
```

**Caso normal (mismo margen):**
```
Figure 0 (2 entities): max_gap = 0.0000000000 mm
  [0] ArcSegment:  (30.0, 50.0)       -> (14.9981, 43.2266)
  [1] LineSegment: (14.9981, 43.2266) -> (30.0, 50.0)      ← coincide exacto
```

**Caso esquina (LEFT + BOTTOM):**
```
Figure 1 (3 entities): max_gap = 0.0000000000 mm
  [0] ArcSegment:  (14.9995, 16.7719) -> (16.7719, 14.9995)
  [1] LineSegment: (16.7719, 14.9995) -> (15.0, 15.0)       ← arco → corner
  [2] LineSegment: (15.0, 15.0)       -> (14.9995, 16.7719)  ← corner → arco
```

51 tests pasan. Los 10 errores son pre-existentes (PermissionError de pytest `tmp_path` en Windows).

---

## Cadena de bugs resuelta

| Task | Causa | Fix |
|---|---|---|
| TASK_023 | `boundary_path()` insertaba esquina para nodos en el MISMO margen | `return [end]` siempre (overcorrección) |
| TASK_024 | `is_closed()` rechazaba contornos con gap <0.01mm → merge no activado | Threshold 1e-6 → 0.01mm |
| **TASK_026** | Clipper clipea chords; ArcRebuilder mapea endpoints al círculo; closing usaba punto chord-boundary (mismatch) + boundary_path overcorregido | Closing toma endpoints de entidades reconstruidas; boundary_path restaura corner routing para márgenes cruzados |
