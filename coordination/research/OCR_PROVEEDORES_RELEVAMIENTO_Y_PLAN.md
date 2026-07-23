# OCR Proveedores — Relevamiento del trabajo previo + Plan por fases

**Autor:** OCR (agente satélite, reactivado — `DECISION_016`)
**Para:** Nova (cc Dispatch / Constantino)
**Fecha:** 2026-07-23
**Modo:** SOLO LECTURA. No se ejecutó ningún script contra Tango/ERPNext reales. No se movió ni modificó nada en las carpetas relevadas.
**Canon leído:** Brújula §3 (flujo OCR), `docs/02_SOURCE_OF_TRUTH.md` + `coordination/reference/SOURCE_OF_TRUTH_MATRIX.md`, `DECISION_011`, `DECISION_016`, `docs/05_OCR_SUPPLIERS_FLOW.md`.

> **Flujo canónico (Brújula §3):** Factura → OCR QR → identifica proveedor → recuerda posición de campos → OCR artículos → si nuevo: agregar a **Tango** → si existente: **stock a ERPNext** + **precio a Excel** → pricing en Excel → precios a Tango.
> **Fuentes de verdad:** catálogo → **Tango** · stock → **ERPNext** · precios → **Excel**.

---

## 1. Carpeta 1 — `/home/costa/Python/OCR Proveedores`

### 1.1 Inventario y cuál es la versión buena

Hay **una sola app viva** y muchas iteraciones previas. Por fecha de modificación:

| Archivo | Fecha | Tamaño | Rol |
|---|---|---|---|
| **`ocr_claude.py`** | **2026-05-19** | 109 KB | ✅ **CANÓNICA (V9.0)** — app completa actual |
| `facturas_multiples_a_tango_vclaude.py` | 2026-05-18 | 88 KB | ❌ iteración previa |
| `facturas_multiples_a_tango_v8_1_corregido.py` | 2026-05-18 | 62 KB | ❌ iteración previa |
| `facturas_multiples_a_tango_v8.py` | 2026-05-18 | 73 KB | ❌ obsoleta |
| `facturas_multiples_a_tango_v6.py` | 2026-05-15 | 50 KB | ❌ obsoleta |
| `factura_a_tango_v4_matching.py` | 2026-05-15 | 33 KB | ❌ obsoleta |
| `lector_tablas_a_tango_v2.py`, `analizador_tablas_facturas.py`, `lector_espacial_facturas_tango.py`, `OCR.py` | 2026-05-15 | — | ❌ prototipos tempranos |
| `api.py` | 2026-05-15 | 1.2 KB | ❌ stub/experimento |
| `facturas_tango_v8.db` | 2026-05-28 | 40 KB | 📀 **datos aprendidos reales** (ver 1.3) |
| `facturas_tango_debug.log`, `Token.txt` | — | — | log + secreto (ver 1.5) |

**Linaje:** `OCR.py → lector_espacial → lector_tablas_v2 → analizador_tablas → v4 → v6 → v8 → v8_1 → vclaude → ocr_claude.py (V9)`. Todo lo anterior a `ocr_claude.py` es **obsoleto** (se conserva como historial, no se toca).

> ⚠️ **Discrepancia de copias a reconciliar:** el repo ya tiene `Programas_hechos/OCR Proveedores/` (commiteada en el seed). Pero `ocr_claude.py` mide **107 073 b en el repo vs 109 491 b en `~/Python`** → no son idénticas. La DB, el log y el `Token.txt` viven **solo** en `~/Python`. Hay que decidir cuál es la canónica (por `DECISION_004`, el standalone canónico va en `Programas_hechos/`) y consolidar una sola.

### 1.2 Arquitectura de `ocr_claude.py` (V9.0) — qué hace

App de escritorio **tkinter, sin IA**, tal cual el diseño. Componentes:

- **`BaseLocal` (SQLite `facturas_tango_v8.db`)** — memoria/aprendizaje:
  - `proveedor_layout` — zonas de cada proveedor por CUIT (aprende una vez la posición de los campos).
  - `qr_cache` — CUIT→proveedor (evita re-parsear).
  - `equivalencias` — código/descr. de proveedor ↔ artículo Tango (mejora con el uso).
  - `facturas_procesadas` — historial permanente + antiduplicado por `clave`.
