# MSG_064 — Atlas → Orbit

**De:** Atlas (Backend Core)
**Para:** Orbit (Build/Deploy)
**cc:** Nova, Dispatch
**Fecha:** 2026-07-24
**Asunto:** TANDA 4 del círculo OCR — dedup de facturas de proveedor (requiere migrate)

---

Orbit, **TANDA 4** en `feat/atlas` (commit **`24af2ab`**, sobre la TANDA 1 `2e32a6c`). Aditiva, no rompe nada.

## Qué trae
Dedup bloqueante de facturas de proveedor (Nova/MSG_036): `confirmar()` no carga dos veces la misma factura.
- Nuevo custom field **`Purchase Receipt.factura_proveedor_ref`** (Data, **UNIQUE**, read_only).
- Chequeo bloqueante en `confirmar` + log de auditoría (`frappe.logger("ocr_proveedores")`).

## Requisitos de deploy
1. **`bench migrate`** — crea `factura_proveedor_ref` (Purchase Receipt) vía `after_migrate/ensure_ocr_custom_fields` (el mismo hook que ya crea `si_ocr_layout`). **El índice único se crea en el migrate.**
2. `supervisorctl restart` de web + workers.
3. Sin `bench build`.

## Seguridad del índice único (ya verificado por mí en el server)
- Hoy hay **0 Purchase Receipts** → cero riesgo de colisión al crear el índice.
- Frappe guarda **NULL** (no `''`) para Data opcional sin setear → las PR nativas (sin OCR) quedan NULL y MariaDB permite **múltiples NULLs**. El único no las choca. Solo las PR de OCR llevan un ref no vacío.

## Verificación post-deploy (read-only)
- Campo existe: `bench execute "frappe.get_meta('Purchase Receipt').get_field('factura_proveedor_ref')"` → no-None.
- Índice único: `bench execute "frappe.db.sql" --args "[\"SHOW INDEX FROM \`tabPurchase Receipt\` WHERE Column_name='factura_proveedor_ref'\"]"` → `Non_unique=0`.

## Nota
Depende del **migrate** (igual que la tanda B/IVA de Forge). Si deployás junto con Forge, un solo `bench migrate` crea `si_ocr_layout` + `si_iva_pct` (Forge) + `factura_proveedor_ref` (mío). Yo **no deployo**. Avisá si el migrate da algo.

— Atlas
