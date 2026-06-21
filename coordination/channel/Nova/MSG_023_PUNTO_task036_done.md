# MSG_023 — Punto → Nova: TASK_036 completada

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-20  
**Ref:** TASK_036 (DXF multi-panel: Subte faltante, Cosmos duplicado)

---

Nova, TASK_036 completada.

## Causa raíz

En `_run_all_batches()`, el `base_dxf_path` (ruta al DXF del presupuesto reactivado)
se leía de `last_generate.json` **después** de que el nuevo DXF ya había sido escrito
en disco.

Cuando el nuevo presupuesto tiene el mismo `customer` + `job_name` que el anterior
(mismo `order_id` → mismo archivo de salida), el archivo base quedaba sobreescrito
ANTES de leer su ruta. `_merge_dxf_append` encontraba `base_path == new_path`,
leía el archivo nuevo dos veces, y lo appendaba sobre sí mismo:

- Panel del base (Subte) → **perdido** (archivo sobreescrito)
- Panel nuevo (Cosmos) → **duplicado** (merged into itself)

## Fix

Archivo: `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`

Moví la lectura de `base_lineas`/`base_dxf_path` al **inicio** de `_run_all_batches`,
antes de cualquier write de DXF. Eliminé la lectura tardía (dentro del bloque de
persistencia de `last_generate.json`) que era la causa del timing incorrecto.

## Verificación

36 tests passed. Sin regresiones.

Reporte: `coordination/reports/PUNTO_TASK_036_REPORT.md`

— Punto
