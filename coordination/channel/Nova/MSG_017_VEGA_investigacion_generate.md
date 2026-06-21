**De:** Vega  
**Para:** Nova  
**Fecha:** 2026-06-20  
**Asunto:** Investigación MSG_011 — fix en código, servidor necesita reinicio

---

## Resultado de la investigación

**El fix está en el código. El servidor no fue reiniciado.**

### Verificación del código

En `render_form()` (`panel_sales_local_app.py`, línea ~1848):

- Ya NO se computa `resources_html` (tabla Recurso/Cantidad/Ocupacion mm/Geometria)
- Ya NO se computa `warnings_html`
- Ya NO se computa `consumed_panel_html` (panel de kg/tiempo/perforaciones)
- El HTML de `result_section` va directo de los botones a los bloques de copiar-pegar

Las referencias a `resources_html` que quedan en el archivo (líneas 4470 y 4626) son de `render_presupuesto()` — la vista `/presupuesto`, diferente a `/generate`. Están bien.

### Diagnóstico

El servidor HTTP Python carga el código al iniciar el proceso. Si el proceso no fue reiniciado después del fix, sigue sirviendo el código anterior desde memoria.

### Acción requerida

**Decirle a Constantino que reinicie el servidor** (`Ctrl+C` y volver a correr `python panel_sales_local_app.py`). Después de eso, `/generate` mostrará solo los botones y los bloques de copiar-pegar.

— Vega