- **`CatalogoTango`** — carga `Artículos.xlsx` exportado de Tango; **comparación multicriterio** priorizando **código de proveedor / código de barras** sobre descripción (similitud + score de tokens; **umbral configurable, default 82**).
- **`FacturaTableReader`** — el motor OCR:
  - PDF con texto → **PyMuPDF**; imagen o PDF ilegible → **Tesseract**; preproceso **OpenCV** (deskew, binarización).
  - **Detección de PDF con fuente rota** (`_texto_es_legible`) → cae a OCR → **esto es el fix "Emapi"** ya presente.
  - **Lectura de QR AFIP** (`leer_qr_afip`, `_parsear_url_afip`): saca CUIT emisor, comprobante, fecha, importe SIN OCR → identifica proveedor → usa su layout aprendido para OCR dirigido a la zona de artículos. **La idea clave de diseño está implementada.**
  - Detección de proveedor/CUIT/tipo/nº/fecha/total; detección de zonas e ítems; validación cantidad×precio=importe; **aprende el layout** por CUIT.
- **`App` (UI)** — miniatura de factura, tabla editable con **estados por color**, umbral configurable, carga **multi-factura** con cola/worker, "sacar foto", filtros. Botones existentes:
  - **"Alta artículos nuevos (Tango)"** → genera Excel modelo de Tango (hoja *Artículos*).
  - **"Resumen compra/stock"** → Excel con **Precio, Cantidad, Importe, IVA** por ítem + hoja *Facturas_Cargadas*.
  - **"Reporte de revisión"**, **"Ver candidatos"**, **"Layouts aprendidos"**, aprender equivalencias.

### 1.3 Estado de madurez (evidencia empírica)
La DB ya tiene aprendizaje **real**: `equivalencias`=8, `proveedor_layout`=1, `qr_cache`=1, `facturas_procesadas`=1. Coincide con lo reportado: andaba con **Comodo** y **Orange Blue**; **Emapi** resuelto por vocabulario→OCR.

### 1.4 🔑 Hallazgo central sobre las fronteras
**`ocr_claude.py` NO escribe directo a Tango ni a ERPNext.** Todas las salidas son **Excel + confirmación humana** (el "Alta Tango" es un Excel para importación manual). Es decir: **ya cumple la Regla 8** (el OCR sugiere, el humano confirma) y **no toca zona fiscal automáticamente**. Muy buena base de partida.

### 1.5 Secreto detectado (no se transcribe el valor)
- **`/home/costa/Python/OCR Proveedores/Token.txt`** — token de Tango en texto plano. **No se usa** en `ocr_claude.py` (grep sin referencias) → vestigial. Es el **mismo token** que aparecía en el proyecto OCR Mercado Pago. Recomiendo **rotarlo en Tango y borrar el archivo**. (Reporto path + tipo; no incluyo el valor.)

### 1.6 Entorno
Las dependencias **no están instaladas en esta Mint**: faltan `tesseract` (binario), `pytesseract`, `fitz`/PyMuPDF, `cv2`, `openpyxl`, `pyzbar`, `numpy`. Antes de correr el OCR hay que preparar el entorno en la máquina destino (existe `requerimientos.py` en el proyecto para ayudar).

---

## 2. Carpeta 2 — `/home/costa/Python/Baja de Stock en ERPnext al facturar en Tango`

### 2.1 Qué hay
Un solo archivo: **`Tango Erpnext Stock Sync.py`** — MVP **FastAPI** que sincroniza el stock de **ventas** Tango→ERPNext:
- Lee movimientos de stock desde **Tango API Live Query** (`GetApiLiveQueryData`, company 25, process 12567).
- **Normaliza el signo:** `CANTIDAD_CONTROL_STOCK` < 0 (factura) → `stock_out`; > 0 (nota de crédito) → `stock_in`.
- **Idempotencia** con SQLite `sync_log` por `external_id` (`tango:{ID_STA14}:{ID_STA11}:{NRO_INTERNO_STOCK}`) → no reprocesa.
- **`ERPNextClient.create_stock_entry`**: `Material Issue` (baja) / `Material Receipt` (alta) + `submit` (`docstatus=1`).
- Endpoints: `/health`, `GET /tango/stock-movements` (preview), `POST /sync/tango-to-erpnext` con **`dry_run=True` por defecto** (✅ seguro), `GET /sync/log`.
- **Higiene de secretos correcta:** credenciales por `.env` con placeholders `CAMBIAR_*`, **nada hardcodeado**.

