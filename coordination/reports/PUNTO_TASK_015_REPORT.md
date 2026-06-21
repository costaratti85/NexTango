# PUNTO_TASK_015 — Report: Editor de splines

**De:** Punto  
**Fecha:** 2026-06-17  
**Estado:** COMPLETO

---

## Resumen

Implementadas las tres partes del editor de splines en el browser. Todos los tests existentes pasan (35/35; los 7 ERRORs son fallas de infraestructura de pytest en esta máquina — directorio temp sin permisos — preexistentes a esta tarea).

---

## Parte 1 — Vista superpuesta (canvas único)

**Modal antes:** dos paneles side-by-side (`sc-orig-canvas` / `sc-conv-canvas`) con SVG independientes.

**Modal ahora:** un único `<svg id="sc-svg">` con cinco capas `<g>` apiladas:
- `sc-layer-orig` — geometría original en gris `#bbb`, opacidad 0.5, stroke 0.3% del viewBox
- `sc-layer-conv` — entidades editables en azul `#1a6fa8`, stroke 0.3% del viewBox
- `sc-layer-editor` — resaltado de selección (rojo, stroke 2.5x)
- `sc-layer-nodes` — círculos rojos de nodos libres (radio 1.2% del viewBox)
- `sc-layer-preview` — arco preview en verde punteado

Checkboxes `#sc-show-orig` y `#sc-show-conv` controlan visibilidad de cada capa via `scRenderLayers()`.

Zoom/pan se aplican directamente al `viewBox` del SVG (sin transformaciones CSS). Scroll de rueda hace zoom centrado en el cursor; drag arrastra el viewBox.

El viewBox combinado es la unión de los bounding boxes de ambos DXFs calculada en JS.

---

## Parte 2 — Editor interactivo

### Carga de entidades
Al abrir el modal:
1. Se obtiene el SVG original via `GET /api/patterns/preview_dxf?mode=original` para extraer los segmentos del layer gris.
2. Se convierte el DXF via `POST /api/patterns/convert_splines` (existente).
3. Se cargan las entidades editables via `GET /api/patterns/entities?path=...` (nuevo).

Cada entidad tiene un `id` único. `_editEntities[]` es la lista mutable; `_editOrigEntities[]` es la copia para descartar.

### Selección
Click en cualquier `<path>` del layer convertido llama `scEntityClick(eid)`. La entidad seleccionada se dibuja en rojo con stroke 2.5x. También hay paths transparentes más anchos como hit-targets.

### Delete
Tecla Delete/Backspace (el SVG tiene `tabindex=0`) llama `scDeleteSelected()`:
- Calcula los dos endpoints de la entidad (para arcos: puntos a `startAngle` y `endAngle`).
- Elimina la entidad de `_editEntities[]`.
- Carga los dos endpoints en `_freeNodes[]`.
- Cursor cambia a crosshair.

### Preview del arco
`window.mousemove` escucha mientras `_freeNodes.length === 2`:
- Convierte la posición del cursor a coordenadas de modelo via `_svgToModel()`.
- Calcula el arco circunscripto por `arcThrough3Points(freeNodes[0], cursor, freeNodes[1])`.
- Lo dibuja en `sc-layer-preview` como `<path>` con `A` (arc SVG) en verde punteado.
- `sweep` (CW vs CCW) se determina por el signo del producto vectorial de los tres puntos.
- Si los puntos son colineales, no se dibuja nada.

### Confirmar arco
Click en el canvas (mouseup sin drag, con `_freeNodes.length === 2`) llama `_scConfirmArc()`:
- Calcula el arco definitivo.
- Lo agrega a `_editEntities[]` con id único.
- Limpia `_freeNodes`, borra el preview, vuelve a modo normal.

### Descartar cambios
Botón "Descartar cambios" llama `scDiscardEdits()`: restaura `_editEntities` desde `_editOrigEntities` (deep copy).

---

## Parte 3 — Export y nuevos endpoints

### `GET /api/patterns/entities?path=...`
Implementado en `_handle_patterns_entities()` y `_dxf_entities_json()`.

Lee el DXF con ezdxf, extrae todas las entidades LINE y ARC de la capa `ARCOS_CONVERTIDOS` (o de todas las capas si esa capa no existe). Retorna JSON:
```json
{"entities": [{"type": "arc", "cx": ..., "cy": ..., "radius": ..., "startAngle": ..., "endAngle": ..., "id": "e0"}, ...]}
```

### `POST /api/patterns/finalize_edit`
Implementado en `_handle_finalize_edit()` y `_entities_to_dxf()`.

Recibe `{entities, name, step_x, step_y}`, genera un DXF limpio en `outputs/panel_sales_demo/uploaded_patterns/{name_editado}.dxf`, lo registra con `add_pattern_to_library()` (sin restricciones — todas las entidades son LINE/ARC), y dispara la generación del thumbnail en background.

### `confirmAndLoad()` actualizado
Serializa `_editEntities[]` a JSON y hace `POST /api/patterns/finalize_edit` en lugar del flow anterior (que usaba `/api/patterns/add` con el path del archivo convertido). Esto garantiza que el patrón registrado refleja exactamente lo que el usuario editó en el canvas.

---

## Archivos modificados

- `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`
  - Nuevas funciones: `_dxf_entities_json()`, `_entities_to_dxf()`
  - Nuevos handlers: `_handle_patterns_entities()`, `_handle_finalize_edit()`
  - Nuevas rutas GET: `/api/patterns/entities`
  - Nuevas rutas POST: `/api/patterns/finalize_edit`
  - Modal HTML completamente reemplazado: canvas único superpuesto + botón "Descartar cambios"
  - JavaScript del modal completamente reemplazado: ~400 líneas del nuevo editor

---

## Tests

```
35 passed, 0 failed
7 errors (preexistentes — falla de permisos en directorio temp de pytest en esta máquina)
```

Todos los `render_admin_*` tests pasan. Los tests de integración que requieren el legacy engine fallan por permisos de SO, no por código.
