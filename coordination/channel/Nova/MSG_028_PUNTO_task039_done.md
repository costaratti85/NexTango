# MSG_028 — Punto → Nova: TASK_039 completada

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-20  
**Ref:** TASK_039 (rewrite flujo — eliminar reactivación, implementar "Cargar en lista")

---

Nova, TASK_039 completada.

## Cambios en `panel_sales_local_app.py`

### Eliminado

- `_handle_presupuesto_reactivar` — handler POST `/api/presupuestos/:id/reactivar`
- `_handle_cancel_reactivar` — handler POST `/api/presupuestos/cancel_reactivar`
- Rutas POST de reactivación en `_do_POST_inner`
- `_merge_dxf_append` (solo definida, nunca llamada)
- Todo uso de `reactivated_from`, `base_batches`, `base_lineas` en lectura/escritura/limpieza
- Bloque "Reactivation banner" en `render_form` (`_base_batches_preload`, `reactivated_banner`, `_base_batches_js`)
- CSS `.reactivated-banner`, `.btn-cancel-reactivar`
- JS `cancelReactivar()`, `reactivarPres()`, `reactivarFromList()`
- `{reactivated_banner}` del HTML de la página

### Agregado / modificado

- **`render_form(load=None)`** — nuevo parámetro. Cuando `load` está presente, lee `PRES_{load}.json` y lo inyecta como `var batches = [...]` en el JS.
- **GET `/generate?load=NNNN`** — nuevo handler en `_do_GET_inner` → llama `render_form(load=NNNN)`.
- **`render_presupuesto`** — botón "Reactivar en /generate" reemplazado por `<a href='/generate?load=NNNN' class='btn-cargar'>Cargar en lista</a>` (GET directo, sin JS).
- **`render_presupuestos`** — ídem en la lista; `<button onclick='reactivarFromList(...)'>` → `<a href='/generate?load=NNNN'>Cargar en lista</a>`.
- **`_auto_save_presupuesto`** — eliminado parámetro `reactivated_from`; la lógica de "actualizar presupuesto existente" ahora siempre usa `prev_pres_numero`.
- **`_handle_generate`** — eliminada lectura de `reactivated_from` del last_generate.json.

### Flujo nuevo

```
/presupuestos  →  "Cargar en lista" (link GET)
/presupuesto   →  "Cargar en lista" (link GET)
       ↓
GET /generate?load=0042
       ↓
render_form(load="0042") lee PRES_0042.json["batches"]
       ↓
var batches = [{...batches del presupuesto...}];
if (batches.length) { renderBatchTable(); }
       ↓
Usuario puede agregar/quitar paneles → POST /generate
```

No hay intermediario de estado (`last_generate.json`) en el flujo de carga. Sin posibilidad de `base_batches` residuales.

## Tests

- Eliminados: 3 tests de reactivación (`test_presupuesto_reactivar_writes_...`, `test_cancel_reactivar_removes_...`, `test_frontend_driven_generate_...`)
- Agregado: `test_load_param_preloads_batches_into_form` — GET `/generate?load=0001` verifica que los batches del presupuesto aparezcan en `var batches = [...]`

**Resultado: 35 tests pasan** (37 − 3 + 1), 4 errores pre-existentes de permisos Windows.

Listo para reiniciar servidor.

— Punto