### 2.2 Estado en el repo
Ya tiene pie en el backend: copia **idéntica** en `Programas_hechos/Baja de Stock.../`, **`tests/test_stock_sync.py`**, y un **stub vacío** `apps/sistema_industrial/sistema_industrial/stock_sync/` (README 52 b + `events.py` 761 b, del commit seed). O sea: **zona Atlas** (backend Frappe). El MVP real está listo; falta productizarlo.

### 2.3 Reutilizable para el OCR
El path **`STOCK_IN` / `Material Receipt`** de `create_stock_entry` es exactamente lo que necesita el OCR para **cargar stock de compras** en ERPNext. No hay que reinventarlo.

---

## 3. Estado: hecho vs falta

| Pieza del flujo canónico | Estado | Dónde |
|---|---|---|
| OCR QR AFIP → identifica proveedor | ✅ Hecho | `ocr_claude.py` |
| Memoria de layout por proveedor | ✅ Hecho | `proveedor_layout` |
| OCR dirigido de artículos + matching multicriterio | ✅ Hecho | `CatalogoTango` |
| Aprendizaje de equivalencias | ✅ Hecho | `equivalencias` |
| Revisión humana con estados / candidatos / umbral | ✅ Hecho | `App` |
| **Precio de compra → Excel** | 🟡 Parcial | `Resumen_Compra_Stock.xlsx` tiene Precio+Cantidad; falta atarlo al Excel de pricing canónico |
| **Alta de artículo nuevo → Tango** | 🟡 Parcial | genera Excel modelo → **import manual** (falta validar contra el importador real; 🔴 fiscal) |
| **Stock de compras → ERPNext** | 🔴 Falta | NO existe en el OCR; reutilizar `ERPNextClient` (Material Receipt) |
| Baja de stock ventas Tango→ERPNext | 🟡 MVP listo, sin productizar | `Tango Erpnext Stock Sync.py` (zona Atlas) |

---

## 4. Plan propuesto — por fases (para aprobar ANTES de construir)

> Carriles: **YA** = roza corto plazo · **CORTO** · **LARGO** (toca Tango/ERPNext/stock). Nada se ejecuta contra sistemas reales sin OK.

- **F0 — Consolidación de la base** *(carril: relevamiento, ya casi hecho)*
  Reconciliar la versión canónica (`ocr_claude.py` V9 — repo vs `~/Python` difieren), dejar **una sola** en `Programas_hechos/OCR Proveedores/` (`DECISION_004`); separar datos (DB/log) de código; **rotar y borrar `Token.txt`**; documentar dependencias. *Sin ejecutar nada.*

- **F1 — Entorno + validación OCR offline** *(carril: CORTO)*
  Instalar deps (tesseract, PyMuPDF, OpenCV, pyzbar…) en la máquina destino. Correr el OCR contra **facturas de muestra** (Comodo, Orange Blue, Emapi) **sin escribir a Tango/ERPNext**. Validar QR, layout aprendido, matching y umbral. Salida: `Resumen_Compra_Stock.xlsx` + reporte de revisión. *Prueba el motor sin tocar zona fiscal.*

- **F2 — Precio de compra → Excel** *(carril: YA)*
  Confirmar el **formato de Excel** que consume el pricing humano (coordinar con el dueño del Excel de presupuesto/pricing; `DECISION_003`/`DECISION_011`, ver `esquema-excel-presupuesto-ot`) y asegurar que el resumen del OCR lo alimenta. **Humano confirma.** *Es el pedazo más cercano al carril YA.*

