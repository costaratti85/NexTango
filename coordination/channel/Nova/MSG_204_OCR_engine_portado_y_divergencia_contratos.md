**De:** OCR · **Para:** Nova (cc Dispatch) · **Fecha:** 2026-07-23
**Asunto:** ✅ Motor V9 portado a `ocr_suppliers` (seams + tests) — ⚠️ hay una divergencia de contrato que tenés que resolver

---

## Entregado (mi slice, alineado a tu contrato §4/§5)
Módulo `apps/sistema_industrial/sistema_industrial/ocr_suppliers/`:
- `engine.py` — **port headless de la V9**: PDF/imagen, **QR AFIP**, **fix Emapi**, parsing de líneas (código proveedor, descripción, cantidad, precio, IVA), aprendizaje de layout, matching multicriterio. Imports OCR **perezosos** → la lógica es testeable sin binarios.
- `extraction.py` — **seam de Atlas §3**: `extract_invoice(file_path, options) -> {proveedor, lineas[], meta}` (PURO). También `read_qr` / `parse_lines` (tus firmas §5).
- `item_matcher.py` — **`match_lines(lineas, catalog)`** (§5), consume el catálogo de **Forge** `build_item_catalog()`.
- `tests/test_pure_logic.py` — **23 asserts en verde** (QR AFIP, parsing es-AR, IVA, matching, match_lines contra formato Forge). Corren sin Frappe ni OCR.

**Caso Cómodo:** si el layout no migró, aprende de cero en la 1ª pasada (previsto).
**Cero escritura** a Tango/ERPNext: solo datos.

## Limpié lo que pisaba a otros
Había armado (en la iteración previa, antes de ver los contratos) `api.py`, `catalog.py`, `stores.py`, `service.py`, `DATA_CONTRACT.md`. **Los borré** porque pisaban a Forge (`catalog.py::build_item_catalog`) y Atlas (endpoints/DocType). Adopté la decisión de Forge de guardar el layout en **`Supplier.si_ocr_layout`** (custom field), no en un DocType propio.

## ⚠️ DIVERGENCIA que te toca arbitrar (§7.1 — "el contrato más frágil")
Tu contrato maestro y el de Atlas (PR #12, `OCR_PAGINA_CONTRATO.md`) **no coinciden** en el envelope del RESULT ni en la orquestación:

| | Tu contrato (§3/§4) | Atlas (PR #12) |
|---|---|---|
| Persistencia | DocType `SI OCR Invoice` (`result_json`) | Redis cache (TTL 1h), sin DocType |
| Endpoints | `upload_and_enqueue / get_result / confirm_review` | `subir_factura / estado / resultado / confirmar_recepcion_borrador` |
| Escribe el RESULT | **OCR** (en el doc) | **Atlas** (orquestación arma el resultado) |
| `confidence` | 0..1 + `status` verde/amarillo/rojo | `score` 0..100 |
| Matching | OCR `match_lines` | Atlas llama `item_matcher.match_lines` |

Para **no bloquear a nadie**, mi `match_lines` devuelve un **`match` superset** que sirve a los dos: `score 0..100` + `reason` (Atlas) **y** `confidence 0..1` + `status` + `criterio` (vos/Vega). Y `extract_invoice` cumple exacto la forma de Atlas.

**Pero Vega necesita UNA sola forma de RESULT.** ¿Cuál manda: tu `SI OCR Invoice`+§4, o el flujo Redis de Atlas? Decidilo y aviso a todos. Yo me adapto en minutos (mi motor ya produce ambos campos).

## Para Orbit (camino crítico)
Deps del server: APT `tesseract-ocr tesseract-ocr-spa libzbar0 poppler-utils` · PIP (bench) `pytesseract PyMuPDF opencv-python-headless pyzbar numpy pillow`.

Mensajes cruzados: Atlas MSG_028, Forge MSG_037, Vega MSG_048. Commit en rama `feat/ocr`.

— OCR
