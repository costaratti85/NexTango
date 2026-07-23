**De:** OCR-MELI (sesión satélite)
**Para:** Nova (→ Dispatch / Constantino)
**Fecha:** 2026-07-20
**Asunto:** OCR Mercado Pago — archivo canónico con fix confirmado + limpieza de copias

---

## 1. Decisión aplicada
- Se **descarta** trabajar sobre el share `.9`. La versión **canónica/única** es:
  `/home/costa/Claude/Cloud Code OCR Mercadopago/ocr_transferencias.pyw`
  Constantino copiará desde ahí a donde haga falta (incluida `.9`) cuando corresponda.

## 2. Fix confirmado en el canónico
- Separadores **es-AR fijos** (`.`=miles, `,`=decimales), **independiente del locale del SO** → `SEP_MILES, SEP_DECIMAL = ".", ","`.
- `formatear_importe()` reescrito a es-AR fijo + **siempre 2 decimales** (redondeo en centavos enteros).
- Parseo con regla fija `_ocr_monto_a_float` (esta versión ya lo traía; correcto).
- `ast.parse` → **sintaxis OK**. Probado bajo locale es-AR y C/POSIX → salida idéntica y correcta (`1.234.567,89`, `234,50`, `15.000,00`).

## 3. Copias eliminadas (objetivo: dejar UNA sola)
Borradas:
- `~/Claude/Cloud Code OCR Mercadopago/Version 1 lista/ocr_transferencias.pyw` (jun 3) — y la carpeta `Version 1 lista/` (quedó vacía).
- `~/Claude/Cloud Code OCR Mercadopago/__pycache__/ocr_transferencias.cpython-314.pyc` (bytecode viejo, jun 3) — y la carpeta `__pycache__/` (quedó vacía).
- `/home/costa/ocr_transferencias.pyw` (la copia que Constantino había pegado; jun 8, vieja y con el bug).

Conservados:
- ✅ **Canónico:** `~/Claude/Cloud Code OCR Mercadopago/ocr_transferencias.pyw` (jul 20, con fix).
- ✅ **Backup:** `~/Claude/Cloud Code OCR Mercadopago/ocr_transferencias.pyw.bak_20260720` (versión previa al fix, por las dudas). **Constantino decide si lo borra más adelante.**

## 4. Pendiente de decisión de Constantino (fuera del scope que se me dio)
- Existe otra copia **fuera de `~/Claude/`**: `/home/costa/Python/OCR Mercadopago/ocr_transferencias.py`
  - Es un **prototipo anterior** (27-may, 26 KB, extensión `.py`, dependencias tesseract/pandas). Tiene el mismo patrón con bug (`_detect_separators`).
  - **No lo borré** porque quedaba fuera del scope indicado (`~/Claude/`). ¿Lo elimino también, o se conserva?
- La carpeta `~/Claude/Cloud Code OCR Mercadopago/OCR Mercadopago Primera version/` **no** contiene copias del `.pyw` (solo `debug_ocr.py`, `instalar_requerimientos.py` y 2 archivos basura de 0 bytes). No la toqué.

## Estado
✅ Tarea cerrada: canónico con fix es-AR + 2 decimales, y una sola copia viva bajo `~/Claude/` (más el backup). Espero decisión sobre el `.py` de `~/Python/`.

— OCR-MELI
