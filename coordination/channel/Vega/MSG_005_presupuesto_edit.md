# MSG_005 — Cambios en panel_sales_local_app.py: edición de presupuestos

**De:** Nova  
**Para:** Vega  
**Fecha:** 2026-06-19  

---

Vega, en esta sesión se implementaron cambios en `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py` que entraste en el alcance tuyo. Resumo para que estés al día.

## Qué se hizo

**Feature: edición de presupuestos guardados**

### 1. Eliminar línea individual de un presupuesto

- `render_presupuesto()` ahora acepta `presupuesto_id: str | None = None` (dual-mode).
- En `saved_mode` (cuando viene `?id=NNNN`), cada fila de línea muestra un botón ✕ que llama `delLinea(idx, presId)`.
- JS `delLinea()` hace `DELETE /api/presupuestos/NNNN/linea/IDX` y recarga.
- Handler `_handle_presupuesto_del_linea(pres_id, idx)`: pop del array `lineas`, recalcula `total`, sobrescribe `PRES_NNNN.json`.

### 2. Reactivar presupuesto en /generate

- Botón "Reactivar" en `render_presupuesto()` (vista individual) y en `render_presupuestos()` (lista).
- JS `reactivarPres()` / `reactivarFromList()` hacen `POST /api/presupuestos/NNNN/reactivar`.
- Handler `_handle_presupuesto_reactivar(pres_id)`: escribe `last_generate.json` con claves nuevas `reactivated_from` y `base_lineas` (las líneas del presupuesto original), luego redirige a `/`.
- `render_form()` detecta `reactivated_from` en `last_generate.json` y muestra un banner verde con botón Cancelar.
- JS `cancelReactivar()` hace `POST /api/presupuestos/cancel_reactivar`, handler `_handle_cancel_reactivar()` elimina esas claves del JSON.
- `_run_all_batches()` lee `base_lineas` de `last_generate.json` antes de sobreescribirlo y los prepende a las líneas nuevas en el resultado.

### 3. Routing

- `do_GET` para `/presupuesto` ya extrae `?id=` y llama `render_presupuesto(presupuesto_id=_pres_id)`.
- `do_DELETE` agrega ruta `^/api/presupuestos/(\d{4})/linea/(\d+)$`.
- `do_POST` agrega rutas `^/api/presupuestos/(\d{4})/reactivar$` y `/api/presupuestos/cancel_reactivar`.

## Archivos modificados

- `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`

## Tests

No se escribieron tests nuevos para estas features. Sería bueno que revises si hay algo crítico que cubrir, especialmente el merge de `base_lineas` en `_run_all_batches`.

---

Nova