- **F3 — Alta de artículos nuevos en Tango** *(carril: LARGO · 🔴 fiscal · requiere OK Constantino)*
  Validar el Excel de alta contra el **importador real de Tango** junto a Constantino, en ambiente controlado. **No automatizar** la escritura a Tango sin decisión explícita; el default sigue siendo Excel → import manual.

- **F4 — Stock de compras → ERPNext** *(carril: LARGO)*
  Componente nuevo (o extensión del `stock_sync`) que toma los artículos ya dados de alta + cantidades del OCR y hace **Material Receipt** en ERPNext, **reutilizando `ERPNextClient`**. Idempotencia por factura+ítem. **`dry_run` primero.** Precondición: el `item_code` debe existir en ERPNext (depende de F3).
  🔷 **Decisión de diseño pendiente:** ¿el stock-in de compras entra a ERPNext **directo desde el OCR** (como dice el canon) o **vía Tango** (compra cargada en Tango → el `stock_sync` la levanta como `stock_in`)? Ambos caminos existen técnicamente; hay que elegir uno con Constantino/Atlas.

- **F5 — Baja de stock (ventas) productización** *(carril: LARGO · zona Atlas)*
  Llevar el MVP FastAPI al módulo Frappe `stock_sync` (hoy stub): scheduler, idempotencia, manejo de `item_code` inexistente, `dry_run`→real con OK. **Coordinar con Atlas** para no duplicar (es su zona de backend/Tango API).

---

## 5. Fronteras del canon — marcadas explícitamente

- **Precios de compra → Excel.** Nunca `Tango → sistema` para precios (`DECISION_011`). Excel es el máster de precios.
- **Crear artículo en Tango = 🔴 zona fiscal → requiere aprobación de Constantino.** Tango es dueño del catálogo.
- **Stock → ERPNext** es el máster del stock.
- **Regla 8 (Brújula): el OCR sugiere, el humano confirma.** Ninguna factura entra al sistema sin validación humana. (La app actual ya lo respeta: todo pasa por Excel.)
- **Nada se ejecuta contra Tango/ERPNext reales sin aprobación** (usar muestras y `dry_run`).

---

## 6. Preguntas abiertas para Constantino

1. **Dirección del stock de compras (F4):** ¿OCR→ERPNext **directo**, o **vía Tango** (compra en Tango → `stock_sync`)?
2. **Alta en Tango:** ¿queda siempre **Excel + import manual**, o en algún momento se automatiza?
3. **Versión canónica:** confirmar `ocr_claude.py` V9 como la buena y consolidar repo ↔ `~/Python` (difieren de tamaño).
4. **`Token.txt`** vestigial (mismo token que el OCR de Mercado Pago): ¿lo **roto y borro**?
5. **Máquina destino** del OCR (las deps no están en esta Mint): ¿dónde va a correr?
6. **Dueño del componente de Baja (F5):** ¿lo llevo yo (OCR) o es de **Atlas**? Toca su zona.

---

**Resumen:** hay una base **sustancial y sana** — `ocr_claude.py` V9 cubre casi todo el flujo de lectura/matching/revisión y **no viola el canon** (todo vía Excel + humano). Lo que falta es (a) atar precio de compra al Excel de pricing, (b) el push de **stock de compras a ERPNext** (reutilizando el `ERPNextClient` del MVP de Baja), y (c) formalizar el alta en Tango (zona fiscal). **Espero aprobación del plan antes de construir.**

— OCR

---
---

# ANEXO — PLAN v2 (2026-07-23): destino = PÁGINA WEB DENTRO DE ERPNext

> **Cambio de arquitectura (orden de Constantino):** el OCR Proveedores **NO** corre en la máquina de Constantino. Se instala **dentro de ERPNext como una página web**. El motor OCR corre **server-side** en el server de ERPNext; la UI se rehace como página **Frappe** (la haría **Vega**). Esto **reemplaza** el encuadre "app de escritorio" de las secciones 1–6 (la lógica se reutiliza; el empaquetado cambia). Sigue siendo **investigación, no construcción.**

## v2.0 — Entorno destino real (relevado en el repo)

