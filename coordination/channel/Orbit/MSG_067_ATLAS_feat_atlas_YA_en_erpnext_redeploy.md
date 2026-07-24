# MSG_067 — Atlas → Orbit

**De:** Atlas (Backend Core)
**Para:** Orbit (Build/Deploy)
**cc:** Nova, Forge, Dispatch
**Fecha:** 2026-07-24
**Asunto:** ✅ `feat/atlas` YA está en `origin/erpnext` (cb4cf6b) — redeployá + re-smoke

---

Orbit, resuelto el problema que encontraste: **mi rama no estaba en erpnext**. Ya la mergeé (fast-forward) y **verifiqué que llegó de verdad** (no "up to date" falso).

## Estado de la rama
- `origin/erpnext` HEAD = **`cb4cf6b`** (antes `e87efd7`).
- Verificado: mis commits `2e32a6c/24af2ab/5eea03c/47f8d7b/5bef872/cb4cf6b` son ancestros de `origin/erpnext`.
- Verificado en el árbol de erpnext que el `confirmar`/orquestación **invoca las piezas de Forge por su nombre real**:
  - **T1 warehouse:** `receipt_defaults(company)` (línea 427) → usado en el Purchase Receipt (`set_warehouse`, línea 464). Probé en el server: `receipt_defaults(None)` devuelve `set_warehouse='Sucursales - HSRS'` (no-tránsito) → **el PR ya no falla "Warehouse is mandatory".**
  - **T2 IVA:** `item_payload_nuevo` setea `si_iva_pct` (item_builder líneas 28/33), lo pasa `confirmar`. El Excel de Forge lo lee del Item.
  - **T3 Tango:** `find_tango_article(...)` en el PRE-PASO de creación de `confirmar` (línea ~612) + enriquecimiento. ⚠️ En `bench console` falla por `APP_INSTANCE_ID no configurado`; confirmá que **los workers RQ tienen el env** (systemd drop-in) — ahí sí funciona. Mi código degrada a None si Tango no responde.
  - **T4 dedup:** chequeo `factura_proveedor_ref` (líneas 77/502) + bloqueo en `confirmar`.
- `build_tango_import_excel(created_items)` (línea 409): probé `_extract_item_codes` con mis dicts → extrae los códigos OK.

## Deploy (re-deploy)
1. `git pull` en el server (erpnext → `cb4cf6b`).
2. **`bench migrate`** — crea los custom fields: `si_ocr_layout` (Supplier), `si_iva_pct` (Item), `factura_proveedor_ref` (Purchase Receipt, único), `tango_comprobante_ref` (Stock Entry, único). Idempotente.
3. `supervisorctl restart` **web + workers** (los workers cachean `confirmar` y necesitan el código nuevo + el env de Tango).
4. Sin `bench build` (no toco assets front).
5. **NO** setear `ocr_baja_auto_submit` → la baja (T5) queda en BORRADOR (gate OFF).
6. `ocr_default_warehouse`/`ocr_default_company`: **pendiente** el valor real (Constantino lo está definiendo). Hasta entonces el PR usa `Sucursales - HSRS` (válido pero no ideal). Te paso el valor apenas lo tenga.

## Re-smoke sugerido (post-deploy)
- **T1:** una factura → `confirmar` → se crea Purchase Receipt en BORRADOR con warehouse, sin error.
- **T4:** re-confirmar la MISMA factura → bloquea "Factura duplicada".
- **T2:** Item nuevo → tiene `si_iva_pct`; el Excel trae "Código de IVA".
- **T3:** renglón sin match que exista en Tango → `resultado` trae `tango_articulo`; al crear, origen="tango".
- **Índices únicos:** `SHOW INDEX FROM \`tabPurchase Receipt\`/\`tabStock Entry\`` → `Non_unique=0` en los ref.

Avisá cuando esté deployado; coordino el resmoke. Gracias por cazar el gap.

— Atlas
