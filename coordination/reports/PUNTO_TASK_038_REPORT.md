# PUNTO_TASK_038 — Bug centrado grilla Subte

**Fecha:** 2026-06-20  
**Estado:** Completada (v2 — fix definitivo)

---

## Causa raíz (v1 — TASK_038 inicial)

En `generate_centered_full_mode_geometry` (`main.py`), el cálculo del "ancho ocupado" usaba `(cols - 1) * step_x` en lugar de `cols * step_x` — introducido en TASK_035.

Fix aplicado: `occupied_width = cols * step_x`. Esto fue NECESARIO pero INSUFICIENTE.

---

## Causa raíz v2 — fix definitivo (seguimiento Constantino)

Después del fix v1, Constantino reportó que el centrado seguía mal después del reinicio del servidor.

**Diagnóstico del DXF de red:**
```
Archivo: //190.190.190.9/.../subte Offx84 Offy84.dxf
bbox.min_x = -26.18 mm   <- contenido 26mm a la IZQUIERDA del origen
bbox.max_x = +66.66 mm
bbox.width =  92.84 mm   (> step_x=84 — el tile es más ancho que su paso)
```

El archivo subido localmente (`outputs/.../subte.dxf`) tiene `bbox.min_x ≈ 0` (normalizado), pero el motor usa `pattern_dxf_path` del batch, que apunta al archivo de red.

Con fix v1 (`start_x = 25.5mm` para 555×444):
- Borde visual izquierdo: `25.5 + (-26.18) = -0.68mm` → **fuera del panel**
- Borde visual derecho: `512.16mm` (gap 22.84mm)
- Completamente asimétrico — por eso Constantino lo veía "descentrado"

**Fórmula correcta:** centrar el **extent visual completo**, no los orígenes de la grilla:

```python
visual_width  = (cols - 1) * step_x + piece_w   # extent real del contenido
visual_height = (rows - 1) * step_y + piece_h
start_x = margin + (usable_width  - visual_width)  / 2 - bbox.min_x
start_y = margin + (usable_height - visual_height) / 2 - bbox.min_y
```

El término `-bbox.min_x` compensa el desplazamiento del origen del DXF.

## Fix final

`Programas_hechos/Panel Decorativo/main.py` — `generate_centered_full_mode_geometry`:

```python
bbox = original_piece.bbox()
piece_w = bbox.max_x - bbox.min_x
piece_h = bbox.max_y - bbox.min_y

cols = int(usable_width / step_x)
rows = int(usable_height / step_y)

while cols > 0 and (cols - 1) * step_x + piece_w > usable_width:
    cols -= 1
while rows > 0 and (rows - 1) * step_y + piece_h > usable_height:
    rows -= 1

if cols == 0 or rows == 0:
    return output_items

visual_width  = (cols - 1) * step_x + piece_w
visual_height = (rows - 1) * step_y + piece_h
start_x = margin + (usable_width  - visual_width)  / 2 - bbox.min_x
start_y = margin + (usable_height - visual_height) / 2 - bbox.min_y
```

## Resultado verificado con DXF real de red

| Panel | Gap izq | Gap der | Gap inf | Gap sup | Simétrico |
|---|---|---|---|---|---|
| 555×444 | 1.08mm | 1.08mm | 40.60mm | 40.60mm | ✓ |
| 555×999 | 1.08mm | 1.08mm | 24.10mm | 24.10mm | ✓ |

## Funciones no afectadas

`generate_cut_mode_geometry` (Philo, `cut_partial=True`) — sin centering por diseño. No afectada.

## Tests

- `test_centered_full_mode_grid_centering_subte_params` actualizado: usa piece con `bbox.min_x=-26.18` (simula DXF real) y verifica simetría de gaps
- 37 tests pasan, 4 errores pre-existentes (permisos Windows temp, no relacionados)
