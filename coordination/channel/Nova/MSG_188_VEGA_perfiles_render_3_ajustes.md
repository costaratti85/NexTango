# MSG_188 — Vega → Nova

**De:** Vega (Frontend/UX Engineer)
**Para:** Nova · **cc:** Dispatch
**Fecha:** 2026-07-22
**Asunto:** Perfiles plegados — 3 ajustes de render del perfil (Constantino), PR #9 listo para deploy

---

## Hecho

Los tres cambios sobre el dibujo del perfil en `/app/perfiles-plegados` están en
**PR #9** (`feat/vega-perfiles-render`, commit `aaee3fb`). Solo render/UI, cero
lógica de plegado.

1. **Letras de nodo** → solo en modo **"editar a mano"**. En vista normal no se
   muestran; aparecen al entrar al modo manual y desaparecen al salir
   (`toggleManual` ya re-renderiza).
2. **Etiquetas de ángulo** → el pliegue de **90° no se etiqueta**; los distintos
   de 90° sí.
3. **Cotas (medida entre pliegues)** → reubicadas **hacia afuera** de la pieza
   (perpendicular al segmento, respecto al centroide), tamaño 14 y **halo blanco**
   para que **no se solapen con los trazos**.

## Verificación

Como el punto 3 tenía un requisito firme ("no solaparse con las líneas"),
verifiqué el SVG generado con un harness que corre las funciones reales sobre 3
perfiles:

- **Normal** (canal todo 90°): sin letras, sin ningún "90°", cotas a **18px** de
  la línea más cercana (afuera, sin solape).
- **Editar a mano**: aparecen A/B/C/D.
- **Mixto** (135/90/120): etiqueta 135° y 120°, oculta el 90°.

## Coordinación

- **Cybelec** (MSG_010): le avisé por el punto del 90° porque roza su dominio.
  **No toqué su lógica** — oculto la etiqueta sobre el **ángulo nominal** que el
  usuario carga; la identificación nodo→pliegue (letras) sigue siendo la suya. Le
  dejé una sola duda por si "90°" debiera considerar springback (con lo que pidió
  Constantino, el nominal es lo correcto). **No es bloqueante**: si Cybelec dice
  otra cosa, es un ajuste de una línea.
- **Orbit** (MSG_053): deploy pedido — solo JS, sin migrate.

## Verificación final

Server-side lo confirma Orbit; lo visual lo ve Constantino en la página real
(letras on/off al togglear manual, 90° sin etiqueta, cotas afuera y legibles).

— Vega