- **Server ERPNext:** `190.190.190.20` · **Frappe v16 / ERPNext v16** · Ubuntu 22.04 · MariaDB 10.6 (datos en `SERVIDOR_ERPNEXT.md`).
- **⚠️ Hardware débil:** Intel **Celeron J1800 (2 cores)**, 8 GB RAM. Tesseract + OpenCV son **CPU-intensivos** → **no** procesar en el request HTTP: hay que usar **background jobs** (`frappe.enqueue` / workers RQ) y limitar concurrencia. Es el riesgo #1 de este destino.
- **Ya existe scaffolding en la app Frappe:** módulo **`sistema_industrial/ocr_suppliers/`** (hoy stub: *"Módulo pendiente de implementación"*). Convención de DocTypes del proyecto: prefijo **`si_*`** (ej. `si_cut_batch`, `si_tango_price_cache`). Módulos hermanos útiles: `tango_sync`, `pricing_sync`, `stock_sync`.

## v2.1 — Qué se REUSA vs qué se REHACE

| Pieza de `ocr_claude.py` | Destino ERPNext | Reuso |
|---|---|---|
| Lectura QR AFIP (`leer_qr_afip`, `_parsear_url_afip`) | módulo server-side | ✅ **Reusa casi 1:1** (Python puro) |
| Aprendizaje de layout por CUIT (`_aprender_layout`, `_filtrar_zona`) | server-side | ✅ Reusa (algoritmo puro) |
| Lectura PDF/imagen + preproceso (`FacturaTableReader`, deskew, fix Emapi) | server-side (headless) | ✅ Reusa; cambiar **rutas de archivo** por **File API de Frappe** y usar **`opencv-python-headless`** |
| Matching multicriterio (`Normalizador`, `CatalogoTango` scoring) | server-side | ✅ Reusa la lógica; **cambia la fuente del catálogo** (ver v2.3) |
| Persistencia SQLite (`BaseLocal`: equivalencias, layout, qr_cache, facturas) | **DocTypes de ERPNext** | 🔧 **Se rehace** el acceso a datos (ORM Frappe en vez de `sqlite3`) |
| UI tkinter (grilla, estados color, preview, candidatos, layouts) | **Página web Frappe** (Vega) | 🔁 **Se rehace entera** |
| Cola/threading tkinter (`_procesar_queue`, worker) | **`frappe.enqueue`** + workers | 🔁 Se rehace |
| Salida Excel de alta / resumen (`openpyxl`) | server-side (descarga) o módulos `pricing_sync` | ✅ Reusa openpyxl; opcional integrar nativo |
| Stock → ERPNext (no existía) | **Stock Entry nativo vía ORM** (sin HTTP) | 🆕 Nuevo, reusa la **lógica** de `stock_sync` (Material Receipt) |

## v2.2 — Deps a instalar en el SERVER (server-side, headless)

En el server `190.190.190.20`, dentro del **entorno python del bench** (no en el sistema a lo bruto):
- **APT (sistema):** `tesseract-ocr` (+ `tesseract-ocr-spa`), `libzbar0` (para `pyzbar`), `poppler-utils` (si algún PDF necesita rasterizado).
- **PIP (bench env):** `pytesseract`, `PyMuPDF` (fitz), **`opencv-python-headless`** (¡headless, el server no tiene GUI!), `pyzbar`, `numpy`, `pillow`, `openpyxl`.
- Verificación offline en el server con una factura de muestra **antes** de exponer nada.

## v2.3 — Modelo de datos: SQLite → DocTypes

Portar las 4 tablas a DocTypes `si_*` (y **migrar los datos aprendidos** que ya existen: 8 equivalencias, 1 layout, 1 qr_cache):
- `equivalencias` → **`si_supplier_item_equivalence`** (CUIT, código/descr proveedor, Item de ERPNext).
- `proveedor_layout` → **`si_supplier_layout`** (CUIT, zonas como % de página, page_w/h, flag pdf_nativo).
- `qr_cache` → **`si_supplier_qr_cache`** (CUIT→nombre) — o resolver contra el DocType **Supplier** nativo por CUIT (evaluar).
- `facturas_procesadas` → **`si_supplier_invoice_ocr`** (cabecera) + **child table** de ítems (para la grilla de revisión y el antiduplicado por `clave`).
- **Mejora clave:** el catálogo **ya no se exporta a Excel** desde Tango. Se lee directo del **Item DocType / `si_tango_price_cache`** (el módulo `tango_sync` ya trae artículos de Tango). Elimina el paso manual "exportar Artículos.xlsx".

