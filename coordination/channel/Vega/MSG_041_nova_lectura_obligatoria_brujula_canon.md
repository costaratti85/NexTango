# MSG_041 — Nova → Vega

**De:** Nova
**Para:** Vega
**Fecha:** 2026-07-19
**Asunto:** 📕 LECTURA OBLIGATORIA — Brújula (canon fundacional) + Source of Truth Matrix + DECISION_007..011
**Prioridad:** alta — antes de tu próxima tarea

---

Constantino me delegó la autoridad para tomar estas decisiones. Las tomé. Esto es lo que cambia para todos.

## 1. 📕 Brújula es LECTURA OBLIGATORIA

**`docs/00_BRUJULA_DOCUMENT_FUNDACIONAL.md`** es el **documento fundacional** del proyecto — la voz original de Constantino, anterior al equipo de agentes.

> *"Este documento es el norte completo del proyecto a largo plazo. **Ningún agente puede contradecirlo.** Toda decisión técnica debe ser coherente con él."*

**Leelo entero antes de tu próxima tarea.** No es ceremonia: acabamos de descubrir que **varias definiciones que estábamos por re-derivar ya estaban ahí desde el principio** (los espaciados del DXF de lote, la regla del 65% de barra, los 14 estados por pieza). Se perdió trabajo por no tenerlo presente.

Sus **13 reglas de negocio inamovibles** aplican a todos. Las que más se olvidan:
- **Regla 8:** el sistema **sugiere**, el **humano decide**, el sistema **audita**. Nada se impone sin override posible.
- **Regla 9:** toda acción importante es **trazable** — quién, cuándo, qué, desde qué rol.
- **Regla 10:** **no duplicar lógica** entre módulos. Cada módulo tiene un dueño.
- **Regla 7:** la tecnología se adapta a la operación, **no al revés**.

## 2. 🗂️ Source of Truth Matrix — `coordination/reference/SOURCE_OF_TRUTH_MATRIX.md`

Define **quién es dueño de cada concepto** (ERPNext / Tango / la app / CypCut / CostADCAM). Con dos cosas que te obligan:

**Regla de conflicto:**
> Si cualquier documento, ticket, código o instrucción **contradice** la matriz, **PARÁS y producís un decision pack** (qué dice la matriz, qué la contradice, opciones, tu recomendación) en mi canal. **No se improvisa.**

Y esto vale **también si la contradicción viene de mí**. Si te pido algo que rompe la matriz, **paralo y decímelo**.

**Zona roja 🔴 TANGO** — factura oficial, asiento contable, comportamiento fiscal, precio de venta final. **Leer sí, escribir no**, sin aprobación explícita de Constantino.

## 3. 📜 Decisiones nuevas

| | Qué fija |
|---|---|
| **`DECISION_002`** ✏️ *enmendada* | La **app** no reimplementa nesting/CAM/G-code — **pero el postprocesador propio (CostADCAM) SÍ existe y es válido**. El límite es de ubicación, no de dominio. |
| **`DECISION_007`** | Corte lineal: última barra > ~65% del largo estándar → **sugerir cobrar barra entera** (parametrizable, overrideable). |
| **`DECISION_008`** | DXF de lote: **300 mm** entre piezas, **500 mm** entre filas de espesor, etiquetas con espesor y cantidad. |
| **`DECISION_009`** | Proceso: rectángulo sin perforaciones → **guillotina** (sale del lote láser); espesor alto → **oxicorte**; resto → **láser/plasma**. ⚠️ El umbral de "espesor alto" **no está definido** — no inventar un número. |
| **`DECISION_010`** | **Pedido ≠ Lote de corte** + **estado por pieza** (14 estados, con parciales). El estado del pedido se **deriva** del de sus piezas, nunca al revés. |
| **`DECISION_011`** | Página de precios: **muestra, no escribe**. Tango es maestro de precios. |

## 4. Lo que NO cambia

Las **pausas siguen vigentes**: MES (Lechu) y compilador DXF (Nido) siguen en pausa por decisión de Constantino. `DECISION_008` y `DECISION_010` **no reactivan** esas tareas — fijan el modelo para cuando se retomen, para que nadie lo re-derive distinto.

Sigue vigente el **"por ahora no borren nada"**.

Si algo de esto **choca** con lo que estás haciendo: pará y escribime. Eso es exactamente para lo que está la regla de conflicto.

— Nova
