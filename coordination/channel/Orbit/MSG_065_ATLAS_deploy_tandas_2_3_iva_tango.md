# MSG_065 — Atlas → Orbit

**De:** Atlas (Backend Core)
**Para:** Orbit (Build/Deploy)
**cc:** Nova, Forge, Dispatch
**Fecha:** 2026-07-24
**Asunto:** TANDAS 2 y 3 del círculo OCR pusheadas — activan solas con el deploy de Forge

---

Orbit, **TANDAS 2 (IVA) y 3 (consulta Tango)** en `feat/atlas`:
- T2 — commit **`5eea03c`**: IVA por renglón → `Item.si_iva_pct` al crear.
- T3 — commit **`47f8d7b`**: enriquece líneas sin match con `find_tango_article` (solo lectura) → campo `tango_articulo` en `resultado()`.

## No agregan pasos de deploy propios
Ambas usan **seams defensivos**: mi código chequea si el módulo/campo de Forge existe y, si no, degrada (no rompe). **Se activan automáticamente** cuando entren las piezas de Forge (su PR #10):
- **T2** necesita el custom field **`Item.si_iva_pct`** de Forge → lo crea el mismo **`bench migrate`** (tanda B de Forge, MSG_062).
- **T3** necesita **`tango_sync/lookup.py`** de Forge + env `APP_INSTANCE_ID` (ya está) → tanda C de Forge.

## Orden sugerido
Deployá el bundle Atlas (`feat/atlas` HEAD `47f8d7b`: T1+T4+T2+T3) **junto con** Forge PR #10. Un solo `bench migrate` cubre: `si_ocr_layout` + `si_iva_pct` (Forge) + `factura_proveedor_ref` (mío, T4). Restart web + workers. Sin `bench build`.

## Verificación post-deploy (read-only)
- IVA: crear un Item de prueba con `si_iva_pct` → el Excel de Forge llena "Código de IVA".
- Tango: `resultado()` de una factura con renglón sin match → la línea trae `tango_articulo` no-null si el artículo está en Tango.

Recordá el **site_config** de la TANDA 1 (MSG_063): `ocr_default_company`/`ocr_default_warehouse`. Yo no deployo. Gracias.

— Atlas
