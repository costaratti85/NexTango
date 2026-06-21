# Investigación: pipeline DXF roto — fallas reportadas por Constantino

**Fecha:** 2026-06-20  
**Ref:** MSG_021 — investigación urgente

---

## Resultado del test end-to-end

El pipeline básico funciona correctamente:

```
Batch 1 (500x300) → 1 item, w=500, h=300, geom_count=17
Batch 2 (800x400) → 1 item, w=800, h=400, geom_count=43
Total: 2 items, 63 arranged, DXF 34KB — OK
```

El bug NO está en el motor de generación. Está en la gestión del estado de reactivación.

---

## Causa raíz única: `_handle_cancel_reactivar` no limpiaba `base_batches`

**Archivo:** `panel_sales_local_app.py`, `_handle_cancel_reactivar`

**Flujo que produce los 3 síntomas:**

1. Usuario genera presupuesto_001 con `batch_A` (ej: Tresbolillo 500×300, espesor 1.25mm)
2. Usuario hace "Reactivar presupuesto_001"
   - `last_generate.json` queda con `"base_batches": [batch_A]`
3. Usuario hace "Cancelar reactivar"
   - El handler popeaba `reactivated_from` y `base_lineas` pero **NO** `base_batches`
   - `last_generate.json` todavía tiene `"base_batches": [batch_A]` ← STALE
4. Usuario hace generate fresco con `batch_B` (500×300) y `batch_C` (800×400)
   - `_run_all_batches` lee `_base_batches = [batch_A]` del last_generate.json
   - `all_batches = [batch_A, batch_B, batch_C]` ← 3 batches en lugar de 2

**Por eso:**
- **Medidas incorrectas**: el usuario submitió 500×300 + 800×400 pero obtiene 3 paneles: 500×300 (stale), 500×300 (nuevo), 800×400 (nuevo). Dos miden igual.
- **Paneles apilados**: si `batch_A` (stale) tiene material/espesor distinto al batch nuevo, cae en grupo distinto → fila distinta → apilado vertical en el DXF.
- **DXF vacío**: si `batch_A` tenía `panel_mode="none"`, su `geometry_items = []` (el tresbolillo artificial no entra en la chapa) → el panel stale no agrega geometría, el DXF solo tiene labels de texto.

---

## Análisis de las otras hipótesis

| Hipótesis | Descartada por |
|---|---|
| Settings compartido entre batches | `Settings()` crea instancia limpia cada vez, verificado |
| Bug en `arrange_cad_result_items` | Paneles mismo material+espesor → mismo grupo → lado a lado, correcto |
| Excepción silenciosa en loop de batches | Loop no tiene try/except, excepciones burbujean al handler |
| Módulos cacheados con estado global | No hay estado global en `main.py` o `Settings` |
| `import_module` reutiliza módulo con estado | Verificado: los módulos son stateless |

---

## Fix aplicado

`_handle_cancel_reactivar` — agregar `data.pop("base_batches", None)`:

```python
def _handle_cancel_reactivar(self) -> None:
    ...
    data.pop("reactivated_from", None)
    data.pop("base_lineas", None)
    data.pop("base_batches", None)  # ← AGREGADO
```

---

## Verificación

- 56 tests passed, 10 errores pre-existentes (permisos Windows temp)
- Sin regresiones

---

## Nota sobre "DXF vacíos" con panel_mode="none"

`panel_mode="none"` (sin perforar) SIEMPRE genera `geometry_items = []` porque el tresbolillo artificial tiene `step_x >> usable_width`. El DXF resultante solo tiene labels de texto (nombre y cantidad). Si Constantino espera ver geometría de corte para "sin perforar", eso requiere un feature separado (sheet_outline), no está en scope.
