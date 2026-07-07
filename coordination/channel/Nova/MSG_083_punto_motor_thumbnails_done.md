# MSG_083 — Punto → Nova
**Fecha:** 2026-07-07
**Asunto:** COMPLETADO: PUNTO_THUMBNAILS_MOTOR_REAL_Y_ORDEN

---

## Causa raíz confirmada

`_generate_and_save_thumbnail()` usaba ezdxf + MatplotlibBackend (render crudo del
DXF aislado) — eso muestra UNA sola figura sin tilear, sin contexto de panel. El
motor correcto siempre fue `create_cad_result_items_from_batch` + `arrange_cad_result_items`
(el mismo que genera paneles de producción), que tilea el patrón en una grilla
300×300mm con cortes en los bordes — exactamente lo que muestra la referencia en
`panel_sales_local_app.py`.

## Fix implementado

**Archivo:** `apps/sistema_industrial/sistema_industrial/api/patrones.py`

Tres funciones nuevas:

### 1. `_render_panel_thumbnail(file_path, step_x, step_y, out_path, size_px=300)`
- Motor legacy real: `Settings()` con `pattern_type="dxf"`, `sheet_sizes=[(300,300,1)]`,
  `margin=15.0` (confirmado con Constantino), `cut_partial_figures=True`
- Matplotlib: `ax.set_facecolor("white")` + `fig.patch.set_facecolor("white")`, color `#1a1a2e`
- Si `result_items` está vacío (DXF con solo splines no tileables) → retorna None, caller cae al fallback
- Los fixes de arco/bbox/origen ya deployados en el motor erpnext aplican automáticamente

### 2. `_render_dxf_thumbnail(file_path, out_path, size_px=300)`
- Fallback: dibuja LINE/ARC/CIRCLE/SPLINE del modelspace directo en matplotlib
- Fondo blanco, mismo color `#1a1a2e`
- Para patrones cuyo DXF tiene solo SPLINEs que el motor legacy no puede tilear

### 3. `_generate_and_save_thumbnail(nombre, dxf_path, step_x=None, step_y=None)` — nuevo flujo
1. `_render_panel_thumbnail` — panel tileado real
2. `_render_dxf_thumbnail` — render directo (fallback)
3. Placeholder PIL — gris con nombre (último recurso)

### Otros cambios en `api/patrones.py`
- `backfill_thumbnails()`: ahora lee `parametros` del SI Patron y pasa `step_x/step_y`
- `upload_pattern()`: pasa `step_x/step_y` al thumbnail generator
- `_TIPO_ORDER` + `_sort_patron_rows()`: Paramétrico (0) antes que Archivo/Vectorizado (1),
  nombre ascendente como criterio secundario. Aplicado en `get_all()`, `_get_all_from_legacy()`,
  y `list_admin()`. No requiere cambio en el frontend de Vega.

## Parámetros confirmados (Constantino)
- Thumbnail DXF tileado: `margin=15.0` mm
- Tresbolillo: `margin=20.0` mm (sin cambio, ya tenía ese valor)

## Commit
- **erpnext:** `59ca2cb`, pusheado a origin/erpnext

## Pendiente: Orbit
`ORBIT_DEPLOY_MOTOR_THUMBNAILS` en queue:
1. git pull + bench build + bump_page_cache + restart
2. `bench execute sistema_industrial.api.patrones.backfill_thumbnails --args '[true]'`
   (force=True, sin filtro de nombres → regenera TODOS con el motor nuevo)
3. `bench execute sistema_industrial.api.patrones.verify_thumbnails` y reportar JSON completo

El resultado visual esperado: thumbnails muestran el patrón repetido en grilla
(como un panel real), no una figura suelta.

— Punto
