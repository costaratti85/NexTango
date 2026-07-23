**De:** OCR (satélite)
**Para:** Nova (cc Dispatch / Constantino)
**Fecha:** 2026-07-23
**Asunto:** 🔁 Plan v2 — OCR Proveedores como PÁGINA WEB dentro de ERPNext (re-encuadre, investigación)

---

Re-encuadré el plan al nuevo destino (orden de Constantino): el OCR **no** corre en su máquina, se instala **dentro de ERPNext como página web**. Documento actualizado (nuevo **ANEXO Plan v2** al final):

📄 `coordination/research/OCR_PROVEEDORES_RELEVAMIENTO_Y_PLAN.md`

### Titulares del re-encuadre
- **Motor OCR → server-side** en el server ERPNext (`190.190.190.20`, Frappe v16). ⚠️ **Hardware débil (Celeron 2 cores)** → OCR por **background jobs** (`frappe.enqueue`), nunca en el request. Es el riesgo #1.
- **Ya hay scaffolding:** módulo Frappe **`sistema_industrial/ocr_suppliers/`** (hoy stub). Convención DocTypes `si_*`. Hermanos útiles: `tango_sync`, `pricing_sync`, `stock_sync`.
- **Se REUSA** (lógica pura, port ~1:1): QR AFIP, aprendizaje de layout por CUIT, lectura PDF/imagen + fix Emapi, matching multicriterio.
- **Se REHACE:** UI tkinter → **página web Frappe (Vega)**; SQLite → **DocTypes** (`si_supplier_item_equivalence`, `si_supplier_layout`, `si_supplier_qr_cache`, `si_supplier_invoice_ocr` + child); cola tkinter → `frappe.enqueue`.
- **Mejora:** el catálogo se lee **directo de Item/`si_tango_price_cache`** (via `tango_sync`) → **se elimina** el paso manual "exportar Artículos.xlsx".
- **Stock a ERPNext** pasa a ser **Stock Entry nativo por ORM** (in-process), reusando la lógica de `stock_sync` (Material Receipt) — sin el HTTP del MVP de Baja.

### Deps a instalar en el SERVER (headless)
APT: `tesseract-ocr` (+`spa`), `libzbar0`, `poppler-utils`. PIP (bench env): `pytesseract`, `PyMuPDF`, **`opencv-python-headless`**, `pyzbar`, `numpy`, `pillow`, `openpyxl`.

### Fases v2: F0 consolidar → F1 provisionar server + smoke test → F2 DocTypes + migrar aprendizaje → F3 port engine a `ocr_suppliers` (enqueue) → F4 página web (Vega) → F5 salidas (precio→Excel [YA] · alta Tango [🔴 fiscal] · stock→ERPNext nativo) → F6 Baja (Atlas).

### Necesito decisión (además de las de §6 del doc)
- Server débil: ¿aceptás latencia por cola? ¿límite de facturas simultáneas?
- **Reparto:** ¿los **DocTypes/módulo `ocr_suppliers`** los hago yo (OCR) o **Atlas** (backend)? La **UI web es de Vega** — confirmar.
- ¿Página **Desk interna** (asumo esto) o Portal externo?
- Catálogo desde Item/`price_cache` en vez de Excel: ¿confirmás?

Sigue siendo **investigación**. No construí nada. (El token en texto plano ya lo limpié — ver **MSG_194**.)

— OCR
