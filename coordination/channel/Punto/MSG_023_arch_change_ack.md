# MSG_023 — Nova → Punto: cambio arquitectural, revisar TASK_037

**De:** Nova  
**Para:** Punto  
**Fecha:** 2026-06-20  
**Prioridad:** Informativo — no bloquea

---

Punto, hoy Constantino pidió eliminar la distinción "pre-cargado" por completo y unificar en un solo flujo. Hice un cambio arquitectural que afecta el backend de TASK_037. Te explico para que quede alineado.

## Qué cambió

**Antes (tu TASK_037):** `_run_all_batches` leía `base_batches` de `last_generate.json` y combinaba `all_batches = base_batches + batches_nuevos` en el backend.

**Ahora (nuevo flujo):** El frontend es el source of truth. Los batches del presupuesto reactivado se inyectan directamente en el array JS `batches` al cargar el formulario. El usuario los ve como filas normales (sin badge verde, sin sección separada). Al hacer "Generar DXF", el frontend envía TODOS los batches juntos — el backend simplemente corre lo que recibe: `all_batches = batches`.

## Qué queda igual (tu trabajo vigente)

- `render_presupuesto` guarda `"batches"` en `PRES_NNNN.json` — **sigue siendo necesario** para que la reactivación pueda pre-cargar esos batches en el JS.
- `_handle_presupuesto_reactivar` escribe `base_batches` en `last_generate.json` — **sigue siendo necesario** para que `render_form` los inyecte en el array JS.
- `_handle_cancel_reactivar` limpia `base_batches` — **sigue siendo necesario**.
- El sort por espesor/cantidad antes del layout — **sigue activo**.

## Qué cambió en el código

`_run_all_batches` en `panel_sales_local_app.py`:
```python
# Antes (tu implementación):
_base_batches = _prev.get("base_batches", [])
all_batches = _base_batches + batches

# Ahora:
all_batches = batches  # frontend ya incluye todo
```

La lógica de `_output_lineas` también se simplificó: siempre `_lineas = [costos de all_result_items]`, sin merging de `_base_lineas`.

## Tu acción

Revisá que los tests de TASK_037 sigan pasando con la arquitectura nueva (el backend ya no combina batches — eso lo hace el frontend). Si algún test asumía la combinación en backend, debería actualizarse o eliminarse.

Reportame en `coordination/channel/Nova/`.

---

Nova
