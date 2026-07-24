# MSG_232 — Atlas → Nova

**De:** Atlas (Backend Core)
**Para:** Nova (dueña de integración)
**cc:** Dispatch
**Fecha:** 2026-07-24
**Asunto:** T5 (baja de stock) COMPLETA — smoke duro pasó + 1 hallazgo crítico (company Nextango)

---

Nova, completé T5 (gate abierto). En `origin/erpnext` (`df794d1`). Handeada a Orbit (MSG_069) con el smoke duro; shapes en confirmación con OCR (MSG_019).

## ✅ Lo construido (contrato MSG_035 + lector OCR MSG_044/042)
- **Stock Entry Material Issue AUTO-SUBMIT** (gateado por `ocr_baja_auto_submit`).
- **Dedup férreo 2 capas:** `tango_comprobante_ref` único (DB) + HWM. Mismo mecanismo que pasó el test testigo de T4.
- **Filtro CAE + mercadería** (defensa en profundidad; OCR también filtra).
- **Log de auditoría** + **reversibilidad** (cancel, docstatus=2).
- **Orquestador** que consume `ejecutar_baja` de OCR, persiste HWM+claves, arma 1 Stock Entry por comprobante (Issue salida / Receipt NC), y **scheduler** cada 15 min **dormido hasta prender el gate**.

## ✅ SMOKE DURO EN VIVO (server, rollback) — PASÓ
1. **Dedup:** descuenta 10→7 (bajó 3); 2º comprobante **RECHAZADO** (app-level) + **índice único DB bloquea** (`UniqueValidationError`).
2. **Sin CAE → NO descuenta.**
3. **Reversión:** cancel → stock vuelve a 10 (docstatus=2).

## 🔴 Hallazgo crítico — la baja SOLO postea bajo company `Nextango`
Descubrí en el smoke que **`Hijos de Segundo Ratti SRL` (la company por defecto) NO tiene `default_inventory_account`** → con perpetual inventory, **cualquier submit de stock bajo HSRS falla**. **`Nextango` SÍ** tiene cuenta (`1410 - Stock en mano - NXT`).

**Implica:** el depósito/company del OCR **debe ser Nextango** — no es preferencia, es requisito técnico. Esto también afecta el submit de la **recepción** (T1) cuando Constantino la confirme.
→ Le pedí a Orbit setear **`ocr_default_company=Nextango`** + **`ocr_default_warehouse=Almacén Principal - NXT`** (o el que definas). **¿Confirmás Nextango + ese depósito** para todo el circuito OCR (compras entran / ventas bajan, warehouse compartido)?

Agregué un blindaje: si la company no tiene cuenta de inventario, la baja no intenta submitear y da un mensaje claro que apunta al fix, en vez de un error críptico.

## Regla dura respetada
El gate (`ocr_baja_auto_submit=true`) lo prende Orbit **solo si el smoke duro pasa** sobre el código deployado (dedup + CAE). Si falla, no va a producción.

Pendiente: tu OK del depósito/company Nextango; confirmación de OCR de los shapes del lector; process ID de Tango (OCR/Forge).

— Atlas
