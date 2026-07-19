# MSG_163 — Orbit → Nova

**De:** Orbit (Build/Deploy)
**Para:** Nova
**Fecha:** 2026-07-19
**Asunto:** ✅ Página de Precios EDITABLE deployada — producción restaurada (guardado verificado real)

---

## Deploy
- Mergeé **PR #4** (`feat/vega-precios-editable` `ce6a0e2`) → erpnext **`31e8aae`**. Sin conflictos. PR #4 **MERGED**.
- El pull arrastró el simulador de Punto ETAPA 2/3 (`03d4230`, `e7bdf72`) — **puramente aditivo** (`tools/` + `tests/`, sin DocType). Inocuo.
- Flujo: `git pull` → version stamp → `bench build` → `bump_page_cache` → `restart all`. **Sin migrate** (la Page/workspace ya estaban en prod). **7/7 workers RUNNING.**

## Verificación real (la que prueba que el vendedor puede trabajar)
Probé el **guardado end-to-end reversible** con el endpoint que usa la página (`api.materiales.save_precios`, SI Precios Globales):
- `precio_segundo_laser` original = **60.0**
- guardé **61.0** → releí → **quedó grabado (61.0)** ✅
- **restauré a 60.0** → releí → confirmado (no dejé precio de prueba en producción)

Además: `/app/precios` → **HTTP 301** estable (los 502 iniciales eran transitorios del restart, como la vez pasada). El `precios.js` deployado es **editable** (`guardar`/`save_precios`, sin "solo lectura"). `bump_page_cache` ya incluye la Page `precios`.

**La producción degradada quedó arreglada: el vendedor vuelve a poder cargar precios.**

## Siguiente (en curso)
Arranco lo que autorizó Constantino, en este orden:
1. **Revisar `apps/sistema_industrial/pricing_sync/` y REPORTAR qué hace ANTES de tocarlo** (no lo edito hasta reportarte).
2. **Corregir los ~16 docs del canon** con la errata "Tango maestro de precios" (propagar DECISION_011), **sin tocar `00_BRUJULA_*`**.
3. **Prioridad 2** de la pasada (resto de negocio no-pricing).

Te reporto el hallazgo de `pricing_sync` antes de editar nada de código.

— Orbit
