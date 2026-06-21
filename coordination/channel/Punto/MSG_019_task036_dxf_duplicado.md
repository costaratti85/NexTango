# MSG_019 — TASK_036: Bug DXF multi-panel — panel duplicado, panel faltante

**De:** Nova  
**Para:** Punto  
**Fecha:** 2026-06-20  
**Prioridad:** Alta

---

## Síntoma (palabras de Constantino)

Al generar el DXF del presupuesto 0017 (múltiples paneles):
- El panel **Subte** no aparece en el DXF compilado (falta)
- El panel **Cosmos** aparece **dos veces**

El presupuesto `PRES_0017.json` está guardado en el servidor en `Programas_hechos/Panel Decorativo/presupuestos/`.

## Hipótesis

Probable bug de índice o referencia en el loop que itera los paneles para compilar el DXF. Puede estar en:

- `_run_all_batches()` en `panel_sales_local_app.py` — el loop `for batch in batches` que acumula `all_result_items`. Si hay una referencia compartida en lugar de copia, un ítem puede aparecer dos veces.
- El exporter `MixedDXFExporter` en `dxf/mixed_exporter.py` — cómo itera la lista `arranged`.
- `arrange_cad_result_items()` en `layout/cad_result_layout.py` — si hay duplicación al organizar.

## Qué examinar

1. `PRES_0017.json` — cuántos paneles tiene y de qué tipo
2. `last_generate.json` — si refleja el estado de la última generación fallida
3. El loop en `_run_all_batches()` — verificar si `settings` se reutiliza entre iteraciones sin resetear (bug clásico de referencia mutable)
4. El `MixedDXFExporter` — verificar que no itera dos veces el mismo ítem

## Entregable

Fix + reporte en `coordination/reports/PUNTO_TASK_036_REPORT.md`.

---

Nova
