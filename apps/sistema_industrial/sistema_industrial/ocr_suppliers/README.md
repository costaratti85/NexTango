# ocr_suppliers — motor OCR de facturas de proveedor (server-side)

Port headless de la V9 de escritorio (`ocr_claude.py`). El OCR **sugiere**; el humano
**confirma** (Regla 8). **No** escribe en Tango/ERPNext: devuelve datos para revisión.

Construido contra la interfaz maestra de Nova
(`coordination/research/CONTRATO_INTEGRACION_OCR_MVP.md`) y los seams de Atlas
(`OCR_PAGINA_CONTRATO.md §3`).

## Piezas (mi slice)
- `engine.py` — motor portado (librería): PDF/imagen, QR AFIP, **fix Emapi**, parsing de
  líneas, aprendizaje de layout, matching multicriterio. Imports pesados perezosos →
  la lógica de texto/matching es testeable sin OCR.
- `extraction.py` — **SEAM de Atlas**: `extract_invoice(file_path, options)` (puro:
  archivo → {proveedor, lineas[], meta}). También `read_qr` / `parse_lines` (firmas Nova).
- `item_matcher.py` — **`match_lines(lineas, catalog)`** (Nova §5): matching multicriterio.
  Consume el catálogo en formato de **Forge** `build_item_catalog()`. Devuelve un `match`
  superset: `score 0..100` + `reason` (Atlas) y `confidence 0..1` + `status`
  (verde/amarillo/rojo) + `criterio` (Nova/Vega).
- `tests/test_pure_logic.py` — 23 asserts de lógica pura (sin Frappe ni OCR). Todos OK.

## NO es mi slice (lo owna otro; no lo toco)
- `catalog.py::build_item_catalog()` → **Forge** (PR #10).
- Endpoints whitelisted + DocType/orquestación → **Atlas** (PR #12).
- Layout persistido en `Supplier.si_ocr_layout` (custom field JSON) → **Forge**.
  `extract_invoice` lo recibe por `options.layout_por_cuit` y devuelve lo aprendido en
  `meta.layout_learned` para que la orquestación lo persista.
- UI / grilla de revisión → **Vega** (PR #11).

## Dependencias del server (las instala Orbit — F1)
APT: `tesseract-ocr` `tesseract-ocr-spa` `libzbar0` `poppler-utils`.
PIP (bench env): `pytesseract` `PyMuPDF` `opencv-python-headless` `pyzbar` `numpy` `pillow`.
