# Relevamiento negocio — Bloque 2: STOCK / PRODUCCIÓN / MES / dominio

**Autor:** Orbit · **Fecha:** 2026-07-19 · **Tipo:** SOLO LECTURA · **Entrega:** POR PARTES (Prioridad 2 — bloque stock/producción; siguen: clientes/biblioteca, OCR, eventos, CAD no-cubierto).
**Regla:** cotejar cada definición de negocio contra `DECISION_001..016`, marcar toda discrepancia, **sin asumir que el canon está bien**.

---

## 0. Titular

A diferencia de pricing, acá **el canon actual está BIEN** en el punto central (stock): `SOURCE_OF_TRUTH_MATRIX` actual dice **"Stock operativo → ERPNext"**, y es el **repo VIEJO** el que trae la afirmación equivocada *"Tango is the stock source of truth"* (que el propio viejo admite conflictiva). **La errata está del lado viejo, no del canon.** Pero queda un **hueco real**: las reglas de **reserva / consumo / scrap / remanente** de producción —bien detalladas en los viejos— **no están en ninguna DECISION**.

---

## 1. Definiciones de negocio (con citas)

### Stock — quién es dueño
- **Canon ACTUAL (correcto):** `coordination/reference/SOURCE_OF_TRUTH_MATRIX.md`:20 → *"Stock operativo | **ERPNext**"*. `docs/03_TANGO_BOUNDARY.md`:18 → *"Toda factura/nota de crédito de Tango debe sincronizar stock/estado en ERPNext vía API."* `docs/TANGO_ERPNEXT_FIELD_MAPPING.md`:8 → *"ERPNext consume como mirror de solo lectura (**salvo stock operativo y pedidos**)."* Brújula:78 → *"stock a ERPNext."*
- **VIEJO (errata):** `INVENTORY_STOCK_CONTRACT_DRAFT.md`:53 → *"**Tango is the stock source of truth.**"* + "Inventory must not override Tango official stock."

### Reserva / consumo / scrap / remanente (reglas del viejo, NO en el canon)
`INVENTORY_STOCK_CONTRACT_DRAFT.md` (viejo):
- :97 → *"Reservation must include correlation with **work order or production demand**."*
- :147 → *"Consumption must reference **work order, material, quantity, unit, batch, operator/system actor**."*
- :159 → *"Scrap must reference **reason, quantity, work order, operation, material**."*
- :209/211 → *"Inventory does not own work order lifecycle"* / *"Production consumption must be traceable to work order and material source."*

### Estados de producción — dos modelos distintos
- **Canon actual:** `DECISION_010` = **estados por pieza** (14: pedida→…→entregada) + **"Pedido ≠ Lote"**.
- **Viejo:** `EVENT_SYSTEM_ARCHITECTURE_DRAFT.md`:149 → *"quote approval → order confirmation → **work order creation**"* — modela con **work order lifecycle** de ERPNext.

### MES
- Viejo, honesto: `ARCHITECTURE_GAPS_AND_RISKS.md` → *"**MES exists only as a placeholder** module. Work order lifecycle is not formally contracted."*

---

## 2. 🔴 Contradicciones contra las DECISIONs

| Tema | Viejo | Canon actual | Gana | ¿Consultar? |
|---|---|---|---|---|
| **Dueño del stock** | "Tango stock source of truth" (INVENTORY_STOCK:53) | "Stock operativo → **ERPNext**" (Source of Truth Matrix:20; 03_TANGO_BOUNDARY; FIELD_MAPPING:8) | **NUEVO** (canon correcto) | No — pero ver nota ⚠️ |
| **Modelo de estados de producción** | "work order lifecycle" (ERPNext manufacturing) | "**estados por pieza** + pedido≠lote" (`DECISION_010`) | **NUEVO** (más fino) | ⚠️ Sí — ¿coexisten work order de ERPNext + estados por pieza SI, o se reemplaza? No está resuelto |
| **Reserva/consumo/scrap** | Reglas detalladas (INVENTORY_STOCK) | **No hay DECISION** que las cubra | — | ⚠️ Hueco (ver §3) |

⚠️ **Nota de método (por el antecedente de precios):** el patrón *"Tango es dueño de X"* ya falló una vez (precios). Acá el canon actual ya corrigió stock a ERPNext, **pero conviene que Constantino lo confirme explícitamente** — el mismo reflejo ("Tango dueño de todo") produjo la errata de precios, y el viejo lo repite para stock. El canon actual parece correcto; solo pido confirmación, no cambio.

---

## 3. Definiciones de negocio NO cubiertas por ninguna DECISION (huecos)

1. **Reserva / consumo / scrap / remanente de producción** — el viejo `INVENTORY_STOCK_CONTRACT` las detalla (correlación a work order, trazabilidad de consumo, razón de scrap); **ninguna DECISION las formaliza**. `DECISION_007` toca solo el 65% de barra (corte lineal). Es el hueco de negocio más grande de este bloque, y se agrava con MES inactivo.
2. **Trazabilidad de scrap/rework** — `TESTING_STRATEGY_DRAFT`:138 la nombra; sin DECISION.
3. **Sync Excel-first: riesgos operativos** — `ARCHITECTURE_GAPS_AND_RISKS` los enumera: *"manual export timing, file format drift, duplicate imports, partial failure; no retry, reconciliation, idempotency or rollback."* **Muy relevante ahora** que el pricing es carga manual (DECISION_011): esos riesgos aplican a la carga diaria de precios. Sin DECISION que los mitigue.
4. **Mapping identificadores SistemaIndustrial ↔ Tango** — `GAPS` lo marca como no definido; hoy **parcialmente** resuelto por el campo `SI_TANGO_ID` (Tango agent), pero sin doc de contrato.

---

## 4. Cobertura
- **Leído (este bloque):** `INVENTORY_STOCK_CONTRACT_DRAFT` (viejo), `ARCHITECTURE_GAPS_AND_RISKS` (viejo — el doc más útil para contradicciones), `EVENT_SYSTEM_ARCHITECTURE_DRAFT` (parcial), y cotejo contra `SOURCE_OF_TRUTH_MATRIX`, `03_TANGO_BOUNDARY`, `TANGO_ERPNEXT_FIELD_MAPPING`, `DECISION_010` del canon actual.
- **PENDIENTE (bloques siguientes):** clientes / biblioteca de piezas de cliente, OCR proveedores (flujo Brújula vs `DECISION_016`), arquitectura de eventos completa, contratos DTO CAD/geometría, y los README por-módulo restantes. Entrego este bloque ahora como pediste.
- Solo lectura, sin secretos, sin tocar repos.

## Resumen ejecutivo
En **stock el canon actual está correcto** (ERPNext = stock operativo); la errata *"Tango stock source of truth"* está del lado **viejo** (y el viejo mismo la marcó conflictiva) — gana el nuevo, solo pido a Constantino confirmarlo por el antecedente de precios. **Hueco grande:** reserva/consumo/scrap/remanente de producción no están en ninguna DECISION (los viejos los detallan). **Tensión a resolver:** estados-por-pieza (`DECISION_010`) vs. work-order-lifecycle (viejo) — no está definido si coexisten. Y los **riesgos del sync Excel-first** (timing, duplicados, sin idempotencia) ahora aplican a la carga manual de precios y no tienen DECISION. Marco, no resuelvo.
