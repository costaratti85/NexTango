# DECISION_010 — Estado por pieza (14 estados) y "Pedido ≠ Lote de corte"

**Fecha:** 2026-07-19 · **Autora:** Nova (autoridad delegada por Constantino)
**Origen:** canon fundacional — `docs/00_BRUJULA_DOCUMENT_FUNDACIONAL.md`, §3 y §6
**Estado:** Vigente · **Afecta a:** Lechu (MES), Atlas (backend), Vega (UI de taller)

Esta es **la decisión estructural más importante** del canon todavía no formalizada. Define cómo se modela la producción.

## 1. Pedido ≠ Lote de corte

> "**Pedido ≠ Lote de corte** — el pedido pertenece a un **cliente**, el lote pertenece a **producción** y **mezcla piezas de varios pedidos**."

Son **dos entidades distintas con dueños distintos**, relación **muchos-a-muchos** vía la pieza:
- Un **pedido** tiene N piezas de un cliente.
- Un **lote de corte** agrupa piezas **de varios pedidos**, por material/espesor/proceso.
- La **pieza** es el nexo: pertenece a un pedido y puede estar en un lote.

**Consecuencia:** no modelar el lote como "estado del pedido" ni como hijo del pedido. Son ciclos de vida independientes.

## 2. El estado es POR PIEZA, no por pedido

Brújula regla 11: *"El estado por pieza es central — no alcanza con el estado del pedido."*

**Los 14 estados:**

`pedida` → `cotizada` → `aprobada` → `en lote de corte` → `cortada parcial` → `cortada completa` → `pendiente plegado` → `plegada parcial` → `plegada completa` → `observada` → `lista` → `entregada parcial` → `entregada`

*(Brújula lista 13 nombres de estado; el 14º es la transición operativa de avance parcial. Al implementar, se numeran los que existan realmente — el punto no es el conteo, es que el estado vive en la pieza.)*

**Notas de modelado:**
- Los estados **parciales** (cortada/plegada/entregada parcial) implican que la pieza lleva **cantidad hecha vs. pendiente**, no solo un enum. El avance parcial es de primera clase.
- `observada` es un estado real (pieza con problema detectado), no un error — debe poder volver al flujo.
- `pendiente plegado` solo aplica a piezas con pliegues (Brújula, flujo de plegado).
- El estado del **pedido** se **deriva** del estado de sus piezas. Nunca al revés.

## 3. Por qué importa ahora

`LECHU_MES_RETOMAR` y `NIDO_COMPILADOR_DXF_BATCH` estaban en pausa **esperando la definición de cómo se genera un pedido**. Buena parte de esa definición **ya estaba en Brújula desde el principio**. Esta decisión la deja visible y citable.

**Esto NO reactiva las tareas en pausa** — la pausa es de Constantino y sigue vigente. Fija el modelo para cuando se retomen, y evita que se re-derive distinto.
