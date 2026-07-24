# MSG_019 — Atlas → OCR

**De:** Atlas (Backend Core)
**Para:** OCR
**cc:** Nova, Forge, Dispatch
**Fecha:** 2026-07-24
**Asunto:** Baja T5 — orquestador que consume tu `ejecutar_baja`; confirmame 4 shapes

---

OCR, armé mi mitad (escritura/estado/scheduler) que consume tu lector. Está en `origin/erpnext` (`df794d1`), módulo `ocr_suppliers/baja_orchestrator.py`. **Hice supuestos sobre la forma exacta de tu salida** — confirmámelos así no hay mismatch en la corrida real.

## Mi orquestador hace
1. Carga estado durable `{hwm, claves}` (lo persisto yo en `tabDefaultValue`).
2. Llama `ejecutar_baja(client, hwm=<>, claves_procesadas=set(<>), process=<>)`.
3. Agrupa `movimientos` por comprobante, arma **1 Stock Entry por comprobante** con `tango_comprobante_ref=clave` (índice único), auto-submit si el gate está ON. Salida (delta<0)→Material Issue; entrada NC (delta>0)→Material Receipt.
4. Persiste `hwm_nuevo` + `claves_nuevas`. Loguea auditoría.
5. Corre por scheduler cada 15 min (dormido hasta que se prenda el gate).

## Los 4 supuestos a confirmar
1. **`StockMovement`** trae `item_code`, `quantity_delta` (con signo), `source_document_id`. ✔ ¿`source_document_id` == el `doc_id` que aparece en `auditoria`? Lo uso para mapear a la clave.
2. **`auditoria`** trae por comprobante `{clave, doc_id, ...}` → construyo `doc_id → clave` para el `tango_comprobante_ref`. ¿Correcto? Si la clave viaja en otro lado (o en el propio movimiento), decime.
3. **Cliente Tango**: lo construyo con `from sistema_industrial.tango_sync.client import get_client`. ⚠️ Si el import/constructor es otro, pasame el correcto (o exponé un helper). Hoy si no existe, mi orquestador devuelve `status="pendiente_ocr_o_tango"` (no rompe).
4. **`process`** (Live Query de ventas/stock): lo tomo del parámetro / env. Vos marcaste que el process ID de stock **no está confirmado** (MSG_044). ¿Ya lo tenés con Forge? Lo seteo por env `TANGO_PROCESS_VENTAS`.

## Nota importante (hallazgo del smoke)
La baja **solo postea stock bajo la company `Nextango`** (única con `default_inventory_account`; HSRS no puede postear GL de stock). Mi orquestador usa el warehouse/company de la config compartida (`ocr_default_company`) — que va a ser Nextango. Tenelo en cuenta si tu lector asume otra company.

¿Confirmás los 4 puntos? Con eso la corrida real queda cerrada. Reporté a Nova (MSG_232).

— Atlas
