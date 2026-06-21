# MSG_010_PUNTO_task025_done

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-18  
**Re:** TASK_025 completada — Etiqueta DXF: formato abreviado + justificación derecha

---

## Resumen

TASK_025 completada. Los dos cambios están aplicados.

## Cambio 1 — Justificación: left → right

Ya estaba implementado en `dxf_writer.py` (función `_text_right`, group code DXF `72=2`). El texto se alinea hacia el borde izquierdo sin solapar el área de corte.

## Cambio 2 — Formato abreviado de material

`dxf_batch_compiler.py` ahora:
1. Lee `material_table.json` y usa el campo `familia` para determinar el formato
2. Genera `N°18`, `Galv N°18`, `Inox 304 1.25mm`, `Inox 430 1.25mm` según corresponda
3. El label del material aparece una vez por fila en el DXF (deduplica por Y)

El campo `familia` ya existía en `material_table.json` para todas las entradas — no fue necesario modificarlo.

## Resultados verificados

```
'Chapa doble decapada' 1.25mm → N°18
'Chapa galvanizada'    1.25mm → Galv N°18
'Inoxidable 304'       1.25mm → Inox 304 1.25mm
'Inoxidable 430'       1.25mm → Inox 430 1.25mm
```

20/20 tests pasan. Reporte completo: `coordination/reports/PUNTO_TASK_025_REPORT.md`

---

**TASK_025 completada. Listo para próxima tarea.**
