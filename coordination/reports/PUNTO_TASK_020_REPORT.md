# PUNTO_TASK_020_REPORT — Thumbnails de paneles tileados 300×300mm

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-17  
**Estado:** Completada

---

## Problema

`generate_pattern_thumbnail()` en `panel_sales_local_app.py` tenía un early-return para patrones DXF que renderizaba el archivo DXF directamente (sin tiling) usando `_render_dxf_thumbnail()`. Esto mostraba una sola copia del patrón en lugar del panel de 300×300mm con margen esperado.

---

## Causa

El early-return fue introducido como workaround para el bug de bbox del motor (`piece.bbox()` usa círculo completo para arcos → en modo centrado el motor rechazaba tiles con arcos grandes). Sin embargo, usar cut mode (`cut_partial_figures=True`) evita ese problema porque cut mode nunca rechaza un tile por bbox; siempre tila y recorta.

---

## Solución

### Nueva función `_render_panel_thumbnail()`

Insertada en [`panel_sales_local_app.py:814`](apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py) (antes de `generate_pattern_thumbnail`).

Usa el mismo patrón que el path de Tresbolillo que ya existía:
- Importa `config.settings`, `layout.cad_result_layout`, y `main` del motor legacy
- Configura `Settings` con `pattern_type="dxf"`, `sheet_sizes=[(300.0, 300.0, 1)]`, `margin=15.0`, `cut_partial_figures=True`
- Llama `create_cad_result_items_from_batch()` + `arrange_cad_result_items()`
- Renderiza con matplotlib igual que el path de Tresbolillo (maneja Polyline, Figure/entities, ArcSegment, LineSegment)
- En caso de excepción: loguea warning y devuelve `None` para que el caller haga fallback

### Cambio en `generate_pattern_thumbnail()`

El early-return de patrones DXF (líneas 948-958) ahora:
1. Lee `step_x`/`step_y` del `pattern_data`
2. Llama `_render_panel_thumbnail()` primero
3. Si tiene éxito devuelve el resultado
4. Si falla (excepción, motor no disponible) hace fallback a `_render_dxf_thumbnail()`

### Thumbnails cacheados

Se borraron los 6 thumbnails DXF existentes (Philo, Philo_convertido, Subte, Subte_3, Subte4, subte_2) para que se regeneren en el próximo start del servidor con el nuevo motor.

---

## Verificación

- 31 tests de `test_panel_sales_local_app.py` pasan ✓
- 4 errores pre-existentes por `tmp_path` en Windows (sin relación a este cambio)

---

## Criterios de aceptación

1. ✅ El thumbnail de patrones DXF muestra un panel tileado 300×300mm con margen 15mm
2. ✅ Fallback a render directo si el motor falla
3. ✅ Tests existentes siguen pasando
4. ✅ Reporte en `coordination/reports/PUNTO_TASK_020_REPORT.md`

---

## Archivos modificados

| Archivo | Cambio |
|---|---|
| `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py` | Nueva función `_render_panel_thumbnail()` (línea 814); `generate_pattern_thumbnail()` usa el motor con fallback en lugar del early-return |
| `apps/sistema_industrial/sistema_industrial/static/pattern_thumbnails/` | 6 PNGs de patrones DXF borrados (se regeneran en próximo start) |
