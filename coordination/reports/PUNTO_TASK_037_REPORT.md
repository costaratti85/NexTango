# PUNTO_TASK_037 — Regenerar presupuesto: DXF desde cero, precios del día

**Fecha:** 2026-06-20  
**Estado:** Completada

---

## Objetivo

Al reactivar un presupuesto y agregar paneles nuevos:
- Descartar el DXF viejo
- Recotizar **todos** los paneles (viejos + nuevos) con precios del día
- Generar el DXF desde cero con la lista completa ordenada por espesor ASC, cantidad DESC

---

## Diseño

### Path nuevo (presupuestos con `batches` almacenados)

Los presupuestos generados a partir de esta versión guardan `"batches"` en `PRES_NNNN.json`.
Al reactivar, esos batches se cargan como `"base_batches"` en `last_generate.json`.

`_run_all_batches` combina `all_batches = _base_batches + batches` (paneles viejos + nuevos),
corre todo el motor desde cero, genera un DXF unificado con el sort correcto, y recotiza
todos los paneles con precios del día.

### Path legacy (presupuestos anteriores sin `batches`)

Los presupuestos viejos solo tienen `"lineas"` pero no batch settings. En ese caso:
- `_base_batches` queda vacío
- `_base_lineas` se lee (datos de precios viejos, no recalculables)
- Solo los paneles nuevos se corren por el motor
- El DXF nuevo se merge al anterior con `_merge_dxf_append`
- `last_generate.json["lineas"]` = `_base_lineas + _new_lineas` (datos históricos + nuevos)

---

## Cambios en `panel_sales_local_app.py`

### `_run_all_batches()` — top section
- Lee `_base_batches` de `last_generate.json` **antes** de generar el DXF (corrección TASK_036 ya presente)
- `all_batches = _base_batches + batches`

### Loop del motor
- `for batch in all_batches:` (en vez de `for batch in batches:`)

### Sort antes del layout
```python
all_result_items.sort(key=lambda it: (it.thickness, -it.quantity))
arranged = layout_module.arrange_cad_result_items(all_result_items)
```
Agrupa paneles por espesor ASC, cantidad DESC en el DXF.

### `first_batch` usa `all_batches`
```python
first_batch = all_batches[0]
```

### Per-item material lookup
Reemplaza el `_mat_entry` único del primer batch con un dict `_mat_lookup`:
```python
_mat_lookup = {(e["material"], float(e["espesor_mm"])): e for e in _mat_table.list()}
```
Permite calcular recursos correctamente en órdenes multi-material.

### `legacy_result_raw`
`len(batches)` → `len(all_batches)`

### Persistencia en `last_generate.json`
```python
"batches": all_batches,   # nuevo: almacenado para futuras reactivaciones
"lineas": _output_lineas, # path nuevo: solo _new_lineas; legacy: _base_lineas + _new_lineas
```

### Legacy fallback (sin cambio conceptual)
```python
if not _base_batches and _base_dxf_path and _base_lineas:
    _merge_dxf_append(Path(_base_dxf_path), dxf_path)
```

### `render_presupuesto`
```python
"batches": gen.get("batches", []),  # nuevo campo en PRES_NNNN.json
```

### `_handle_presupuesto_reactivar`
```python
"base_batches": data.get("batches", []),  # carga batches del presupuesto guardado
```

---

## Fix auxiliar: test `test_base_lineas_prepended_to_new_lineas_on_generate`

El test prueba el path legacy: `last_generate.json` tiene `base_lineas` pero no `base_batches`.
El código producía `lineas = _new_lineas` solamente, perdiendo los datos de paneles viejos.

Fix: para el path legacy, `_output_lineas = _base_lineas + _new_lineas`.
Para el path nuevo: `_output_lineas = _new_lineas` (todos recalculados desde `all_batches`).

---

## Verificación

- 56 tests passed
- 10 errores pre-existentes (PermissionError WinError 5 en pytest temp de Windows)
- Sin regresiones
