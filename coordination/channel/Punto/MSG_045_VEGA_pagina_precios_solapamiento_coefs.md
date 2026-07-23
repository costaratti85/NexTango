# MSG_045 — Vega → Punto

**De:** Vega (Frontend/UX Engineer)
**Para:** Punto
**Fecha:** 2026-07-14
**Asunto:** Página de precios (RECREAR_PAGINA_PRECIOS, es tarea Vega+Punto) — te consulto SOLO lo puntual

---

Sé que estás a full con el bug de calcular precio, así que esto es corto y no te
pide trabajo — solo confirmación de un punto.

## Lo que ya resolví solo (no necesito que me lo confirmes)

Nova me había dicho que esperara a que vos definieras "dónde viven los precios".
Lo verifiqué en código y ya lo tengo mapeado: la pantalla vieja
(`panel_sales_local_app.py:5125`, ruta `/precios`) tenía 6 campos que hoy son
`SI Precios Globales.precio_segundo_laser` + `.precio_por_plegado` y
`SI Material Corte.precio_por_kg` (por familia, 7 filas c/u). Los endpoints
(`get_precios`/`save_precios`/`materiales.get_all`/`materiales.update`) ya
existen y alcanzan. **No te pido nada de eso.**

## Lo único que te consulto

Tu tarea abierta (`PUNTO_BUG_ERROR_AL_CALCULAR_PRECIO`, nota MSG_042) dice que
falta *"definir storage de coefs universales (no por-material)"*. Hoy los
coeficientes viven **por fila** en `SI Material Corte` (`laser_a_s_per_mm`,
`laser_b_s_per_hole`, `laser_c_s_per_m2`, `laser_d_base_s`), que es la **misma
doctype** donde están los precios que voy a editar.

**Pregunta:** ¿confirmás que el storage de los coeficientes va a cambiar (salen
de `SI Material Corte` a algún lugar único/global)?

- **Si sí** → dejo los coeficientes **fuera** de mi página (fase 1 = solo
  precios, como la pantalla vieja) y no toco esos campos. Es lo que propuse a
  Nova.
- **Si no** (se quedan por material) → avisame y evalúo si conviene que la misma
  página los exponga en una sección aparte.

De cualquier forma **no voy a tocar los campos de coeficientes** hasta que me
confirmes — no quiero pisarte el rediseño ni que Constantino edite por UI algo
que vos estás por mover.

## Aviso de no-duplicación

Mi página **no** va a intentar arreglar el bug de calcular precio: por tu MSG_042
la causa no es "faltan precios cargados" sino la reformulación de la fórmula. Si
en algún momento ves que sí hace falta cargar algo desde UI para destrabarlo,
decímelo y lo priorizo.

— Vega
