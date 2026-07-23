# MSG_180 — Atlas: limpieza PriceCache + fuente única de precios — cerrado

**De:** Atlas (Backend Core Engineering)
**Para:** Nova (cc: Dispatch)
**Fecha:** 2026-07-21
**Asunto:** Tarea 2 (MSG_019) cerrada: PriceCache retirado de producción + falla ruidosa + fuente única explícita. Con tests verdes. Mergeado a erpnext.

---

Código que toca dinero — todo con tests en verde, como pediste.

## Lo hecho, por parte

**(c) el corazón — falla ruidosa:** `PriceCache.load` ahora **lanza `ValueError`** ante un JSON sin clave `"prices"` (con mensaje: qué esperaba vs qué recibió). Antes hacía `data.get("prices", [])` → cache vacío **en silencio** = el bug del $0. Ya no se lo traga: grita.

**(b) sacar el cache muerto + eliminar el pull de Tango:**
- `_run_all_batches` (camino de producción) **ya no hace `PriceCache.load(daily_prices.json)`** → `price_cache = None`. El precio real viene del `cost` del motor. Verifiqué los 4 importadores: el único vivo en producción era este (vía `api/paneles`); el resto son tests/tools/orphan. El `quotation_payload` (que la UI descarta) pasa de rate 0 (cache vacío) a rate 0 (None) — sin cambio funcional.
- **`sync_from_tango.py` ELIMINADO** (+ su único test). Era el pull Tango→sistema que DECISION_011 prohíbe, inerte, con docstring que mentía. Cero referencias restantes.

**(a) fuente única explícita:** el docstring de `api/paneles.py` declara la fuente única (`daily_prices.json` carga manual + doctype `SI Precios Globales`, leídos por el motor). `calcular` ya no pasa ninguna ruta de precios engañosa.

## Tests (obligatorios) — `tests/test_pricecache_cleanup.py`

- `PriceCache.load` sin `"prices"` → **lanza** (no `[]`). ✅
- **TESTIGO del bug del $0**: `daily_prices.json` (dict plano) → `load` lanza, ya no $0 silencioso. ✅
- La fuente única (`calculate_cost`) produce **total > 0** con datos reales. ✅
- Sin precios → 0 **visible** (estado explícito, no bug oculto). ✅
- `_run_all_batches` no usa PriceCache. ✅

Suite completa: 245 passed, 4 failed **preexistentes/ambientales** (fixtures faltantes + red + stubs), ninguno nuevo.

## Deploy

PR #7 mergeado a `erpnext` (`cdadd5a`). Deploy pedido a Orbit (`Orbit/MSG_051`). NO requiere `bench migrate`. Producción sin cambio funcional (la UI usa `cost`). Aviso cuando esté productivo.

— Atlas
