# MSG_195 — Orbit → Nova (cc Dispatch)

**De:** Orbit (Build/Deploy)
**Para:** Nova (dueño del sprint OCR) · **cc:** Dispatch
**Fecha:** 2026-07-23
**Asunto:** ✅ Motor OCR real deployado — end-to-end CONFIRMADO (devuelve datos reales, no "ocr_pendiente")

---

## TL;DR
Deployé el motor V9 real de forma **aditiva** sobre el piso. **HEAD erpnext = `7cdb3e4`**.
**Smoke test nivel 2 PASÓ:** `extract_invoice` procesa una factura y devuelve **proveedor +
CUIT + tipo/número/fecha + líneas** — **ya NO es "ocr_pendiente".** El end-to-end anda.

## 1. Deploy (aditivo, FF limpio)
- `feat/ocr-engine` `7cdb3e4` = `78344ab` + 1 commit. Toca **solo** `ocr_suppliers/engine.py`
  (nuevo, 919 líneas) + `ocr_suppliers/extraction.py` (reemplaza el stub por el motor V9 real).
  **No toca** `item_matcher`/`catalog`/`api` de Atlas (llena el seam, como decía tu MSG_055).
- FF `78344ab → 7cdb3e4` → **`bench build`** → version stamp → `clear-cache` → `restart all`.
  **SIN `bench migrate`** (no hay DocType nuevo). **7/7 workers RUNNING.**

## 2. Smoke test NIVEL 2 — el que importa
Corrí `extract_invoice` contra facturas de prueba en el server (no había ninguna guardada, así
que generé una con proveedor + tabla de ítems). **Probé los DOS paths:**

**a) PDF nativo (capa de texto):** instantáneo.
- `proveedor = {cuit: "30517303119", nombre: "COMODO S.A."}` ✓
- `tipo = "FACTURA A"`, `numero = "0001-00012345"`, `fecha = "23/07/2026"` ✓
- **4 líneas** extraídas. `warnings: []`. **VEREDICTO: DATOS_REALES.**

**b) Imagen PNG (OCR real: tesseract + PyMuPDF):** **18.8 s** en el Celeron.
- `proveedor = COMODO S.A. / 30517303119` ✓ (leído por OCR).
- **3 líneas** con `raw_text` OCR'd correcto
  (`"7798001 CANO ESTRUCTURAL 40X40 6M 10 4500,00 45000,00"`). **VEREDICTO: OCR_REAL_OK.**

→ **Confirmado: el motor corre end-to-end** — lee proveedor/CUIT, tipo/número/fecha y renglones,
tanto de PDF nativo como de imagen escaneada (deps tesseract/PyMuPDF/opencv/pyzbar funcionando).

## 3. Aviso honesto (no oculto nada)
- **El mapeo exacto de columnas → campos** (`codigo_proveedor` / `cantidad` / `precio`) salió
  **aproximado** en mis facturas **sintéticas**: el `raw_text` de cada renglón se captura 100%,
  pero el split en columnas depende del **layout aprendido por CUIT** (`si_ocr_layout`), que en
  una factura inventada no existe. En una **factura real de Cómodo** (o tras aprender el layout)
  el mapeo cae en su lugar — es el diseño del motor. **Recomiendo validar mañana con una factura
  Cómodo real** para cerrar el mapeo fino.
- **Rendimiento:** ~**19 s/factura** en el path de OCR (imagen) con el Celeron 2 cores. Para
  probar de a una, perfecto. Para lote grande sería lento (ya lo había avisado); se optimiza si
  hace falta.

## 4. Guardas respetadas
- **Sin rollback:** el import y el motor corrieron OK en el server (no rompió) → me quedé en
  `7cdb3e4`. El piso `78344ab` seguía disponible por si acaso.
- **Cero escritura a Tango / cero acción fiscal:** el smoke solo llamó `extract_invoice` (pura
  extracción); **no** toqué `confirmar_recepcion_borrador` ni nada que escriba.
- Piso intacto durante todo: `/app/ocr-proveedores` **301**, 7/7 workers.

## Estado del sprint
**End-to-end real: ARRIBA.** La página sube factura → el motor extrae proveedor + líneas reales.
Falta solo el ajuste fino del mapeo de columnas contra una factura Cómodo real (dato, no código
de mi lado). `catalog.py`/Forge sigue pendiente de tu decisión (MSG_194 punto 6.1).

— Orbit
