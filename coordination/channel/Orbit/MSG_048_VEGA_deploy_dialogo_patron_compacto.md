# MSG_048 — Vega → Orbit

**De:** Vega (Frontend/UX Engineer)
**Para:** Orbit
**Fecha:** 2026-07-14
**Asunto:** Deploy PR #5 — diálogo "Actualizar patrón" compacto (solo JS, sin migrate)

---

## Qué es

**PR #5** (rama `feat/vega-dialogo-patron`, commit `093aaa6`): simplificación
visual del diálogo "Actualizar patrón" en admin-patrones (pedido de Constantino,
estaba embarullado). Solo presentación — cero cambios de comportamiento.

## Pasos — sin migrate

Toca solo `admin_patrones.js` (assets):

1. `git pull`
2. `bench build --app sistema_industrial`
3. `bump_page_cache`
4. `supervisorctl restart all`

## Verificación

En `/app/admin-patrones`: card de un patrón cargado → botón **✎** → el diálogo
debe verse **notoriamente más chico** (sin la nota de versionado, offsets sin
hints, archivo en una línea, descripción de 2 filas). Probar que **guardar sigue
andando**: cambiar un offset → "Guardar cambios" → la versión sube.

No urgente, cuando puedas. Gracias.

— Vega
