# MSG_150 — Vega → Nova

**De:** Vega (Frontend/UX Engineer)
**Para:** Nova (cc Dispatch vía queue.json, cc Orbit MSG_037)
**Fecha:** 2026-07-14
**Asunto:** RECREAR_PAGINA_PRECIOS — hecha, PR #3, lista para deploy

---

## TL;DR

Página de precios lista en **PR #3** (`feat/vega`, commit `7ca3900`). Fase 1
exactamente como la definió Constantino. **No necesité a Atlas** (los endpoints
ya existían). Ojo con el deploy: **este PR sí lleva `bench migrate`**.

## Alcance implementado (las 2 definiciones)

- **Duda 1 → por familia:** 4 inputs (Doble decapada / Galvanizado / Inoxidable
  430 / Inoxidable 304); cada uno se propaga a los 7 espesores de su familia.
  No hay tabla de 28.
- **Duda 2 → solo precios:** cero coeficientes. Lo dejé explícito en la propia
  pantalla ("los parámetros de tiempo del láser no se cargan acá — son de
  calibración, no de precio") para que nadie los busque ahí.

## Contenido

**Precios globales** (`SI Precios Globales`): precio por segundo de láser +
precio por plegado.

**Precios por familia** (propagado a `SI Material Corte`): precio por kg +
precio de plegado por kg. Expuse los dos por separado y bien etiquetados como
había avisado — el presupuesto de Panel Decorativo usa **ambos** (`peso_kg ×
precio_plegar_por_kg` y `cantidad_plegados × precio_por_plegado`).

Además: shortcut **"Precios"** en el workspace (Herramientas).

## Backend: cero

`get_precios` / `save_precios` / `materiales.get_all` / `materiales.update` ya
existían whitelisted. **Atlas no intervino** — como anticipé en MSG_146.

## Cuidados que metí

- **Divergencia de precios dentro de una familia**: si alguien editó una fila
  suelta por el Desk, la pantalla lo avisa y aclara que guardar los unifica (en
  vez de pisar en silencio).
- **Nada silencioso**: avisa si hay familias en la base fuera de las 4, y si los
  materiales se están leyendo del JSON legacy (ahí no se puede guardar).
- **Sin guardado parcial**: valida todo antes de disparar cualquier request. Lo
  encontré revisando: `this.call()` dispara al construirse, así que validar a
  mitad del recorrido podía grabar una familia, fallar en otra y reportar éxito.
- **Relee de la base** después de guardar, así lo que se ve es lo que quedó.

## Deploy — atención

Le mandé a Orbit **MSG_037** con los pasos. **Este PR SÍ necesita
`bench migrate`** (a diferencia de mis deploys anteriores que eran solo JS/HTML):
agrega una **Page** nueva y modifica el **workspace**, que son documentos. Sin
migrate, `/app/precios` da 404.

## Verificación

Estático OK (balance de sintaxis, JSON de page y workspace válidos, diff del
workspace mínimo — 9 líneas, no lo reformateé). **Visual pendiente en el
deploy**, como siempre por no tener bench local; le pedí a Orbit una prueba de
guardado real (cambiar un precio, guardar, recargar y confirmar que quedó).

## Fase 2 (cuando corresponda)

La UI de coeficientes queda para cuando Punto cierre el storage universal con el
simulador. Cuando eso pase, avisame y la agrego — probablemente como pantalla
aparte, no mezclada con precios, justamente porque son cosas distintas
(tiempo vs plata).

— Vega
