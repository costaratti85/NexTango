# PUNTO_TASK_036 — Bug DXF multi-panel: panel duplicado, panel faltante

**Fecha:** 2026-06-20  
**Estado:** Completada

---

## Síntoma

Presupuesto 0017 (Subte 550×550 + Cosmos 300×300):
- Subte **ausente** en el DXF compilado
- Cosmos aparece **dos veces**

---

## Causa raíz

En `_run_all_batches()` (`panel_sales_local_app.py`), el `base_dxf_path` (ruta del DXF
del presupuesto anterior, usado para el merge por reactivación) se leía de
`last_generate.json` **después** de que el nuevo DXF ya había sido escrito:

```
línea 1431: exporter.save(arranged, str(dxf_path))   ← DXF nuevo escrito
...
línea 1589: _prev = json.loads(LAST_GENERATE_FILE...)  ← base_dxf_path leído AQUÍ
línea 1612: _merge_dxf_append(Path(_base_dxf_path), dxf_path)
```

Cuando el presupuesto anterior y el nuevo comparten el mismo `customer` + `job_name`,
ambos producen el mismo `order_id` → mismo `dxf_path`. Al momento de leer
`base_dxf_path`, el archivo ya fue sobreescrito con el contenido nuevo.

`_merge_dxf_append(base_path, new_path)` recibe `base_path == new_path`, lee el
archivo dos veces (ambas en memoria con el contenido nuevo), y appenda el contenido
nuevo sobre sí mismo. Resultado:
- El panel que estaba en el base DXF (Subte) → **perdido** (el archivo fue sobreescrito)  
- El panel nuevo (Cosmos) → **duplicado** (merged into itself)

---

## Fix

**Archivo:** `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`

Mover la lectura de `base_lineas` y `base_dxf_path` al **inicio** de `_run_all_batches`,
antes de cualquier generación de DXF. Eliminar la lectura tardía que estaba dentro del
bloque `try:` de persistencia de `last_generate.json`.

```python
def _run_all_batches(...):
    # Leer ANTES de generar el DXF
    _base_lineas: list = []
    _base_dxf_path: str = ""
    try:
        if LAST_GENERATE_FILE.exists():
            _prev = json.loads(LAST_GENERATE_FILE.read_text(encoding="utf-8"))
            _base_lineas = _prev.get("base_lineas", [])
            if _base_lineas:
                _base_dxf_path = _prev.get("dxf_path", "")
    except Exception:
        pass

    price_cache = ...  # resto de la función sin cambios
```

El bloque duplicado (que leía lo mismo después de escribir el DXF) fue eliminado.

---

## Verificación

- 36 tests passed (+ 4 errores pre-existentes de permisos Windows en carpeta temp)
- La lectura de `base_dxf_path` ahora siempre ocurre antes de que el DXF sea escrito
- Si `base_dxf_path == dxf_path`, el merge ahora lee el archivo correcto (contenido previo),
  no el ya-sobreescrito
