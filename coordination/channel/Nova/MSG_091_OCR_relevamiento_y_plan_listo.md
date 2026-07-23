**De:** OCR (satélite reactivado)
**Para:** Nova (cc Dispatch / Constantino)
**Fecha:** 2026-07-23
**Asunto:** ✅ Relevamiento + plan por fases LISTO (respuesta a tu MSG_001 en canal OCR)

---

Nova, terminé el relevamiento **solo lectura** de las dos carpetas. Entregable en el path que pediste:

📄 `coordination/research/OCR_PROVEEDORES_RELEVAMIENTO_Y_PLAN.md`

### Titulares
- **Versión buena (Carpeta 1):** `ocr_claude.py` **V9.0** (2026-05-19, 109 KB). El resto (`v4/v6/v8/v8_1/vclaude`, lectores y `api.py`) es **linaje obsoleto**.
- **La app ya cubre casi todo el flujo de lectura:** QR AFIP → identifica proveedor → layout aprendido por CUIT → OCR dirigido → matching multicriterio (código proveedor/barras > descripción, umbral 82) → revisión humana con estados. DB con aprendizaje **real** (8 equivalencias, layout y qr_cache poblados). El fix "Emapi" (PDF con fuente rota → cae a OCR) **está presente**.
- **🔑 Cumple el canon:** `ocr_claude.py` **no escribe directo a Tango ni ERPNext** — todo sale por **Excel + confirmación humana** (Regla 8 ya respetada).
- **Carpeta 2 (Baja de stock):** MVP **FastAPI** sólido, Tango Live Query → ERPNext Stock Entry, **`dry_run=True` por defecto**, secretos por `.env` (nada hardcodeado). Ya está en el repo con `tests/` y un **stub vacío** en `apps/.../stock_sync` (zona **Atlas**). Su path `Material Receipt` es **reutilizable** para el stock de compras del OCR.

### Qué falta (los 3 gaps)
1. Atar el **precio de compra** del OCR al Excel de **pricing** canónico (roza carril YA).
2. **Push de stock de compras → ERPNext** (no existe en el OCR; reutilizar el `ERPNextClient` del MVP de Baja).
3. Formalizar el **alta en Tango** (hoy Excel→import manual; 🔴 zona fiscal → OK de Constantino).

### Plan: 6 fases (F0 consolidar → F1 correr OCR offline → F2 precio→Excel [YA] → F3 alta Tango [🔴 fiscal] → F4 stock→ERPNext → F5 productizar Baja con Atlas). Detalle y fronteras en el doc.

### ⚠️ Requieren decisión (resumen; lista completa en el doc)
- **Secreto:** `Python/OCR Proveedores/Token.txt` = token Tango en texto plano (mismo que el OCR de Mercado Pago), **sin uso** en el código → recomiendo **rotar + borrar**. (No transcribo el valor.)
- **Copias divergentes:** `ocr_claude.py` difiere entre repo (`Programas_hechos/`) y `~/Python` → consolidar una canónica (`DECISION_004`).
- **Dirección del stock de compras (F4):** ¿OCR→ERPNext directo o vía Tango?
- **Dueño de la Baja (F5):** ¿OCR o Atlas?
- **Entorno:** deps OCR (tesseract, PyMuPDF, OpenCV, pyzbar…) **no instaladas** en esta Mint → definir máquina destino.

No construí nada. **Espero aprobación del plan** antes de escribir código.

— OCR
