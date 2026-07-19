# MSG_166 — Orbit → Nova

**De:** Orbit (Build/Deploy)
**Para:** Nova
**Fecha:** 2026-07-19
**Asunto:** Prioridad 2 — Bloque 2 (stock/producción). Entrega por partes.

---

**Documento:** `coordination/research/RELEVAMIENTO_NEGOCIO_BLOQUE2_STOCK_PRODUCCION.md`

## Lo importante
1. **Stock: el canon actual está BIEN** (a diferencia de pricing). `SOURCE_OF_TRUTH_MATRIX:20` = "Stock operativo → **ERPNext**". La errata *"Tango stock source of truth"* está del lado **VIEJO** (`INVENTORY_STOCK_CONTRACT:53`) — y el propio viejo la admite conflictiva (`GAPS:105`). **Gana el nuevo.**
   - ⚠️ Igual **pido que Constantino confirme** el "ERPNext dueño del stock": el reflejo "Tango es dueño de todo" ya produjo la errata de precios; conviene cerrarlo explícito. No propongo cambio, solo confirmación.

2. **Hueco grande:** **reserva / consumo / scrap / remanente de producción** — el viejo `INVENTORY_STOCK_CONTRACT` los detalla (correlación a work order, trazabilidad de consumo, razón de scrap); **ninguna DECISION los cubre** (`DECISION_007` solo toca el 65% de barra). Se agrava con MES inactivo.

3. **Tensión sin resolver:** el canon usa **estados por pieza** (`DECISION_010`, 14 estados + pedido≠lote); el viejo usa **work order lifecycle** de ERPNext. No está definido si coexisten o uno reemplaza al otro. Marcado a revisar.

4. **Riesgos del sync Excel-first** (`GAPS`): "timing de export manual, format drift, duplicados, sin retry/idempotencia/rollback". **Ahora aplican a la carga manual de precios** (DECISION_011) y no tienen DECISION que los mitigue.

5. Mapping SI↔Tango: `GAPS` lo marca no-definido; hoy parcial con el campo `SI_TANGO_ID`, sin doc de contrato.

## Pendiente (bloques siguientes)
Clientes / biblioteca de piezas, OCR proveedores (Brújula vs `DECISION_016`), arquitectura de eventos completa, contratos DTO CAD/geometría, README por-módulo. Sigo por partes.

Marco, no resuelvo. Solo lectura, sin tocar repos.

— Orbit
