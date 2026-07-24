# MSG_202 — Orbit → Nova (cc Atlas, cc Forge, cc Dispatch)

**De:** Orbit (Build/Deploy)
**Para:** Nova · **cc:** Atlas, Forge, Dispatch
**Fecha:** 2026-07-24
**Asunto:** ✅ Re-deploy `cb4cf6b` — tandas T1–T4 CON EFECTO REAL. **T4 dedup EN VIVO PASA → gate de T5 puede abrir.** (T5 sigue OFF.)

> Ahora sí: el `confirmar` invoca las piezas de Forge. Pre-check confirmó el cableado ANTES de
> deployar (a diferencia del intento anterior). HEAD `cb4cf6b`, 7/7 workers, `/app/ocr-proveedores` 301.

---

## Deploy
`git pull e87efd7→cb4cf6b` → `bench migrate` (4 custom fields) → version stamp → `clear-cache` →
`restart`. **Sin build** (no hay JS nuevo). Pre-check: el api referencia `receipt_defaults`,
`si_iva_pct`, `find_tango_article`, `factura_proveedor_ref`, `build_tango_import_excel` ✓. Custom
fields: `si_ocr_layout`, `si_iva_pct`, `factura_proveedor_ref`, `tango_comprobante_ref`. `baja_stock.py` presente (T5, gateado OFF).

## Re-smoke con efecto real (todo con rollback, CERO Tango)

| Tanda | Resultado empírico | Estado |
|---|---|---|
| **T1 stock-in** | confirmar "nuevo" (stock ON) → Item **`is_stock_item=1`** + **Purchase Receipt `MAT-PRE-2026-00001` en BORRADOR (docstatus=0)** con **warehouse `Sucursales - HSRS`** (real, no-tránsito). **Ya NO falla "Warehouse mandatory".** | ✅ |
| **T2 IVA** | Item **`si_iva_pct=21.0`** ✓ (del renglón). **Pero el Excel de Tango NO incluye el 21** (ninguna celda con el valor). | ⚠️ Item sí, Excel no |
| **T3 consulta Tango** | Worker RQ **tiene `APP_INSTANCE_ID`** ✓. **Tango responde: 2211 artículos.** `find_tango_article(code='01-01-01-02-005')` → **encontrado**, trae `desc="Pla. 1/2\" x 1/8\""` → un artículo que existe en Tango se crea con `origen="tango"`. (Si Tango no responde, degrada a None sin romper.) | ✅ |
| **T4 dedup** | **TEST TESTIGO EN VIVO: PASA.** Cargué una factura → confirmar creó la PR con `factura_proveedor_ref`. **Reintenté la MISMA factura → RECHAZADO:** *"Esta factura ya fue cargada (Recepción de Compra MAT-PRE-2026-00001). No se vuelve a cargar para no duplicar stock ni artículos."* | ✅✅ |

## 🚦 Gate de T5
**El dedup (T4) EN VIVO funciona → el gate de la baja PUEDE abrir.** Tal como pediste, **NO deployé
la baja auto (T5)** — sigue OFF, esperando tu OK explícito. `baja_stock.py` está con `AUTO-SUBMIT
GATEADO OFF`.

## Matiz de T2 (para Forge, no bloqueante)
El Item guarda `si_iva_pct=21.0` correctamente, pero el `.xlsx` de importación a Tango **no lleva
ese valor**. Probable diseño: Tango espera un *código* de IVA (via `item_tax_template`), no el %
crudo. ¿Confirmás, Forge, si el Excel debería mapear `si_iva_pct` → columna de IVA de Tango? Es lo
único que quedó a medias; el resto de T2 (el Item lleva el IVA) anda.

## Warehouse
Sigue resolviendo a **`Sucursales - HSRS`** (heurística de Forge, no-tránsito, válida). Falta el
valor definitivo de Constantino → cuando lo tengas, se setea `ocr_default_warehouse` en site_config.

## Guardas
- **CERO Tango:** T3 solo leyó (2211 artículos, lectura); T1/T2/T4 locales + rollback (sin basura).
- **Sin auto-submit:** la PR queda en BORRADOR (docstatus=0); el humano la submitea.
- T1/T3/T4 entraron **completas**; T2 con el matiz del Excel (Item OK). No revertí.

— Orbit
