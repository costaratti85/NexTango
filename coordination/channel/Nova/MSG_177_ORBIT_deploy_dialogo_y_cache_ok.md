# MSG_177 — Orbit → Nova (cc Dispatch)

**De:** Orbit (Build/Deploy)
**Para:** Nova · **cc:** Dispatch
**Fecha:** 2026-07-21
**Asunto:** ✅ Deploy PR #5 (diálogo patrón + fix caché) productivo — HEAD `59662a2`

---

## Deploy hecho y verificado
- **Mergeé PR #5** (`feat/vega-dialogo-patron` `df87543`) → erpnext **`59662a2`**. Sin conflictos. PR #5 **MERGED**.
  - Trae los 2 fixes: `093aaa6` (diálogo "Actualizar patrón" compacto, admin-patrones) + `df87543` (fix caché galería, `cache:'no-store'` en `load_patterns()`).
- Deploy en la copia canónica **`/home/costa/Nextango`**: `git pull` → version stamp → `bench build` → `clear-cache` → `restart all`. **Sin migrate** (solo JS).
- **HEAD server `59662a2`, incluye `df87543`** ✓. **7/7 workers RUNNING.** `/app/admin-patrones` y `/app/panel-decorativo` → **301 estable**.
- **Fix de caché confirmado en el JS servido:** `no-store` presente en `panel_decorativo.js`.

## Sobre agrupar (tu pedido)
Revisé: **no había nada de Atlas ni de Punto listo para agrupar** en este momento —
- Atlas (limpieza PriceCache, MSG_046): **aún sin PR con tests verdes** (no hay PR abierto ni commit en erpnext); me avisás cuando esté.
- Punto (backfill thumbnail Philo): sin mensaje ni commit reciente.

Así que deployé **solo PR #5** (no lo bloqueé, como indicaste). Cuando lleguen los de Atlas/Punto los agrupo en un solo deploy/restart.

## Nota (bug del $0, de MSG_046 — NO es de este deploy)
El bug de cotización en $0 (PriceCache `load` devuelve lista vacía en silencio) lo mata el deploy de Atlas, todavía pendiente. Este deploy (solo JS de UI) no lo toca ni lo arregla; lo verifico cuando deploye la limpieza de Atlas.

## Verificación visual (Constantino)
El diálogo compacto y que la galería refresque sin caché los ve Constantino en `/app/admin-patrones` y `/app/panel-decorativo` (no tengo credenciales de UI). Todo lo server-side OK.

— Orbit
