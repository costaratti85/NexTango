# DECISION_007 — Corte lineal: 65% de barra → sugerir cobrar barra entera

**Fecha:** 2026-07-19 · **Autora:** Nova (autoridad delegada por Constantino)
**Origen:** canon fundacional — `docs/00_BRUJULA_DOCUMENT_FUNDACIONAL.md`, §3 flujo de corte lineal
**Estado:** Vigente · **Afecta a:** Gemu (corte lineal), Atlas (cotización)

## La regla

> "si última barra supera ~65% del largo estándar, sugerir **cobrar barra entera**."

Cuando el sobrante consumido de la última barra de un corte lineal **supera ~65%** del largo estándar de la barra, el sistema **sugiere facturar la barra completa** en lugar del metraje efectivamente cortado.

## Por qué

El recorte que queda por debajo del 35% rara vez se recoloca: es desperdicio real que igual paga la empresa. La regla traslada ese costo al pedido que lo genera.

## Cómo aplica

- Es una **sugerencia**, no una imposición: **el sistema sugiere, el humano decide, el sistema audita** (Brújula regla 8). Debe poder overridearse, y el override queda registrado.
- El umbral es **~65%** — aproximado y **parametrizable**, no hardcodeado.
- El "largo estándar" depende del perfil/caño/barra; sale del maestro de materiales, no de una constante global.
- Es criterio **comercial**, no geométrico: afecta la cotización, no el plan de corte.

## Pendiente de negocio (a Constantino, no lo decide Nova)

El valor exacto del umbral y si varía por tipo de material. Hasta que se defina, **~65% para todos**.
