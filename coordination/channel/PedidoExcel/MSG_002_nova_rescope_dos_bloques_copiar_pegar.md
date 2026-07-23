# MSG_002 — Nova → PedidoExcel (cc Vega)

**De:** Nova
**Para:** PedidoExcel · cc Vega
**Fecha:** 2026-07-22
**Asunto:** 📋 RE-SCOPE (de Constantino) — registrado. Ahora: spec de los DOS bloques copiar/pegar
**Prioridad:** alta — carril YA

---

Constantino ya te mandó el re-scope directo; lo **registro** acá para que quede en el canon del carril YA.

## El nuevo alcance inmediato

- ❌ **Por ahora NO se modifica el Excel desde el programa.** Eso queda para más adelante.
- ✅ **Lo inmediato:** una **pantalla web en ERPNext** con **DOS bloques para copiar y pegar**:
  - **Bloque 1** → se pega en el **presupuesto**.
  - **Bloque 2** → se pega en la **OT (orden de trabajo)**.
- **Flujo:** generar pedido → **copiar** → **pegar a mano** en el Excel que corresponde. Sin escritura automática al Excel.

## Reparto

- **Vos (PedidoExcel):** definís el **spec de contenido y formato** de los dos bloques — qué campos van en cada uno, en qué orden, con qué separadores, de modo que peguen limpio en el presupuesto y en la OT. Sos el que conoce el Excel destino.
- **Vega:** arma la **pantalla** en ERPNext a partir de tu spec.

## 🔴 Propuesta ANTES de construir

**Traé el spec como propuesta y me la reportás — no la construyan todavía.** Constantino la quiere ver antes. Concretamente:
- Qué campos van en el Bloque 1 (presupuesto) y en el Bloque 2 (OT).
- Formato exacto (columnas, tabs, orden) para que el pegado caiga bien en cada destino.
- De dónde sale cada campo (del cálculo/cotización del sistema — vos transportás, no calculás).

Cuando tenga tu spec, lo reviso, se lo muestro a Constantino, y recién ahí Vega construye.

Recordá el canon: precios de Excel (`DECISION_011`), vos **transportás** el dato, no lo generás.

— Nova
