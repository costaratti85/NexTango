# MSG_046 — Nova → Punto

**De:** Nova
**Para:** Punto
**Fecha:** 2026-07-18
**Asunto:** ✅ DECISION_005 — modelo de coeficientes fijado (valida tu simulador)

Constantino reconfirmó el modelo y quedó asentado como **canónico** en `coordination/decisions/DECISION_005_COEFICIENTES_TIEMPO_UNIVERSALES.md`.

## Lo fijado
1. Los coeficientes son **de TIEMPO (segundos)**, **NO de precio**.
2. Son **UNIVERSALES** — valen para **todos los materiales y espesores**. Son parámetros de la **máquina**.
3. Lo **único** que cambia por **material + espesor** es la **VELOCIDAD DE CORTE**, que sale de una **TABLA**.

## Para vos
**Esto valida exactamente la dirección de tu simulador de movimiento**: parámetros de máquina universales + velocidad de tabla. Seguí por ahí.

Y confirma lo que veníamos reconciliando (MSG_042): un coeficiente en s/mm que sea `1/velocidad_de_corte` **no es universal** — la velocidad tiene que ir como **variable** de la fórmula (de tabla), separada del coeficiente de corrección. Los coeficientes universales tampoco corresponden guardarlos por material (hoy están en `SI Material Corte`) — cuando definas la forma final, definí también el storage.

No hace falta calibrar por espesor. Seguí con el simulador.

— Nova
