# DECISION_008 — DXF de lote: espaciados 300/500 mm y etiquetado

**Fecha:** 2026-07-19 · **Autora:** Nova (autoridad delegada por Constantino)
**Origen:** canon fundacional — `docs/00_BRUJULA_DOCUMENT_FUNDACIONAL.md`, §5 archivos a generar
**Estado:** Vigente · **Afecta a:** Nido (compilador DXF batch), Punto (geometría)

## La regla

> "DXF de lote de corte (ordenado, **300mm entre piezas**, **500mm entre filas de espesor**, **etiquetas con espesor y cantidad**)."

El DXF de lote se compila **ordenado**, con:
- **300 mm** de separación entre piezas.
- **500 mm** entre filas de distinto espesor.
- **Etiquetas** que indiquen **espesor y cantidad**.

## Por qué

El DXF de lote **no es el layout final de corte** — el nesting lo hace CypCut (`DECISION_002`). Es un **archivo de entrega ordenado y legible** para que el pantografista identifique y agrupe sin ambigüedad. Los espaciados generosos existen para que las piezas se distingan a simple vista y se puedan separar/reagrupar antes del nesting, no para optimizar material.

## Cómo aplica

- Los valores **300/500 mm** son **parámetros configurables**, no constantes hardcodeadas.
- No optimizar el espaciado "para ahorrar chapa": sería hacer nesting, y eso es de CypCut.
- Las filas se agrupan **por espesor** — es el criterio de orden primario (Brújula regla 12: producción se organiza por lógica de taller).

## Nota de estado

`NIDO_COMPILADOR_DXF_BATCH` sigue **en pausa** por decisión de Constantino. Esta decisión **no reactiva la tarea**: fija el parámetro para cuando se retome, y evita que se re-derive o se invente otro.
