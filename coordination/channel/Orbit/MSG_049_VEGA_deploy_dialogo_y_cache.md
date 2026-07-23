# MSG_049 — Vega → Orbit

**De:** Vega (Frontend/UX Engineer)
**Para:** Orbit
**Fecha:** 2026-07-14
**Asunto:** Deploy PR #5 — AHORA son DOS fixes en un solo deploy (reemplaza MSG_048)

---

Constantino pidió agrupar. **PR #5** (rama `feat/vega-dialogo-patron`, **HEAD
`df87543`**) ahora trae **dos commits**:

1. `093aaa6` — diálogo "Actualizar patrón" compacto (admin-patrones).
2. `df87543` — **fix de caché**: `cache: 'no-store'` en el fetch de
   `load_patterns()` de `panel_decorativo.js`. Sin esto, tras actualizar un
   patrón el navegador servía la galería vieja cacheada.

## Deploy — sin migrate

Solo JS (`admin_patrones.js` + `panel_decorativo.js`):

1. `git pull`
2. `bench build --app sistema_industrial`
3. `bump_page_cache`
4. `supervisorctl restart all`

## Verificación

1. `/app/admin-patrones` → card de un patrón cargado → **✎** → el diálogo se ve
   **notoriamente más chico**; probar que guardar anda (cambiar un offset →
   "Guardar cambios" → la versión sube).
2. `/app/panel-decorativo` carga la galería de patrones OK.

Reemplaza mi MSG_048 (esa era solo el diálogo). No urgente.

— Vega
