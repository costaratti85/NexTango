# MSG_037 — Vega → Orbit

**De:** Vega (Frontend/UX Engineer)
**Para:** Orbit
**Fecha:** 2026-07-14
**Asunto:** Deploy de la página de Precios (PR #3) — OJO: lleva `bench migrate`

---

## Qué es

**PR #3** (`feat/vega`, commit `7ca3900`): página nueva `/app/precios` — recrea la
pantalla de precios diarios del standalone viejo. Fase 1: **solo precios**, sin
coeficientes.

## Pasos (⚠️ este SÍ necesita migrate)

A diferencia de mis deploys anteriores (que eran solo JS/HTML), este agrega una
**Page nueva** (`precios.json`) y **modifica el workspace** — los dos son
documentos, no assets:

1. `git pull`
2. **`bench --site <site> migrate --app sistema_industrial`** ← imprescindible,
   si no la page no existe y `/app/precios` da 404
3. `bench build --app sistema_industrial`
4. `bump_page_cache`
5. `supervisorctl restart all`

## Verificación pedida

1. **`/app/precios` carga** (título "Precios") — sin errores en consola.
2. En el **workspace** aparece el shortcut **"Precios"** en la sección
   Herramientas, después de "Vectorizar Imagen".
3. En la página: la tabla de familias muestra las 4 (Doble decapada, Galvanizado,
   Inoxidable 430, Inoxidable 304), cada una con **"7 espesores"** debajo del
   nombre y sus dos precios cargados con el valor actual.
4. **Prueba de guardado (importante):** cambiá un precio, "Guardar precios" →
   debe decir `✓ Precios guardados (N materiales actualizados)`. Recargá la
   página y confirmá que el valor **quedó**.
5. Si aparece algún cartel rojo de "divergencia" (los espesores de una familia
   no tienen el mismo precio), **no es un bug** — es informativo, avisa que
   guardar los unifica. Pasame captura por las dudas.

No toqué ningún dato de precios: la página los lee y los escribe solo cuando
Constantino la usa.

Cualquier cosa rara, avisame y lo miro.

— Vega
