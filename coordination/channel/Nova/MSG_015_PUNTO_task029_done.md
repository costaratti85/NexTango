# MSG_015_PUNTO_task029_done

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-18  
**Re:** TASK_029 — Thumbnail Philo + sobreescritura del original — completada

---

## Diagnóstico

**DXF original**: perdido. Nunca fue commiteado a git. No es recuperable.

**Dos bugs encontrados** (independientes pero relacionados en el síntoma):

### Bug 1 — Thumbnail en blanco (1,292 bytes)

`_render_panel_thumbnail()` corría el motor legacy sobre el DXF original de splines → motor no importa SPLINE → `result_items = []` → matplotlib renderizaba figura vacía → PNG blanco de 1,292 bytes → **el método devolvía `out_path` (éxito) aunque el render estuviera vacío**. Fallback a `_render_dxf_thumbnail` nunca se activaba.

### Bug 2 — Sobreescritura silenciosa del original

`_handle_convert_splines()` no verificaba si el nombre ya existía en la librería antes de escribir el DXF. Constantino borró `(convertido)` del nombre → el sistema sobreescribió `Philo_editado.dxf` sin advertir.

---

## Fixes en `panel_sales_local_app.py`

1. **`_render_panel_thumbnail`**: `if not result_items: return None` → activa fallback para DXFs con splines
2. **`_handle_convert_splines` (servidor)**: verifica colisión en `pattern_library.json` antes de guardar; devuelve `{"ok": False, "exists": True}` en 409
3. **`confirmAndLoad` (JS cliente)**: cuando recibe `d.exists`, muestra `confirm()` explícito advirtiendo que el original se perderá; re-envía con `force: true` si el usuario acepta

## Acción directa

- Thumbnail en blanco eliminado
- Regenerado correctamente: `Philo.png` = 56,730 bytes ✓

## Nota para Constantino

El DXF original de Philo (con splines) fue sobreescrito y no se puede recuperar. La versión convertida (ARC+LINE) es la que está disponible. A partir de ahora, el sistema pedirá confirmación explícita antes de reemplazar cualquier patrón existente.

**Reporte:** `coordination/reports/PUNTO_TASK_029_REPORT.md`
