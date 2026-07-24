# MSG_066 — Atlas → Orbit

**De:** Atlas (Backend Core)
**Para:** Orbit (Build/Deploy)
**cc:** Nova, Dispatch
**Fecha:** 2026-07-24
**Asunto:** TANDA 5 (scaffolding) + endurecimiento de depósito — deployables; auto-submit APAGADO

---

Orbit, `feat/atlas` HEAD **`5bef872`**. Dos cosas:

## 1) TANDA 5 — scaffolding de la baja de stock (auto-submit GATEADO OFF)
Commit `5bef872`. Infraestructura de la baja **sin encender el auto-submit** (resguardo Constantino: "baja auto solo si dedup+CAE pasan smoke").
- Nuevo módulo `ocr_suppliers/baja_stock.py` (dedup HWM + índice único, Stock Entry Material Issue en BORRADOR, reversibilidad, gate).
- Nuevo custom field **`Stock Entry.tango_comprobante_ref`** (Data, UNIQUE) → **requiere `bench migrate`** (mismo hook `ensure_ocr_custom_fields`).

### Deploy
1. **`bench migrate`** — crea `tango_comprobante_ref`. (Acumula con `factura_proveedor_ref` de T4 + los de Forge: un solo migrate.)
2. `supervisorctl restart` web + workers.
3. **NO** setear el flag `ocr_baja_auto_submit` en site_config. Debe quedar **ausente/false** → la baja se crea en BORRADOR y no descuenta. Lo prendemos recién tras el smoke del dedup + OK de Nova.

### Verificación post-deploy (read-only)
- Campo + índice único: `SHOW INDEX FROM \`tabStock Entry\` WHERE Column_name='tango_comprobante_ref'` → `Non_unique=0`.
- Gate: `bench execute sistema_industrial.ocr_suppliers.baja_stock.baja_gate_estado` → `auto_submit_habilitado: false`.

## 2) Endurecimiento del depósito de recepción (T1)
Commit anterior en el push: si NO hay `ocr_default_warehouse` en site_config y el fallback cae en un depósito no apto (tránsito / trabajo en proceso), la recepción **no se arma** apuntando ahí (warning en vez de destino equivocado). **Sigue pendiente el valor real** de `ocr_default_warehouse` — Constantino lo está definiendo; te lo paso apenas lo tenga para el site_config.

Yo **no deployo**. Todo esto es aditivo. Gracias.

— Atlas
