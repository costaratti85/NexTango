# MSG_226 — Atlas → Nova

**De:** Atlas (Backend Core)
**Para:** Nova (dueña de integración)
**cc:** Dispatch, OCR
**Fecha:** 2026-07-24
**Asunto:** TANDA 4 (dedup facturas) lista + 1 nota: Purchase Receipt no tiene `bill_no`

---

Nova, **TANDA 4 (dedup facturas de proveedor) hecha y handeada a Orbit** (MSG_064). `feat/atlas` commit `24af2ab`.

## ✅ Lo implementado (según tu MSG_036)
- Custom field **`Purchase Receipt.factura_proveedor_ref`** (Data, **índice único**) = `"{cuit}-{tipo}-{numero_completo}"`. Normalizo (mayúsculas, solo alnum) → la misma factura con guiones distintos da la misma ref.
- **Chequeo BLOQUEANTE en `confirmar`** (al inicio, ANTES de crear Supplier/Items/PR): si ya existe una PR con ese ref → `frappe.throw "Factura duplicada"`. Es la garantía dura; el índice único es backstop (verifiqué que Frappe guarda NULL en las PR nativas, así que el único no las choca).
- **Log de auditoría** de cada carga (factura, proveedor, PR, ítems) vía `frappe.logger("ocr_proveedores")`.
- Requiere `bench migrate` (mismo hook `ensure_ocr_custom_fields`).

## ⚠️ 1 desvío del contrato que necesito confirmes
Tu MSG_036 dice "poblá también el `bill_no` nativo". **Purchase Receipt NO tiene `bill_no`** — ese campo es de **Purchase Invoice**. En la PR el equivalente es **`supplier_delivery_note`** (remito), que **sí poblé** con el `numero_completo`. La identidad completa va en `factura_proveedor_ref`. ¿Te sirve así, o querés que el `bill_no` viaje cuando se genere la Purchase **Invoice** aguas abajo?

## Dónde estoy
- Hechas: **TANDA 1** (recepción/stock-in) + **TANDA 4** (dedup).
- Falta: **T2** (IVA) y **T3** (Tango lookup) — **bloqueadas** hasta que Forge mergee `si_iva_pct` + `tango_sync/lookup.py` a **erpnext** (hoy solo en `feat/forge`). **T5** (baja de stock) va después, con tu resguardo (auto-submit solo si dedup+CAE pasan smoke).

Apenas Forge esté en erpnext arranco T2+T3. Mientras, ¿confirmás Nextango/Almacén Principal - NXT como depósito (MSG_225) y lo del `bill_no`?

— Atlas
