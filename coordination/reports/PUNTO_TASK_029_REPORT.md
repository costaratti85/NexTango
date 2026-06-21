# PUNTO_TASK_029_REPORT — Thumbnail Philo + sobreescritura del original

**Agente:** Punto  
**Fecha:** 2026-06-18  
**Estado:** COMPLETADO

---

## Investigación

### 1. Estado del DXF original

El archivo `uploaded_patterns/Philo_editado.dxf` (652,227 bytes) contiene únicamente ARC y LINE — es la versión convertida. El DXF original con splines **fue sobreescrito** y **no está en git** (los archivos de `outputs/` nunca fueron commiteados).

**Recuperación: no es posible.** El archivo original se perdió.

Hay un segundo archivo `Philo__convertido__editado.dxf` (652,420 bytes, también ARC+LINE) que corresponde a un guardado anterior del convertido.

### 2. Causa del thumbnail en blanco (1,292 bytes)

La secuencia fue:

1. `Philo_editado.dxf` tenía splines (original)
2. Al guardar el patrón convertido con nombre `"Philo"`, el sistema inició la regeneración del thumbnail en un thread
3. `_render_panel_thumbnail` corrió el motor legacy con el DXF de splines → el motor no puede importar SPLINE entities → `result_items = []`
4. Con `result_items` vacío, matplotlib renderizó una figura en blanco → **PNG de 1,292 bytes**
5. El bug: `_render_panel_thumbnail` devolvía `out_path` (éxito) aunque el render estaba vacío → **el fallback a `_render_dxf_thumbnail` no se activó**
6. El DXF fue sobreescrito con ARC+LINE justo después → pero el thumbnail ya tenía el blank

### 3. Causa de la sobreescritura del original

`_handle_convert_splines()` en el servidor:
```python
safe_name = re.sub(r"[^A-Za-z0-9_\-]", "_", name)
out_path = str(out_dir / f"{safe_name}_editado.dxf")
_entities_to_dxf(entities, out_path)  # sobreescribe sin advertir
add_pattern_to_library(...)            # actualiza la librería sin advertir
```

No había ninguna verificación de colisión de nombres. Cuando Constantino escribió `"Philo"` (borrando el sufijo `(convertido)`), el archivo original fue destruido silenciosamente.

---

## Fixes aplicados

### Fix 1 — `panel_sales_local_app.py`: fallback cuando motor produce nada

En `_render_panel_thumbnail()`, después de obtener `result_items`:
```python
if not result_items:
    # Motor produced nothing (DXF has only splines/unsupported entities).
    # Signal caller to fall back to _render_dxf_thumbnail.
    return None
```

Ahora si el motor falla silenciosamente (DXF con splines → empty result), se activa `_render_dxf_thumbnail` que sí maneja SPLINE via `e.flattening()`.

### Fix 2 — `panel_sales_local_app.py`: detección de colisión en conversor

En `_handle_convert_splines()`, antes de escribir el DXF:
```python
force = bool(data.get("force", False))
if not force:
    # Lee pattern_library.json directamente para evitar import del motor
    lib_path = find_legacy_panel_dir() / "pattern_library.json"
    if name in existing_patterns:
        return 409 {"ok": False, "exists": True, "error": "..."}
```

### Fix 3 — JS `confirmAndLoad()`: confirmación explícita antes de reemplazar

El cliente recibe `{"exists": True}` y muestra un `confirm()` nativo con el texto:

> "Philo" ya existe en la galería.
> ¿Reemplazar el patrón existente con la versión convertida?
> (El archivo original se perderá.)

Si el usuario confirma, re-envía con `force: true`. Si cancela, muestra aviso de "Elegí otro nombre."

### Fix 4 — Thumbnail en blanco eliminado y regenerado

- Eliminado `static/pattern_thumbnails/Philo.png` (1,292 bytes — blank)
- Regenerado directamente: `Philo.png` = 56,730 bytes ✓
- `_ensure_all_thumbnails()` en el próximo start del servidor también lo hubiera regenerado (ahora que el DXF tiene ARC+LINE y el fallback funciona)

---

## Verificación

```
generate_pattern_thumbnail('Philo', data)
→ Philo.png: 56,730 bytes ✓  (antes: 1,292 bytes — blank)
```

49 tests pasan. Errores pre-existentes (PermissionError Windows) sin cambio.

---

## Recuperación del DXF original

**No es posible.** Opciones futuras para prevenir pérdidas:

1. **Fix implementado**: conversor pide confirmación explícita antes de sobreescribir
2. **Recomendación adicional** (no implementado): antes de sobreescribir el DXF físico, hacer una copia de respaldo en `uploaded_patterns/backups/`
3. **Recomendación adicional** (no implementado): agregar los uploads a `.gitignore` negado (forzar tracking) — permite recuperar desde `git log`

---

## Resumen de bugs

| Bug | Causa | Fix |
|---|---|---|
| Thumbnail en blanco | Motor produce `result_items=[]` para DXF con splines; `_render_panel_thumbnail` devolvía éxito con imagen vacía | `return None` si `not result_items` → activa fallback `_render_dxf_thumbnail` |
| Sobreescritura silenciosa | `_handle_convert_splines` no verificaba si el nombre ya existía | Check en servidor + confirm en cliente con `force: true` |
