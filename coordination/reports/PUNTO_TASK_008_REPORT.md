# PUNTO_TASK_008_REPORT — Tres fixes críticos

**Agente:** Punto  
**Fecha:** 2026-06-15  
**Estado:** COMPLETADO

---

## Fix 1 — Botón Borrar (HTML bug)

**Archivo modificado:** `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`

El onclick del botón Borrar usaba `json.dumps(name)` que produce comillas dobles dentro del atributo HTML con comillas dobles, truncando el atributo en el browser.

**Cambio:** El botón ahora usa `data-pattern-name="{safe_name}"` y el onclick lee `this.dataset.patternName`. `safe_name` ya era `escape(name)` (HTML-safe). La función JS `deletePattern(name, btn)` no cambió.

---

## Fix 2 — Recursos en cero (adaptador bypasseado)

**Archivo modificado:** `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`

El loop `all_resources` leía `item.cut_length_mm` e `item.pierce_count` directamente del motor legacy (que devuelve 0 hardcodeado). Las funciones correctas de Gemu en `legacy_panel_adapter.py` nunca se llamaban desde este path.

**Cambio:** Se agregaron `calculate_cut_length_mm` y `calculate_pierce_count` al import existente de `legacy_panel_adapter`. En el dict `all_resources`, los dos campos ahora llaman a estas funciones pasando `item.geometry_items`.

---

## Fix 3 — Nueva página `/materiales`

**Archivo modificado:** `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`

Se agregó:
- `render_materiales()` — función que genera la página HTML completa con tabla editable inline
- Ruta `GET /materiales` en `do_GET`
- Link `<a href="/materiales">` en `_TOPBAR_ADMIN_HTML`
- Link `<a href="/admin">Volver a Admin</a>` en el header de `/materiales`

**UX implementada:**
- Carga los materiales vía `GET /api/materials` al cargar la página (JS fetch)
- Columnas: Material | Espesor mm | Densidad kg/m² | Vel. corte mm/s | T. perforación s | Acciones
- Celdas editables inline: click → input editable con highlight amarillo
- Enter: guarda y avanza a la fila siguiente; Tab: guarda y avanza a la columna siguiente
- Escape: cancela sin guardar
- Fila nueva siempre visible al final con inputs directos; Tab en el último campo guarda y limpia
- Botón Borrar por fila, con feedback visual durante la operación
- Status bar en la parte inferior del card para confirmaciones y errores
- `consumible_por_perforacion` se envía como 0 en filas nuevas (campo oculto, requerido por API)

---

## Tests

- 28 tests de `test_panel_sales_local_app.py` pasan (sin cambio en conteo previo)
- 20 tests de otros archivos pasan
- 4 errores en `test_panel_sales_local_app.py` son pre-existentes (fixture `tmp_path` falla por permisos Windows en `pytest-of-vendo`)
- 6 errores en otros archivos son pre-existentes (mismo motivo)
- Ningún test nuevo roto por estos cambios
