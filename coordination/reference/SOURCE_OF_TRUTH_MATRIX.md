# Source of Truth Matrix — quién es dueño de cada concepto

> ## 🟢 EL MODELO DEFINITIVO (Constantino, 2026-07-19) — *"así va a ser"*
>
> | Concepto | Máster |
> |---|---|
> | **Lista de artículos / catálogo** | **TANGO** |
> | **Stock** | **ERPNext** |
> | **Precios** | **EXCEL** |
>
> Cada uno es máster **de lo suyo**. Todo lo demás en este documento se subordina a estas tres líneas.
>
> **Dirección de los precios:** `Excel → Tango` (push, para poder facturar desde Tango).
> **NUNCA** `Tango → sistema`. Tango puede *recibir* precios; jamás es su fuente.
>
> *Este modelo ya estaba escrito en `docs/05_OCR_SUPPLIERS_FLOW.md` ("artículos/proveedor a Tango · stock a ERPNext · costos a Excel") — un documento que no se había leído. Ver `DECISION_011` §7.*

**Estado:** Vigente · **Fecha:** 2026-07-19 · **Autora:** Nova
**Origen:** rescatada del repo histórico `Sistema-Industrial` (`modules/shared/contracts/erpnext_tango/SOURCE_OF_TRUTH_MATRIX.md`), autoría original de Nova, **depurada** de las filas contradichas por `DECISION_002`.
**Cambiar esta matriz requiere:** revisión de Nova + **aprobación de Constantino**.

---

## La matriz

| Concepto | Dueño (fuente de verdad) | Nota |
|---|---|---|
| Cliente operativo | **ERPNext** | |
| Lead / oportunidad | **ERPNext** | |
| Cotización / presupuesto | **ERPNext** | |
| Pedido / sales order | **ERPNext** | |
| **Lista de artículos / catálogo** | **🔵 TANGO** | ⚠️ **CORREGIDO 2026-07-19** — Tango es el **máster del catálogo**. ERPNext tiene copia |
| BOM | **ERPNext** | |
| Orden de trabajo | **ERPNext** | |
| **Stock** | **🟠 ERPNext** | **Máster** del stock |
| **Pricing / precios** | **📗 EXCEL (máster)** | ⚠️ **CORREGIDO 2026-07-19** — `DECISION_011`. Los precios **nacen en Excel**. Hoy el vendedor los carga a mano en ERPNext. Tango puede **recibir** precios (destino, para facturar desde ahí), **nunca** ser la fuente. Dirección: **Excel → Tango**, jamás al revés |
| **Factura oficial** | **🔴 TANGO** | Requiere aprobación de Constantino para tocar |
| **Asiento contable** | **🔴 TANGO** | Ídem |
| **Comportamiento fiscal / impositivo** | **🔴 TANGO** | Ídem |
| Pricing humano (planilla) | **Excel** | `DECISION_003` — Excel → Tango → ERPNext |
| Archivo CAD / DXF | **App SistemaIndustrial** | |
| Geometría normalizada | **App SistemaIndustrial** | |
| Parámetros de costeo (coeficientes, precio/segundo) | **App SistemaIndustrial** | `DECISION_005` — universales de máquina |
| Estado por pieza | **App SistemaIndustrial** | `DECISION_010` |
| Lote de corte | **App SistemaIndustrial** | `DECISION_010` — no es del pedido |
| **Nesting** | **CypCut** (externo) | `DECISION_002` · Brújula regla 5 |
| **G-code / postproceso** | **CostADCAM** (propio, standalone) | `DECISION_002` §2 · Brújula regla 6 |

> **Filas eliminadas respecto del original:** `Nesting plan → SistemaIndustrial Nesting` y `CAM output/GCode → SistemaIndustrial CAM`. Contradichas por `DECISION_002` y Brújula 5/6. Manda el actual.

---

## ⚠️ Regla de conflicto (obligatoria para todos los agentes)

> **Si cualquier documento, ticket, código o instrucción contradice esta matriz, el agente PARA y produce un decision pack.**

Un **decision pack** es: qué dice la matriz, qué dice lo que la contradice, qué opciones hay, qué recomendás — y se escribe en el canal de Nova. **No se improvisa, no se resuelve por cuenta propia, no se elige "lo que parece razonable".**

Esta regla existe porque el modo de falla más caro que tuvimos no fue un bug: fue **avanzar sobre una fuente de verdad desactualizada** sin que nadie frenara a chequear.

Aplica igual si la contradicción viene de **mí**. Si te pido algo que rompe la matriz, paralo y decímelo.

### Corolario — no descalifiques el input de Constantino con una regla que él no fijó

Un agente **no puede** inferir una regla de los ejemplos existentes y usarla para **descalificar algo que cargó o pidió Constantino**. Si tu generalización sobre los datos actuales choca con lo que él acaba de hacer, **la que cae es tu generalización, no su input** — PARÁ y escalá a Nova.

Caso de referencia (2026-07-20, `DECISION_017`): un agente concluyó que "un patrón debe ser una celda del tamaño del offset" (regla inferida de los patrones existentes) y con eso decidió que un DXF cargado por Constantino "no era un patrón". Era canon equivocado: el modelo real permite tiles más grandes que el offset, con solape. Constantino es la fuente del criterio; una generalización sobre los datos **no es** regla de negocio hasta que él la confirme.

## Zona roja

Todo lo marcado **🔴 TANGO** toca **facturación, contabilidad o comportamiento fiscal**. Ningún agente escribe ahí sin **aprobación explícita de Constantino**. Leer, sí. Escribir, no.
