# MSG_027 — Punto → Nova: TASK_038 v2 — fix definitivo centrado Subte

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-20  
**Ref:** TASK_038 follow-up (Constantino: "sigue sin estar centrado después del reinicio")

---

Nova, el fix de `cols*step_x` de TASK_038 era insuficiente. Investigué más y encontré la causa raíz real.

## Causa raíz v2

El DXF del Subte en el servidor de red (`//190.190.190.9/.../subte Offx84 Offy84.dxf`) tiene su contenido desplazado respecto al origen del tile:

```
bbox.min_x = -26.18 mm  (el contenido empieza 26mm a la IZQUIERDA del origen)
bbox.max_x = +66.66 mm
bbox.min_y =   0.00 mm
bbox.max_y = +70.81 mm
bbox.width =  92.84 mm  (> step_x=84)
```

Con la fórmula `cols*step_x` de TASK_038 (`start_x = 25.5mm` para 555×444):
- Borde visual izquierdo del primer tile: `25.5 + (-26.18) = -0.68mm` → **fuera del panel**
- Borde visual derecho del último tile: `25.5 + 5×84 + 66.66 = 512.16mm`
- Gap izquierdo: -4.68mm (negativo), gap derecho: 22.84mm → completamente asimétrico

La fórmula centraba los **orígenes de la grilla**, pero no el **contenido visual** del patrón.

## Fix v2

`Programas_hechos/Panel Decorativo/main.py` — `generate_centered_full_mode_geometry`:

```python
# Antes:
occupied_width = cols * step_x
start_x = margin + (usable_width - occupied_width) / 2

# Ahora:
bbox = original_piece.bbox()
piece_w = bbox.max_x - bbox.min_x
piece_h = bbox.max_y - bbox.min_y
visual_width = (cols - 1) * step_x + piece_w
visual_height = (rows - 1) * step_y + piece_h
start_x = margin + (usable_width - visual_width) / 2 - bbox.min_x
start_y = margin + (usable_height - visual_height) / 2 - bbox.min_y
```

El término `-bbox.min_x` compensa el desplazamiento del origen del DXF respecto al borde izquierdo del contenido.

También se agrega un bucle `while` que reduce `cols`/`rows` si `piece_w > step_x` (tile más ancho que su paso).

## Resultado verificado con el DXF real de red

| Panel | Gap izq | Gap der | Gap inf | Gap sup | Simétrico |
|---|---|---|---|---|---|
| 555×444 | 1.08mm | 1.08mm | 40.60mm | 40.60mm | ✓ |
| 555×999 | 1.08mm | 1.08mm | 24.10mm | 24.10mm | ✓ |

## Nota sobre el archivo local vs red

El archivo subido localmente (`outputs/.../subte.dxf`) tiene `bbox.min_x ≈ 0` (normalizado). El archivo en la red tiene `bbox.min_x = -26.18mm`. El motor usa la ruta del batch (`pattern_dxf_path`), que apunta al archivo de red — por eso el bug solo se manifestaba en producción.

## Tests

Test `test_centered_full_mode_grid_centering_subte_params` actualizado: ahora usa un piece con `min_x=-26.18` (simula el DXF real) y verifica simetría de gaps en lugar de coordenadas absolutas.

37 tests pasan. Los 4 errores son permisos Windows del directorio temp — pre-existentes, no relacionados.

— Punto
