# ocr_suppliers

Módulo del OCR de proveedores (factura de compra → ERPNext). En construcción — sprint nocturno 2026-07-23.

**Principio de diseño (Constantino):** aprovechar lo nativo de ERPNext; construir solo el hueco (lectura OCR, mapeo a nuestros códigos, confirmación humana, puente con Tango). Ver `coordination/reports/FORGE_REVISION_PROMPT_ASESOR_OCR.md`.

## Parte de Forge (integración ERPNext) — ya implementada

### 1. Lectura del catálogo para el matching — `catalog.py` (de Atlas)
El catálogo lo lee **`load_catalog()`** (autor: Atlas), que trae Items + Item Barcode +
Item Supplier y cachea en Redis (TTL 30 min). El matcher (`item_matcher.match_lines`)
lo consume. **Reemplaza el export manual `Artículos.xlsx` de Tango.**
```python
from sistema_industrial.ocr_suppliers.catalog import load_catalog
catalogo = load_catalog()          # cacheado; force=True re-lee de la DB
```
> Nota de reconciliación (2026-07-23): la lectura de catálogo la ganó la interfaz de
> Atlas (`load_catalog`), que es la que importa el api `api/ocr_proveedores.py`. Mi
> `build_item_catalog`/`get_item_catalog` previos se retiraron (mi sugeridor consulta
> los Items directo, no necesita el catálogo).

### 2. Custom field del layout aprendido — `custom_fields.py` + `layout.py`
- **`Supplier.si_ocr_layout`** (fieldtype **JSON**, read-only, no-copy): guarda las zonas/posiciones de la factura que el OCR aprende por proveedor/CUIT ("experiencia de scaneo"). Vacío hasta la primera pasada.
- Se crea **idempotente en cada `bench migrate`** vía `after_migrate` → `ensure_ocr_custom_fields()` (declarado en `hooks.py`). Reproducible y versionado.
- **Helpers `layout.py`** (para que el OCR persista tras procesar cada factura, sin tocar el ORM):
  ```python
  from sistema_industrial.ocr_suppliers.layout import (
      get_supplier_layout, save_supplier_layout,     # por name de Supplier
      get_layout_by_cuit, save_layout_by_cuit,        # por CUIT (Supplier.tax_id)
      find_supplier_by_cuit,
  )
  ```
  El **OCR es dueño de la forma del JSON**; los helpers solo guardan/leen un dict.
  `save_layout_by_cuit` devuelve `None` si no existe Supplier con ese CUIT (el alta del Supplier la decide el humano — Regla 8).

### 3. Generador del Excel de importación a Tango — `tango_sync/article_export.py`
Punto que **Atlas invoca en el "Confirmar" de la Fase 2, tras crear los Items**:
```python
from sistema_industrial.tango_sync.article_export import build_tango_import_excel
res = build_tango_import_excel(created_items)   # los Items recién creados
# -> {"file_url", "file_name", "count", "item_codes", "gaps"}
# res["file_url"] = .xlsx REAL descargable (File de Frappe), formato plantilla Tango
```
- `created_items`: cada elemento puede ser item_code (str), dict (`item_code`/`name`) o Document de Frappe. Se normaliza y deduplica.
- Genera un **.xlsx real y descargable** (no filas sueltas): la UI descarga `file_url`.
- Equivalente por filtro/grupo: `generate_tango_import_excel(item_codes=..., item_group=...)` (mismo return). `build_tango_article_rows(...)` devuelve solo las filas (sin archivo), para preview.
- Carga la **plantilla oficial de Tango** (bundleada en `tango_sync/tango_templates/`) y **pega solo las filas** en la hoja "Artículos", preservando las 80 hojas de lookup + `_metadata`. **No fabrica el xlsx de cero.**
- Devuelve el **`file_url`** de un File privado de Frappe (para descargar/revisar/subir a Tango a mano — Regla 8, no sube nada).
- Requiere `openpyxl` en el bench (dep del OCR).

### 4. Sugerencia inteligente de código — `code_suggester.py`
**Interfaz de Atlas (la que importa el api), lógica de Forge.** Para cada línea
**sin match**, propone el próximo `item_code` libre.
```python
from sistema_industrial.ocr_suppliers.code_suggester import (
    suggest_next_item_code, aplicar_sugerencias,
)
# firma exacta que llama el api:
codigo = suggest_next_item_code(linea, candidatos)   # -> str | None (solo el código)
aplicar_sugerencias(lineas, suggest_next_item_code)  # setea l["codigo_sugerido"] por línea sin match
```
- **`suggest_next_item_code(linea, candidatos) -> str | None`**: infiere familia+subcategoría
  del **candidato top** del matcher (`{item_code, item_name, score, reason}`) y calcula el
  próximo código libre. Ej: amoladora DeWalt → candidatos 54 → **`54-00-00-00-126`**.
- **Numeración:** máximo del grupo + paso (5 taller / 1 en 52·54·99), con ceros. Maneja
  **grupo vacío** y **colisiones**. Sin familia clara / sin candidatos → **`None`** (no inventa;
  la UI deja el campo vacío para carga manual — Regla 8).
- **`aplicar_sugerencias(lineas, suggester)`**: wiring PURO de Atlas (graceful; líneas con
  match no llevan sugerencia).
- **NO reconstruye el árbol de Item Groups** (decisión de Constantino): solo lee `item_code`.
- Metadata (confianza/needs_review/nota) disponible en el debug `suggest_code_details_api`
  (la interfaz principal devuelve solo el string, por contrato con Atlas).
- Anatomía de referencia: `coordination/reports/FORGE_ANATOMIA_CODIGOS_ARTICULOS.md`.

## Pendiente (otros dueños)
- Motor OCR server-side (QR AFIP + layout + parsing) en `frappe.enqueue` — **OCR**.
- DocTypes `si_supplier_*` (equivalencias, invoice_ocr) — **OCR / Atlas**.
- Página web de revisión/confirmación (Regla 8) — **Vega**.
- Puente de alta a Tango — zona fiscal, OK Constantino.
