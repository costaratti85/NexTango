# DECISION_006 — Todo corte se factura como UN artículo: "chapa procesada"

**Fecha:** 2026-07-18
**Autor:** Constantino (registrada por Nova)
**Estado:** Vigente — modelo canónico de facturación
**Afecta a:** Tango (artículos, pedidos, facturación), Atlas/Lechu (flujo de pedido/presupuesto), Punto (dónde desemboca el cálculo)

---

## La definición

**Todos los cortes de pantógrafo / láser se facturan como UN SOLO artículo: "chapa procesada".**

Los artículos **"hierro cortado"**, **"hierro plegado"**, etc. **NUNCA se facturan.** Son únicamente **INSUMOS DE CÁLCULO** — pasos intermedios para llegar al precio de la "chapa procesada".

## Consecuencias operativas
- El **cálculo** (tiempo de láser, material, plegado, factores) puede desglosarse internamente en cuantos componentes haga falta, pero **desemboca en un único artículo cobrable**: "chapa procesada".
- Al armar el **flujo de generar pedido/presupuesto** (ERPNext → Tango), el renglón que se emite es **"chapa procesada"** — no los insumos.
- No crear ni empujar a facturación artículos intermedios del tipo "hierro cortado"/"hierro plegado".
- El desglose de insumos sirve para **costeo y trazabilidad interna**, no para el comprobante.

Relacionado: `DECISION_003` (Excel pricing preservado) · flujo de push de Pedidos a Tango · `SI Presupuesto Panel`.

---

> ⚠️ **CORRECCIÓN 2026-07-19 (`DECISION_011`):** **Tango NO maneja precios.** El pricing se hace en **EXCEL** y de ahí vienen los precios; hoy el vendedor los carga a mano en nuestro sistema. Cualquier tramo de este documento que diga "precios a Tango" o "Tango maestro de precios" **queda sin efecto**. Tango es **fiscal/facturación**.
