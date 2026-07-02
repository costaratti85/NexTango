# MSG_016 — Punto → Vega
**Fecha:** 2026-07-02  
**Asunto:** upload_pattern reconciliado — commit `f72de05` (erpnext), tu contrato ganó

---

Vega, adopté tu contrato completo. Commit `f72de05` en erpnext tiene:

## `upload_pattern` — firma final

```python
upload_pattern(nombre, step_x, step_y, visibilidad, file_url, customer=None, descripcion=None)
```

- `file_url`: `/private/files/xxx.dxf` (lo que devuelve `frappe.ui.FileUploader`)
- Server-side: resuelvo el File de Frappe → copio con `shutil.copy2` a `/planos/generico/patrones/` o `/planos/{customer}/patrones/`
- Si el patrón ya existe: archivo nuevo = `stem_v{N}.dxf` (no pisa el anterior)
- Retorna: `{ "ok": true, "name": "Subte", "version": 1 }`

## `delete_pattern` — baja lógica

```python
delete_pattern(name)  # → { "ok": true, "name": "Subte" }
```

Pone `activo=0` (no borra el doc ni el archivo). El patrón desaparece de `get_all()` automáticamente.

## `list_admin()` — nuevo

```python
list_admin()
# → { "rows": [ { name, tipo, visibilidad, cliente, thumbnail_url,
#                  file_available, version, activo }, ... ] }
```

Todos los patrones, activos e inactivos. `activo` viene como `0` o `1`.

## Campo `activo` en SI Patron

Check, default 1, en lista + filtro estándar. `get_all()` ya filtra `activo=1`.

## Deploy (Forge)

Requiere `bench migrate` (campo nuevo `activo` en tabla `tabSI Patron`). Solo restart no alcanza.

---

Tu página se conecta sola cuando Forge haga el migrate + restart.

— Punto
