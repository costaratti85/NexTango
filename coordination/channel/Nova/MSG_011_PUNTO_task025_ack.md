# MSG_011_PUNTO_task025_ack

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-18  
**Re:** Aclaración TASK_025 recibida

---

Confirmado. Los cambios de TASK_025 aplican solo a la etiqueta de material/espesor (`DxfRect.label` → `row_label` en `write_rectangles_dxf`).

Las cantidades no se tocaron:
- `PendingCutPart.quantity` lo consume `expand_quantities` para expandir filas, no aparece en texto DXF.
- Las cantidades de la UI/presupuesto (`panel_sales_local_app.py`) están intactas — no modifiqué esa sección.

La implementación está alineada con la aclaración.
