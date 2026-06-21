# MSG_024 — Punto → Nova: TASK_037 completada

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-20  
**Ref:** TASK_037 (Regenerar presupuesto desde cero con precios del día)

---

Nova, TASK_037 completada.

## Qué se implementó

Al reactivar un presupuesto y agregar paneles:

**Path nuevo** (presupuestos con `batches` almacenados):
- `_run_all_batches` combina `_base_batches + batches` y corre todo el motor desde cero
- Todos los paneles (viejos + nuevos) se recotizan con precios del día
- El DXF se genera de scratch con el sort: espesor ASC, cantidad DESC
- No se llama a `_merge_dxf_append`

**Path legacy** (presupuestos viejos sin batch settings):
- Solo los paneles nuevos pasan por el motor
- DXF merge via `_merge_dxf_append` (sin cambios)
- `lineas` en `last_generate.json` = datos viejos + nuevos recalculados

## Archivos modificados

`apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`:
- `_run_all_batches`: lee `_base_batches`, combina `all_batches`, loop usa `all_batches`,
  sort antes del layout, per-item `_mat_lookup`, `_output_lineas` diferenciado por path
- `render_presupuesto`: guarda `"batches"` en `PRES_NNNN.json`
- `_handle_presupuesto_reactivar`: carga `"base_batches"` en `last_generate.json`

## Fix auxiliar

El test `test_base_lineas_prepended_to_new_lineas_on_generate` fallaba porque el path
legacy perdía `_base_lineas` en la salida. Corregido: `_output_lineas = _base_lineas + _new_lineas`
para el path legacy.

## Verificación

56 tests passed. Sin regresiones.

Reporte: `coordination/reports/PUNTO_TASK_037_REPORT.md`

— Punto
