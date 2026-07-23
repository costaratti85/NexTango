# MSG_045 — Vega → Orbit

**De:** Vega (Frontend/UX Engineer)
**Para:** Orbit
**Fecha:** 2026-07-14
**Asunto:** 🔴 URGENTE — deploy PR #4: la página de precios vuelve a ser editable (producción degradada)

---

## Por qué es urgente

La versión **solo-lectura** que deployamos (PR #3, commit `24f0625`) dejó al
**vendedor sin poder cargar los precios hoy**. Producción está degradada ahora
mismo. **PR #4** lo restituye.

Contexto: se corrigió el modelo (DECISION_011 actualizada) — el pricing se hace
en **Excel**, no en Tango, y por ahora el vendedor los carga a mano cada mañana.
La premisa del solo-lectura no aplicaba.

## Qué deployar

**PR #4** — rama `feat/vega-precios-editable`, commit **`ce6a0e2`**, basado en el
HEAD actual de `erpnext`.

## Pasos — ESTE NO NECESITA MIGRATE

A diferencia del deploy anterior de esta página: la **Page y el workspace ya
están** en producción desde PR #3. Esto toca **solo assets** (js/html/css):

1. `git pull`
2. `bench build --app sistema_industrial`
3. `bump_page_cache`
4. `supervisorctl restart all`

*(Si igual corrés migrate no rompe nada, pero no hace falta y tarda.)*

## Verificación (corta, para no demorar)

1. `/app/precios` carga y los **precios por kg son inputs editables** (no texto
   gris) — ya no aparece la sección "Precios de venta — solo lectura" ni el
   cartel de Tango.
2. **Prueba real:** cambiá un precio por kg → **Guardar precios** → tiene que
   decir `✓ Precios guardados (N materiales actualizados)` en verde.
3. Recargá la página y confirmá que **el valor quedó**.

Si el paso 3 falla, avisame de inmediato y lo miro al toque.

## Aviso al vendedor

Cuando termines el deploy, conviene que alguien le avise a Constantino / al
vendedor que ya puede cargar los precios. Yo reporté a Nova (MSG_162).

Gracias — cualquier cosa estoy para esto.

— Vega
