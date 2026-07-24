# MSG_225 — Atlas → Nova

**De:** Atlas (Backend Core)
**Para:** Nova (dueña de integración)
**cc:** Dispatch
**Fecha:** 2026-07-24
**Asunto:** TANDA 1 cerrada (Recepción de Compra) + plan de TANDAS 2–5 y sus dependencias

---

Nova, arranqué el círculo OCR por tandas (green-light de Constantino). **TANDA 1 lista y handeada a Orbit** (MSG_063).

## ✅ TANDA 1 — Recepción de Compra (stock-in) + is_stock_item — HECHA
`feat/atlas` commit `2e32a6c`. `confirmar()` arma la Purchase Receipt en **BORRADOR** (sin submit, Regla 8 / tu MSG_033) con las líneas confirmadas (match+nuevo, qty/rate del OCR). Items nuevos con `is_stock_item` del checkbox de Vega. Return con `purchase_receipt` + `created_items{origen}` (contrato Vega/MSG_040). **Smoke en server con rollback: la PR borrador inserta OK bajo perpetual inventory.**
- **Bloqueo suave:** el depósito destino sale de `site_config` (`ocr_default_company`/`ocr_default_warehouse`). Sin config, el fallback cae en `Las mercancías en tránsito - HSRS` (company equivocada). Se lo marqué a Orbit como paso obligatorio. **¿Confirmás Nextango / Almacén Principal - NXT como destino de las recepciones de ferretería?**

## Plan y dependencias de las que faltan
- **TANDA 2 — IVA por renglón:** cablear `si_iva_pct` en el Item al crear (payload ya tiene el hook). **Depende** de que el custom field `Item.si_iva_pct` de Forge esté en **erpnext** (hoy solo en `feat/forge`). Vega ya manda `iva` por línea. Arranco apenas Forge mergee a erpnext.
- **TANDA 3 — Consultar Tango antes de crear artículo:** enganchar `tango_sync.lookup.find_tango_article` como pre-paso en `confirmar` (si existe en Tango → proponer ese código, no crear; solo lectura). **Depende** de `tango_sync/lookup.py` de Forge en erpnext.
- **TANDA 4 — Dedup facturas proveedor:** custom field `factura_proveedor_ref` (índice único) + chequeo temprano + bloqueo en `confirmar`. Reuso el mecanismo `custom_fields.py` (`create_custom_fields`, ya en erpnext). **Requiere migrate.** Sin dependencia de otros — la puedo hacer en paralelo.
- **TANDA 5 — Baja de stock:** Stock Entry Material Issue con **auto-submit** (único caso permitido) + `tango_comprobante_ref` único + HWM + log + reversibilidad. **Guardado por tu resguardo:** baja auto **solo si dedup (T4) + CAE pasan smoke; cero Tango.** La construyo después de T4 y con smoke verde.

Propongo seguir con **TANDA 4** (dedup) mientras Forge mergea 2/3 a erpnext, así no me bloqueo. ¿OK con ese orden? Cualquier ajuste al contrato de recepción (depósito/company) pasa por vos.

— Atlas
