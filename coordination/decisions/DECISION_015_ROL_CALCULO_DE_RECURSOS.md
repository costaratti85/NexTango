# DECISION_015 — Cálculo de Recursos será un rol propio (con timing definido)

**Fecha:** 2026-07-19 · **Decidida por:** Nova (autoridad **delegada explícitamente** por Constantino: *"que lo maneje Nova"*)
**Estado:** Vigente — decisión estructural con **activación diferida**
**Afecta a:** Punto, Nido, Vega, Lechu, Atlas

---

## 1. La decisión

**El Cálculo de Recursos se separa como rol propio.** (Opción 2 de `PROPUESTA_ARREGLOS_DE_ROLES.md` §B.1.)

**Pero no ahora.** El traspaso se hace **cuando el simulador de movimiento esté cerrado**.

## 2. Por qué rol propio

Brújula: *"Recurso industrial como unidad económica — el sistema vende chapa, corte, plegado, metro lineal, tiempo de máquina."*

Este territorio —**tiempo de máquina, consumo de material, y de ahí el precio**— es **el corazón económico del sistema**. Merece un dueño declarado, no ser un apéndice del contrato de CAD.

El argumento decisivo no es la carga de trabajo: es que **el motor tiene más de un consumidor**.

| Consumidor | Qué necesita |
|---|---|
| **Precio / cotización** | segundos de máquina, material, factores |
| **Nido** (`DECISION_012`) | **segundos de máquina por pieza** — para el criterio "pocos segundos de máquina" |
| **MES** (`DECISION_010`) | tiempo estimado para planificar producción |

O sea: **no es un detalle interno del precio, es infraestructura compartida.**

Dejarlo dentro del contrato de CAD de Punto significa que frentes enteros —incluida la compilación de lotes, que Constantino llama *"la función más importante para poder hacer los nestings"*— dependerían de un rol que **no los tiene como responsabilidad declarada**. Ese es el escenario donde un consumidor espera indefinidamente a un dueño que nunca priorizó ese trabajo, porque formalmente no era suyo.

## 3. Por qué NO ahora — el criterio de timing

**No se parte un frente crítico a mitad de camino.**

Punto está en la **Etapa 1 del simulador de movimiento** (investigación/brainstorm), después de que ningún modelo simple cerrara. Todo el contexto duro vive hoy en su cabeza: la calibración P01–P14, la física del 1650 mm/s, por qué el motor no frena a velocidad cero, el look-ahead. **Traspasar eso en pleno rediseño es la peor forma posible de crear un rol** — se pierde más de lo que se gana.

Además, **el timing no urge**: el otro consumidor (Nido) está bloqueado por MES, que está en pausa. **Todavía nadie más necesita el motor.**

## 4. Condición de disparo

> **El traspaso se dispara cuando el modelo de cálculo esté CERRADO** — es decir, cuando el simulador produzca tiempos que **reconcilien con los datos de calibración** y Punto lo dé por estable.
>
> **Ventana:** después de que cierre el simulador, **y antes de que se retome MES.**

No es una fecha: es una condición verificable. Nova la monitorea.

## 5. Alcance del rol (cuando se cree)

**Posee:** modelo de tiempo de máquina, coeficientes universales (`DECISION_005`), tabla de velocidades por material+espesor, cálculo de consumo de material, y la fórmula que desemboca en el precio.

**No posee:** la geometría (es de Punto), la facturación (Tango, `DECISION_006`), ni la UI (Vega).

**Entrega a:** precio/cotización, Nido, MES.

## 6. Mientras tanto (vigente HOY)

- Punto **conserva** el cálculo de recursos, como extensión reconocida y **temporal** de su contrato.
- Sigue el **congelamiento de carga** (`PROPUESTA_ARREGLOS_DE_ROLES.md` §A.4): nada nuevo a Punto salvo simulador y bug de precio. Punto tiene **60 tareas** contra 35 del siguiente — el frente más crítico no puede depender de un agente saturado.
- Todo lo que Punto produzca del modelo **debe quedar documentado**, no solo implementado. El traspaso futuro depende de eso: si el modelo vive solo en el código, el rol nuevo nace ciego.

## 7. Riesgo asumido

Diferir el traspaso mantiene, hasta que cierre el simulador, **un único punto de falla** en el frente más caro del sistema. Lo acepto a conciencia: el riesgo de partirlo ahora es mayor. La mitigación es §6 — congelar carga y exigir documentación.
