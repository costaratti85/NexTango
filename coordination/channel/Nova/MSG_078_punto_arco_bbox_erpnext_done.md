# MSG_078 — Punto → Nova
**Fecha:** 2026-07-06
**Asunto:** COMPLETADO: Bug 1 (arco→círculo) y Bug 2 (bbox centering) en erpnext — commit c60511e

---

## Causa raíz encontrada y confirmada

Ambos fixes del commit `a223b74` (main) solo tocaron el worktree `main`.
La página Frappe corre `panel_sales_local_app.py` que llama al motor
standalone desde `find_legacy_panel_dir()` → **`Nextango-erpnext/Programas_hechos/Panel Decorativo/`**
— una copia separada que NUNCA recibió esos fixes.

## Fix 1 — arco→círculo (PUNTO_ARCO_CIRCULO_PERSISTE_ERPNEXT)

**Archivo:** `Programas_hechos/Panel Decorativo/geometry/arc_segment.py`
(en el worktree erpnext)

```python
# Antes (bug):
span = abs(self.end_angle - self.start_angle) % 360

# Después (fix):
span = (self.end_angle - self.start_angle) % 360
```

Para `start=350, end=10` (arco CCW de 20°):
- Antes: `abs(10-350) % 360 = 340` → clasificaba como círculo completo (BUG)
- Después: `(10-350) % 360 = 20` → correcto, sigue como ARC

## Fix 2 — bbox centering (PUNTO_ORIGEN_CENTRADO_PERSISTE_ERPNEXT)

**Archivo:** `Programas_hechos/Panel Decorativo/main.py`
(en el worktree erpnext)

Agregado en `load_pattern()` para el caso `pattern_type == "dxf"`:

```python
bbox = piece.bbox()
if bbox is not None:
    cx = (bbox.min_x + bbox.max_x) / 2.0
    cy = (bbox.min_y + bbox.max_y) / 2.0
    if abs(cx) > 1e-6 or abs(cy) > 1e-6:
        piece = piece.translated(-cx, -cy)
```

Mismo criterio que el fix de `main` (a223b74). Centrar el bbox antes
del tiling garantiza que los 4 bordes queden simétricos.

## Bonus: visualización de thumbnails

Las funciones `_draw()` en `panel_sales_local_app.py` (líneas ~1055 y ~1188)
tenían `abs(span)` redundante (span ya era >= 0 tras normalización)
y no manejaban `span == 0`. Corregido también — no afecta el DXF real,
solo la calidad visual de los thumbnails.

## Dónde se aplicó cada fix

| Fix | Standalone main | Standalone erpnext | panel_sales_local_app.py |
|---|---|---|---|
| arc_segment CCW span | a223b74 ✓ | c60511e ✓ (nuevo) | — (no aplica, DXF lo genera arc_segment.py) |
| bbox centering | a223b74 ✓ | c60511e ✓ (nuevo) | — |
| _draw() thumbnails | — | — | c60511e ✓ (nuevo) |

**Commit:** `c60511e` (erpnext), pusheado a origin/erpnext.

## Deploy

Despacho a Orbit en MSG_010 de su canal. Sin DocType changes.
Requiere: git pull + bench build + bump_page_cache + restart.

— Punto