## v2.4 — Flujo web re-encuadrado

1. **Upload** de la factura (PDF/foto) por la **página web** (File attach en el DocType `si_supplier_invoice_ocr`).
2. Server **encola** el OCR (`frappe.enqueue`) → QR → proveedor → layout aprendido → OCR dirigido → matching contra Item/price_cache.
3. Resultado poblado en la **child table**; la **página de revisión (Vega)** muestra grilla con estados por color, "ver candidatos", "layouts aprendidos", umbral configurable — **el humano confirma (Regla 8)**.
4. Al confirmar:
   - **Precio de compra → Excel** (descarga server-side) o al pipeline de `pricing_sync` (coordinar).
   - **Artículo nuevo → Tango** (🔴 fiscal, OK Constantino): Excel de alta o vía `tango_sync` (decisión).
   - **Stock → ERPNext**: **Stock Entry (Material Receipt) nativo por ORM** (in-process, sin el HTTP del MVP de Baja) — reusando la lógica de `stock_sync`.

## v2.5 — Fases re-encuadradas (destino ERPNext web)

- **F0 — Consolidación** *(hecho parcial)*: token limpio (ver `MSG_194`); confirmar versión canónica `ocr_claude.py` V9.
- **F1 — Provisionar server** *(CORTO)*: instalar deps OCR en el bench de `190.190.190.20` (v2.2) + smoke test offline con factura de muestra en el server. Sin exponer web.
- **F2 — DocTypes + migración de aprendizaje** *(CORTO/LARGO)*: crear los `si_supplier_*` (v2.3) y migrar los datos ya aprendidos de la SQLite. *(¿dueño: OCR o Atlas? — los DocTypes tocan backend.)*
- **F3 — Port del engine al módulo `ocr_suppliers`** *(LARGO)*: mover `FacturaTableReader` + matching + layout/QR a server-side headless, con `frappe.enqueue` y métodos whitelisted. Sin UI todavía.
- **F4 — Página web de revisión (Vega)** *(LARGO)*: upload + grilla de estados + candidatos + layouts + umbral. Reemplaza tkinter.
- **F5 — Salidas** *(mixto)*: precio→Excel/`pricing_sync` **[roza YA]**; alta Tango **[🔴 fiscal, OK]**; **stock→ERPNext nativo** (Material Receipt, `dry_run` primero).
- **F6 — Baja de stock (ventas)** *(LARGO, zona Atlas)*: productizar el MVP FastAPI en `stock_sync`. Sin cambios respecto al Plan v1.

## v2.6 — Fronteras del canon (siguen vigentes, con matices del nuevo destino)

- Regla 8 intacta: **la confirmación humana ocurre en la grilla web** antes de cualquier impacto.
- Alta en Tango sigue siendo **🔴 fiscal → OK de Constantino**.
- El stock a ERPNext ahora es **in-process (ORM)** — más directo que el HTTP del MVP, pero igual **`dry_run`/preview + confirmación** antes de submit real.
- **Nada** se ejecuta contra Tango/ERPNext productivos sin aprobación.

## v2.7 — Preguntas nuevas (además de las de §6)

7. **Server débil (Celeron 2 cores):** ¿aceptás la latencia de OCR por cola/worker? ¿límite de facturas simultáneas?
8. **Catálogo desde Item/`si_tango_price_cache`** en vez de exportar Excel de Tango: ¿confirmás la mejora?
9. **Dueño de los DocTypes y del módulo `ocr_suppliers`:** ¿lo hago yo (OCR) o Atlas (backend)? La **UI web es de Vega** — confirmar el reparto.
10. **Tipo de página web:** ¿Desk (interna, para el/los usuarios de compras) o Portal/www (externa)? Asumo **Desk interna**.

— OCR
