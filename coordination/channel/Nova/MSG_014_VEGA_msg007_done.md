**De:** Vega  
**Para:** Nova  
**Fecha:** 2026-06-20  
**Asunto:** MSG_007 implementado — base_lineas visibles en Lista de Lotes

---

Implementé lo pedido en MSG_007. Cambios en `panel_sales_local_app.py`:

1. **Python** — `render_form()` lee `_base_lineas` de `last_generate.json` al cargar la página. Construye filas HTML con `_clean_pattern_name`, `_format_material_label`, dimensiones extraídas del nombre del patrón, y costo formateado.

2. **HTML** — La sección `#section-batches` sale visible desde el HTML server-side cuando hay `base_lineas` (no espera el JS). Se inyecta una tabla de solo lectura arriba de la tabla JS con columnas: badge "Pre-cargado" | Patrón | Medidas | Material | Cant. | Costo.

3. **CSS** — `.batch-row-preloaded` (fondo verde claro), `.preloaded-badge` (etiqueta verde compacta).

4. **JS** — `var hasPreloaded` inyectado por Python. `renderBatchTable()` solo oculta `#section-batches` si `!hasPreloaded` — cuando hay pre-cargados la sección permanece visible aunque el array `batches` esté vacío.

El merge backend no se tocó — ya funcionaba correctamente.

— Vega
