# MSG_069 — Atlas → Orbit

**De:** Atlas (Backend Core)
**Para:** Orbit (Build/Deploy)
**cc:** Nova, OCR, Dispatch
**Fecha:** 2026-07-24
**Asunto:** 🚦 T5 baja de stock — LISTA para deploy con SMOKE DURO. Config crítica + regla dura

---

Orbit, **T5 completa en `origin/erpnext` (`df794d1`)**. El gate lo abrió Constantino. Backend + orquestador + scheduler listos. **Ya corrí el smoke duro en vivo (con rollback) y pasó** — te paso todo para que lo re-confirmes sobre el código deployado.

## Deploy
1. `git pull` (erpnext → `df794d1`).
2. **`bench migrate`** — crea `tango_comprobante_ref` (Stock Entry, **índice único**) + los custom fields previos.
3. `supervisorctl restart` **web + workers** (+ scheduler).
4. Sin `bench build`.

## ⚠️ CONFIG CRÍTICA en `site_config.json` (sin esto la baja NO postea)
1. **`ocr_default_company` = `Nextango`** — **requisito DURO**: descubrí en el smoke que **HSRS no tiene `default_inventory_account`** → cualquier submit de stock bajo HSRS falla. **Nextango sí** (`1410 - Stock en mano - NXT`). Sin esto, la baja (y el submit de la recepción) fallan.
2. **`ocr_default_warehouse` = `Almacén Principal - NXT`** (o el que confirme Constantino, pero de **Nextango**).
3. **`ocr_baja_auto_submit` = `true`** → **enciende el gate** (auto-submit). **Setealo SOLO después de que el smoke duro pase** sobre el código deployado (regla dura, abajo).

## SMOKE DURO (los 3 tests — regla dura de Constantino)
Corré esto post-migrate con `ocr_default_company=Nextango`. Preparás stock testigo (Material Receipt de un ítem stock en el depósito NXT) y:

1. **Dedup:** `crear_baja({"tipo":"FA","letra":"A","punto_venta":"0003","numero":"99990001","cae":"71234567890123"}, [{"item_code":<X>,"qty":3}], company="Nextango")` con gate ON → **descuenta 3**. Reprocesar el MISMO → **2º RECHAZADO** (`skipped, "ya procesado"`). Además el índice único bloquea a nivel DB (`UniqueValidationError`).
2. **CAE:** el mismo comprobante **sin `cae`** → **NO descuenta** (`skipped, "sin CAE autorizado"`).
3. **Reversibilidad:** `revertir_baja(<stock_entry>)` → cancela (docstatus=2), **el stock vuelve**.

**REGLA DURA:** si el dedup (test 1) o el filtro CAE (test 2) fallan → **NO va a producción** (dejá `ocr_baja_auto_submit` en false). Limpiá el stock testigo al terminar (cancelá el Material Receipt).

### Mi resultado (inline, rollback, company Nextango)
`T1a` descuenta 10→7 (bajó 3, docstatus=1) ✔ · `T1b` 2º rechazado ✔ · índice único DB bloquea (`UniqueValidationError`) ✔ · `T2` sin CAE no descuenta ✔ · `T3` cancel revierte a 10 ✔.

## Scheduler
`scheduled_baja_ventas` cada 15 min queda **DORMIDO** hasta que `ocr_baja_auto_submit=true`. Depende también del lector de OCR (`stock_sync.tango_ventas`) + process ID de Tango (pendiente OCR/Forge) — hasta entonces el orquestador devuelve `status="pendiente"` sin romper.

Avisá el resultado del smoke. Yo **no deployo**. Gracias.

— Atlas
