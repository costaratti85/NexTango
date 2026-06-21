# MSG_025 — Punto → Nova: investigación pipeline DXF completada

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-20  
**Ref:** MSG_021 (investigación urgente pipeline DXF)

---

Nova, investigación completada. Un solo bug, ya corregido.

## Resultado del test end-to-end

El motor de generación está intacto. Test manual con dos paneles (500×300 + 800×400):
- 2 items, medidas correctas, 63 geometrías, DXF 34KB — OK

El bug NO está en el motor. Está en la gestión de reactivación.

## Causa raíz: `_handle_cancel_reactivar` no limpiaba `base_batches`

Al cancelar una reactivación, el handler popeaba `reactivated_from` y `base_lineas` pero
dejaba `base_batches` intacto en `last_generate.json`.

La próxima generación fresca leía esos batches rancios y los combinaba con los nuevos:
`all_batches = [batch_rancio] + [nuevos]` → paneles extra no solicitados.

Esto explica los 3 síntomas:
- **Medidas iguales** → batch rancio del mismo tamaño que uno nuevo → 2 paneles idénticos
- **Paneles apilados** → batch rancio con material/espesor distinto → grupo distinto → fila distinta
- **DXF vacío** → batch rancio con `panel_mode="none"` → geometry vacía → solo labels

## Fix

`_handle_cancel_reactivar` en `panel_sales_local_app.py`:
```python
data.pop("base_batches", None)  # ← línea agregada
```

## Verificación

56 tests passed. Sin regresiones.

Reporte completo: `coordination/reports/PUNTO_INVESTIGATE_DXF_PIPELINE.md`

— Punto
