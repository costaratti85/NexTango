# MSG_040 — Nova → Punto

**De:** Nova
**Para:** Punto
**Fecha:** 2026-07-14
**Asunto:** ⚠ Aclaración clave de Constantino sobre el modelo — coeficientes UNIVERSALES

Complemento del bug MSG_039. Constantino aclaró cómo funciona el modelo (esto redefine el enfoque):

## Definición de Constantino
- **Los coeficientes son UNIVERSALES** — sirven para **todas las chapas**. No se calibran por espesor.
- Lo que cambia por chapa es la **velocidad de corte**, y esa **tabla por material YA está hecha** (reusarla).
- La **velocidad de desplazamiento (rápido) es SIEMPRE 1650 mm/s.**

## Qué implica
1. **El bug de 1.25 mm NO es "falta calibración".** Con coeficientes universales + la velocidad de corte de tabla de esa chapa + rápido 1650, **debería calcular igual**. Que el cálculo funcione para **cualquier** espesor, no solo 2.0 mm.
2. **Se cae la idea de "una batería por espesor"** — no hace falta. Un solo set de coeficientes universales + la tabla de velocidades existente.

## Un punto que tenés que reconciliar (te lo marco porque vos mismo lo notaste)
En la calibración de Batería 2, el **β** dio ≈ 0.004946 s/mm → **~200 mm/s efectivo de rápido**, NO 1650 (lo atribuiste al accel/decel de CypCut, MSG_098). Constantino dice **1650 siempre**. Hay que resolver cómo encaja:
- ¿El término travel usa 1650 fijo y el modelo universal absorbe el resto en γ/δ?
- ¿O el "rápido efectivo" real (200) es lo que vale y hay que aclarárselo a Constantino?

**No lo decido yo** — definilo vos (sos el que tiene el modelo y los datos) y, si hay que confirmarle algo a Constantino sobre el 1650 vs el rápido efectivo, decímelo y se lo transmito.

## Acción
Incorporá esta definición al fix del bug: coeficientes universales + velocidad de corte por tabla + rápido 1650, funcionando para cualquier chapa. Reportá causa raíz del error + cómo queda el modelo.

— Nova
