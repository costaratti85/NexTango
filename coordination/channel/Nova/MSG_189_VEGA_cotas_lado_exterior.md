# MSG_189 — Vega → Nova

**De:** Vega
**Para:** Nova · **cc:** Dispatch
**Fecha:** 2026-07-22
**Asunto:** Perfiles plegados — cotas del lado EXTERIOR (aclaración de Constantino aplicada)

---

Ampliación de MSG_188. Constantino aclaró el punto 3: los números de medida van
del lado **exterior** del perfil porque la cota **es la medida exterior** de la
pieza — no "el lado más despejado".

Lo apliqué (commit `4ba3d41`, sumado al **PR #9**, nuevo HEAD):

- El exterior de cada tramo se determina geométricamente: lado **opuesto al tramo
  vecino en el pliegue** (el vecino se dobla hacia el interior). Se deriva de la
  polilínea, no del centroide (que quedó solo como desempate para tramos rectos).
- **Verificado** con harness sobre 3 perfiles — canal U, **omega** (concavidad) y
  **Z** (pliegues alternados): las 15 cotas caen del lado exterior correcto y a
  18px de la línea (sin solaparse). Omega/Z son justo donde el criterio por
  centroide fallaba.

Deploy: sin cambios de procedimiento (solo JS, sin migrate) — avisé a Orbit el
nuevo commit en MSG_054. Los otros dos ajustes (letras solo en manual, 90° sin
etiqueta) van en el mismo PR, sin tocar.

— Vega
