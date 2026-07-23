# DECISION_005 — Los coeficientes de la fórmula son de TIEMPO y son UNIVERSALES

**Fecha:** 2026-07-18
**Autor:** Constantino (registrada por Nova)
**Estado:** Vigente — modelo canónico
**Afecta a:** Punto (motor/simulador de tiempo, calibración), y a todo cálculo de precio de corte

---

## La definición

1. Los coeficientes de la fórmula de tiempo son **de TIEMPO (segundos)** — **NO son coeficientes de precio.**
2. Son **UNIVERSALES**: valen para **todos los materiales y todos los espesores**. Son parámetros de la **máquina**, no del material.
3. Lo **único** que cambia por **material + espesor** es la **VELOCIDAD DE CORTE**, que se obtiene de una **TABLA**.

## Por qué (física)
Los coeficientes existen para **conciliar la teoría con la realidad**: la cuenta `distancia ÷ velocidad` no contempla las **rampas de aceleración/desaceleración** ni que la **torcha sube y baja** cada vez que empieza o termina de cortar. `1650 mm/s` es la velocidad **máxima** de desplazamiento, alcanzada solo con la torcha arriba y ya acelerada. Eso depende de los **motores de la máquina** → por eso es universal.

## Consecuencias operativas
- ✅ **NO se calibra por espesor.** No hacen falta baterías de calibración por material.
- ✅ **Valida la dirección del simulador de movimiento de Punto**: parámetros de máquina universales + velocidad de tabla.
- ⛔ Un coeficiente en **s/mm** que equivalga a `1/velocidad_de_corte` **NO es universal** — significa que la velocidad quedó absorbida dentro del coeficiente. La velocidad debe ir como **variable de la fórmula** (de tabla), separada del coeficiente de corrección.
- Los coeficientes universales **no corresponden guardarlos por material** (hoy están en campos de `SI Material Corte`); definir un storage acorde.

Relacionado: MSG_040/041/042 a Punto · `PUNTO_BUG_ERROR_AL_CALCULAR_PRECIO` · trabajo del simulador de movimiento.
