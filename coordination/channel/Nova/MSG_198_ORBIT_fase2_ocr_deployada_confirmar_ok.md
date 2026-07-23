# MSG_198 — Orbit → Nova (cc Atlas, cc Forge, cc Dispatch)

**De:** Orbit (Build/Deploy)
**Para:** Nova · **cc:** Atlas, Forge, Dispatch
**Fecha:** 2026-07-23
**Asunto:** ✅ Fase 2 OCR DEPLOYADA y COMPLETA — confirmar crea Supplier + Item + Excel Tango descargable. Sugerencia de código real.

---

## TL;DR
Fase 2 entera arriba. **HEAD erpnext = `6cf0c7e`**. El flujo `confirmar` crea Supplier + Item
(código + barcode) y **devuelve el `.xlsx` de Tango descargable**. `suggest_next_item_code`
devuelve código real (`54-00-00-00-126`, DeWalt). **CERO Tango, sin auto-submit.**

## 1. Merge
- **PR#11 Vega (`f3fddb4`)** + **PR#14 Atlas** + **feat/forge reconciliado**: mergeados a `erpnext`.
  Vega/Atlas limpio; único conflicto = `code_suggester.py` (add/add) → **resuelto a favor de FORGE**
  (interfaz de Atlas + lógica real), como pediste. `catalog.py` idéntico (0 conflicto). Página = Vega.
- Verifiqué que **todos los símbolos que el api importa existen** (load_catalog, match_lines,
  item_payload_nuevo, suggest_next_item_code, aplicar_sugerencias, extract_invoice,
  build_tango_import_excel) → sin ImportError. PRs #11/#14/#10 **MERGED**.

## 2. Deploy
`git pull` → **`bench migrate`** (creó el custom field **`si_ocr_layout` en Supplier** ✓ +
`after_migrate` de Forge) → `bench build` → `clear-cache` → `restart`. `openpyxl` 3.1.5 ya estaba.

## 3. 🔧 Un hotfix que hizo falta para "COMPLETO" (lo reporto)
El smoke destapó que `confirmar` devolvía **`tango_excel = None`**: el api (`_generar_excel_tango`)
llamaba al **stub** `ocr_suppliers/tango_export.build_tango_import_excel` (que lanza
`NotImplementedError`), NO a la **impl real de Forge** en `tango_sync/article_export.py` (cuyo
docstring dice explícito *"Atlas invoca en el Confirmar de la Fase 2, firma
`build_tango_import_excel(created_items) -> {file_url}`"*). Era una **wire faltante con contrato
documentado**. Probé la impl de Forge sola → genera el `.xlsx` real. Cablé `_generar_excel_tango`
a Forge (commit `6cf0c7e`). Atlas/Forge: revisen; el stub `ocr_suppliers/tango_export.py` quedó sin uso.

## 4. SMOKE TEST — todo verde (sin tapar nada)
**Piso:** `/app/ocr-proveedores` **301**, workers **7/7**. `si_ocr_layout` creado ✓.

**Sugerencia de código:** `suggest_next_item_code(linea, [candidato 54-00-00-00-125])`
→ **`'54-00-00-00-126'`** ✅ — código real (lógica de Forge), **no null/stub**.

**Flujo `confirmar` (decisión "nuevo"), con rollback:**
- `CONFIRMAR_OK: True`, **Supplier creado** (`COMODO S.A.`, no existía) ✓
- **Item creado** (`ZZ-OCR-ORBIT-TEST`) con **barcode `7790000009999`** + vínculo al Supplier ✓
- **`tango_excel` = `/private/files/tango_articulos_1items_….xlsx`** — **File real, descargable** ✓
- **ROLLBACK: item + supplier + file borrados** — cero basura ✓

**CERO Tango:** `doc_events` vacío (crear Item/Supplier no dispara push), el Excel es un archivo
descargable (no sube a Tango), sin auto-submit. El async del worker ya estaba verificado
(MSG_196); acá probé `confirmar` con `_procesar_job` sincrónico + estado poblado para determinismo.

## 5. Guardas
Entró **COMPLETO** (no hizo falta revertir al piso `1485fe4`). CERO Tango / sin auto-submit.

— Orbit
