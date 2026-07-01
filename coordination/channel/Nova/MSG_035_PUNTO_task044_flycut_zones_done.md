# MSG_035 — PUNTO → Nova
**Fecha:** 2026-07-01  
**Asunto:** TASK_044 Flycut zones cuadriculado cuadrado — COMPLETADO

---

## Status: COMPLETADO

Todos los criterios de aceptación cumplidos.

---

## Qué se hizo

### Funciones públicas de zona (spec exacto)

En `legacy_panel_adapter.py`:

```python
calcular_zonas(w_mm, h_mm, target=250.0)
# → (n_cols, n_rows, zone_w, zone_h, total_zonas)

zona_de_agujero(x, y, n_cols, n_rows, zone_w, zone_h)
# → int  (0-indexed, row_zona * n_cols + col_zona)
```

Las zonas se calculan sobre las dimensiones del **panel completo** (no el área visual de la grilla). `x, y` son relativos al origen del panel.

### Asignación de capas en el DXF

`_write_cuadriculado_square_to_doc` reescrito:
- **Antes:** capa fija `"CORTE"` + entidades GROUP `ZONA_CxFy`
- **Ahora:** `layer = str(zona % 16)` por agujero (CypCut capas 0-15)
- Parámetro `file_index` filtra qué chunk de 16 zonas escribir en ese doc
- CONTORNO sigue en capa `"CONTORNO"` siempre

### Multi-archivo DXF

Nueva función `_generate_cuadriculado_square_dxf_files(...)`:
- `total_zonas ≤ 16` → 1 archivo `{stem}.dxf`
- `total_zonas > 16` → N archivos `{stem}_flycut_1deN.dxf … {stem}_flycut_NdeN.dxf`
- Devuelve `{paths, pierce_count, cut_length_mm, zone_cols, zone_rows, total_zones, n_files}`

### Backend — `panel_sales_local_app.py`

En `_run_all_batches`:
- Reemplazó el enfoque de "combined_doc con offsets" por generación independiente por batch
- Si resultado es 1 archivo sin legacy → descarga directa
- Si hay múltiples archivos **o** hay también contenido legacy → ZIP `{order_id}_legacy_panel.zip`

En `_handle_download_dxf` y ruta `/outputs/`:
- Content-Type `application/zip` cuando el archivo es `.zip`
- `Content-Disposition: attachment` añadido a `/outputs/`

En `render_form`:
- Botón cambia a "Descargar ZIP (flycut)" cuando el resultado es ZIP
- Aviso amarillo: *"El panel fue dividido en X archivos DXF. Cargar en CypCut en orden."*

---

## Ejemplos de tabla del spec verificados

| Panel | n_cols | n_rows | Zonas | Archivos |
|---|---|---|---|---|
| 500×500 | 2 | 2 | 4 | 1 |
| 1220×2440 | 5 | 10 | 50 | 4 |

---

## Tests — `tests/test_cuadriculado_square_dxf.py`

15 tests pasan (0 fallos):

**Spec (3):**
- `test_zonas_panel_pequeno` — 500×500 → 2×2=4 zonas
- `test_zonas_panel_grande` — 1220×2440 → 5×10=50 → 4 DXFs
- `test_asignacion_zona_esquinas` — 4 esquinas → 4 zonas distintas

**Estructura DXF (6):**
- `test_returns_pierce_count_and_cut_length`
- `test_known_grid_dimensions`
- `test_no_holes_when_hole_too_big`
- `test_dxf_file_created`
- `test_dxf_has_contorno_layer`
- `test_dxf_squares_are_lwpolyline` (actualizado: capas numéricas, no "CORTE")
- `test_dxf_squares_have_4_vertices`
- `test_dxf_squares_are_closed`

**Capas numéricas (1):**
- `test_holes_on_numeric_layers` — verifica que ningún agujero está en "CORTE", todos en capas 0-15

**Multi-archivo (2):**
- `test_single_zone_produces_one_file`
- `test_large_panel_produces_multiple_files`

---

## Criterios de aceptación verificados

- [x] Cuadriculado modo Cuadrado asigna cada agujero a la capa de su zona geográfica (`str(zona % 16)`)
- [x] Panel ≤16 zonas → 1 DXF, descarga directa
- [x] Panel >16 zonas → ZIP con N DXFs nombrados `*_flycut_XdeN.dxf`
- [x] UI muestra mensaje informativo cuando se generan múltiples archivos
- [x] Cuadriculado Círculo, Tresbolillo y patrones custom NO modificados
- [x] Los 3 tests del spec pasan

## No modifica

- Cuadriculado modo Círculo (sigue en motor legacy, capa 0)
- Tresbolillo (sin cambios)
- Patrones DXF custom (sin cambios)
- Cálculo de recursos (pierce_count, cut_length_mm sin cambios)

---

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `apps/.../legacy_panel_adapter.py` | `calcular_zonas`, `zona_de_agujero`, `_write_cuadriculado_square_to_doc` (reescrito), `_generate_cuadriculado_square_dxf_files` (nueva), `_generate_cuadriculado_square_dxf` (actualizada) |
| `apps/.../panel_sales_local_app.py` | `_run_all_batches` (ZIP logic), `_handle_download_dxf` (ZIP content-type), `/outputs/` (Content-Disposition), `render_form` (botón + aviso flycut) |
| `tests/test_cuadriculado_square_dxf.py` | Reescrito: +spec 3 tests, +multi-file 2 tests, actualizado layer checks |
| `coordination/channel/Nova/MSG_035_...` | Este mensaje |

— Punto
