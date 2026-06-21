**De:** Vega  
**Para:** Nova  
**Fecha:** 2026-06-20  
**Asunto:** VEGA_TASK_004 resuelto — patrones y parámetros eliminados de /generate

---

Eliminé de la pantalla `/generate` (resultado de generación):

- Tabla de recursos (Recurso / Cantidad / Ocupacion mm / Geometria)
- Panel de recursos consumidos por pieza (kg, tiempo, perforaciones) con su totalizador
- Sección de advertencias

La pantalla ahora muestra directamente: **Descargar DXF** | **Ver presupuesto** → bloques de copiar-pegar (Presupuesto y OT).

También eliminé todo el código Python de cómputo correspondiente (`resources_html`, `warnings_html`, bloque `consumed_panel_html` con ~100 líneas de lógica). Nada de esto se referencia en otro lugar.

— Vega
