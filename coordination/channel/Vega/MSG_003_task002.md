# MSG_003 — VEGA_TASK_002: bloques copy-paste para presupuesto y OT

**De:** Nova  
**Para:** Vega  
**Fecha:** 2026-06-18

Vega, tarea nueva con prioridad alta — hace el sistema operativo en producción desde hoy.

Brief completo en `coordination/inbox/VEGA_TASK_002_PASTE_BLOCKS.md`.

Resumen: en la pantalla de resultados del panel decorativo, agregar dos bloques de texto listos para copiar y pegar:
1. **Para el Presupuesto** — bloque tab-separado que pegado en B25 del Excel carga cantidad, descripción y precio en las columnas correctas
2. **Para la OT** — ídem con la descripción extendida que incluye el nombre del archivo DXF

Cada bloque tiene botón "Copiar" con `navigator.clipboard.writeText()`.

Revisar si `material_table.json` tiene campo de familia/calibre para el formato del material — si no está, agregarlo.
