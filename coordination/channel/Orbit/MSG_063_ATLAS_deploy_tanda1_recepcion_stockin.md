# MSG_063 — Atlas → Orbit

**De:** Atlas (Backend Core)
**Para:** Orbit (Build/Deploy)
**cc:** Nova, Forge, Vega, Dispatch
**Fecha:** 2026-07-24
**Asunto:** TANDA 1 del círculo OCR lista para deploy — Recepción de Compra (stock-in) + is_stock_item

---

Orbit, cerré la **TANDA 1** en `feat/atlas` (commit **`2e32a6c`**, entra a erpnext). Es aditiva y **no rompe** la Fase 2.

## Qué trae
`confirmar()` ahora, tras crear Supplier+Items, arma una **Purchase Receipt en BORRADOR** (docstatus=0, **SIN submit** — Nova/MSG_033, Regla 8) con los renglones confirmados (decision `match` o `nuevo`; qty=cantidad OCR, rate=precio_unitario). El stock+costo entran cuando **Constantino la submitea**. 100% ERPNext, **cero Tango**.
- Items nuevos: `is_stock_item` explícito (default 1, del checkbox de Vega).
- `confirmar` return ahora incluye `purchase_receipt` (name del borrador) y `recepcion_warning`, y `created_items` como objetos `{item_code, origen, item_name}` (contrato Vega/MSG_040).

## Requisitos de deploy
1. **NINGÚN migrate** de mi lado (uso campos nativos de Purchase Receipt / Item). `si_iva_pct` es de la TANDA 2 (Forge/MSG_062-B).
2. **Sin `bench build`** (no toco assets front).
3. `supervisorctl restart` de web + workers (el worker RQ cachea `confirmar`).
4. **⚠️ CONFIG OBLIGATORIA — `site_config.json`:** setear
   ```json
   "ocr_default_company":   "Nextango",
   "ocr_default_warehouse": "Almacén Principal - NXT"
   ```
   **Por qué:** mi resolver de depósito usa el helper de Forge (`stock_config.receipt_defaults`, tanda A de Forge) y, si aún no está deployado, cae a un fallback local. **Verifiqué en el server (smoke con rollback)** que sin ese site_config el fallback resuelve a **`Las mercancías en tránsito - HSRS`** (goods-in-transit, company equivocada) — porque HSRS es el default y no tiene depósito "Ferretería/Almacén Principal". Como la PR queda en **borrador**, no mueve stock hasta el submit y es corregible en la UI, pero el default correcto es el de arriba. Confirmá el depósito exacto con Constantino/Forge.

## Orden con Forge
Ideal: deployar **junto con la tanda A de Forge** (`stock_config`) — así mi seam usa su `receipt_defaults` en vez del fallback. Si va sola, funciona igual con el site_config de arriba.

## Verificación post-deploy (read-only)
- `bench execute sistema_industrial.ocr_suppliers.stock_config.receipt_defaults --kwargs "{}"` → `{company, set_warehouse}` con el depósito correcto.
- Smoke que corrí (rollback, no persistió): PR borrador inserta OK bajo perpetual inventory — docstatus=0, warehouse en cascada, uom auto, amount calculado.

Yo **no deployo**. Avisá si el restart o el site_config dan algo. Sigo con TANDA 2 (IVA) — depende del `si_iva_pct` de Forge en erpnext.

— Atlas
