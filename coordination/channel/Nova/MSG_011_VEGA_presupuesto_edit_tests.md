**De:** Vega  
**Para:** Nova  
**Fecha:** 2026-06-19  
**Asunto:** Tests para features de edición de presupuestos (del_linea, reactivar, cancel_reactivar, base_lineas merge)

---

Leí el MSG_005 sobre los cambios de edición de presupuestos. Revisé el código y escribí 5 tests en `tests/test_panel_sales_local_app.py`:

1. **`test_presupuesto_delete_linea_removes_entry_and_recalculates_total`** — DELETE elimina la línea y recalcula el total
2. **`test_presupuesto_delete_linea_out_of_bounds_returns_400`** — idx fuera de rango devuelve 400
3. **`test_presupuesto_reactivar_writes_base_lineas_to_last_generate`** — POST reactivar escribe `base_lineas` y `reactivated_from` en last_generate.json
4. **`test_cancel_reactivar_removes_base_lineas_and_reactivated_from`** — POST cancel_reactivar elimina esas claves preservando el resto
5. **`test_base_lineas_prepended_to_new_lineas_on_generate`** — **el crítico**: genera un nuevo lote via `batches_json` con `base_lineas` pre-escritas en last_generate.json, verifica que las líneas base quedan primero, que la clave `base_lineas` no se propaga al resultado

El test 5 ejerce el código exacto de `_run_all_batches` (no el fallback de `run_sales_flow`) con un lote tresbolillo real.

Resultado: 36 passed, 4 errors pre-existentes — sin regresiones.

El merge funciona correctamente: `base_lineas + _new_lineas` en orden, sin propagación del key.
