# PUNTO_TASK_018_REPORT — Resultado, presupuestos y campo cliente

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-17  
**Estado:** Completada

---

## Cambios realizados

### 1. `dxf_path` en `last_generate.json`

Al guardar `last_generate.json` después de una generación, se agrega el campo `dxf_path` con la ruta absoluta del DXF producido. Esto permite que `/presupuesto` ofrezca el botón de descarga sin necesidad de recalcular ni buscar el archivo.

### 2. Topbar — link a `/presupuestos` (plural)

`_topbar_html()` ahora genera el link como `/presupuestos`. La página activa correspondiente es `"presupuestos"`. El docstring del parámetro `active` fue actualizado.

### 3. `/presupuesto` — botón "Descargar DXF"

Si `presupuesto_data["dxf_path"]` no está vacío, aparece el botón `⬇ Descargar DXF` en la barra de acciones. Sirve el archivo vía `GET /download_dxf?path=...`.

`_handle_download_dxf()` valida que el path resuelto esté dentro de `output_dir` antes de servir (previene path traversal). Responde con `Content-Disposition: attachment`.

### 4. `/presupuesto` — campo cliente editable

Campo `<input>` con `id="cliente-input"` que muestra el nombre del cliente. Guarda automáticamente vía:
- `blur`: al perder el foco
- Debounce de 1500ms en cada keystroke

El endpoint `POST /api/presupuestos/:id/cliente` actualiza el JSON en disco y responde `{"ok": true}`. El indicador "✓ guardado" aparece 2 segundos después del save exitoso.

### 5. `/presupuestos` — lista de presupuestos

Nueva función `render_presupuestos()` y ruta `GET /presupuestos`. Muestra todos los `PRES_NNNN.json` en `PRESUPUESTOS_DIR`, ordenados de más nuevo a más viejo, con columnas:

| N° | Fecha | Cliente | Total | Ver | Borrar |
|---|---|---|---|---|---|

- **Ver** → `/presupuesto?id=NNNN`
- **Borrar** → `DELETE /api/presupuestos/NNNN` con confirmación JS antes de llamar

### 6. Endpoints nuevos

| Método | Path | Handler |
|---|---|---|
| `GET` | `/presupuestos` | `render_presupuestos()` |
| `GET` | `/download_dxf?path=...` | `_handle_download_dxf()` |
| `POST` | `/api/presupuestos/:id/cliente` | `_handle_presupuesto_cliente()` |
| `DELETE` | `/api/presupuestos/:id` | `_handle_presupuesto_delete()` |

---

## Tests

Tres tests nuevos en `tests/test_panel_sales_local_app.py`:

| Test | Resultado |
|---|---|
| `test_topbar_presupuestos_link_points_to_plural` | ✓ pasa |
| `test_render_presupuestos_empty_state` | ✓ pasa |
| `test_render_presupuestos_lists_saved_files` | ✓ pasa |

Total suite: 31 tests pasan (4 deseleccionados por ERRORs pre-existentes de `tmp_path` en Windows).

---

## Criterios de aceptación

1. ✅ Desde `/presupuesto` se puede descargar el DXF del panel generado
2. ✅ `/presupuestos` lista todos los presupuestos guardados con fecha, cliente y total
3. ✅ Desde la lista se puede ver cada presupuesto individual y borrarlo
4. ✅ El campo de cliente se puede editar y persiste al recargar la página
5. ✅ Tests existentes siguen pasando

---

## Archivos modificados

| Archivo | Cambio |
|---|---|
| `apps/.../panel_sales_local_app.py` | Todos los cambios descriptos arriba |
| `tests/test_panel_sales_local_app.py` | 3 tests nuevos + imports actualizados |
