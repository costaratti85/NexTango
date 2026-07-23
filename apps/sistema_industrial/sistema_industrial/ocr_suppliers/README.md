# ocr_suppliers

Módulo del OCR de proveedores (factura de compra → ERPNext). En construcción — sprint nocturno 2026-07-23.

**Principio de diseño (Constantino):** aprovechar lo nativo de ERPNext; construir solo el hueco (lectura OCR, mapeo a nuestros códigos, confirmación humana, puente con Tango). Ver `coordination/reports/FORGE_REVISION_PROMPT_ASESOR_OCR.md`.

## Parte de Forge (integración ERPNext) — ya implementada

### 1. Lectura del catálogo para el matching — `catalog.py`
Reemplaza el export manual `Artículos.xlsx` de Tango: el OCR lee el catálogo directo de ERPNext.

- **`build_item_catalog(item_group=None, tango_only=False, include_disabled=False) -> list[dict]`**
  Función **in-process** (ORM). Es la que debe usar el módulo OCR server-side.
  Eficiente: **3 queries** (Item + Item Barcode + Item Supplier), agrupadas en memoria (sin N+1).
- **`get_item_catalog(...)`** — wrapper `@frappe.whitelist()` para debug/consumo externo (no para el OCR in-process).

**Contrato de salida** (una fila por Item):
```python
{
    "item_code":      str,            # = COD_STA11 (mismo código en Tango y ERPNext)
    "item_name":      str,
    "description":    str | None,
    "item_group":     str,            # ej. "Ferretería"
    "stock_uom":      str,
    "si_tango_id":    int | None,     # mapeo Tango <-> Item
    "barcodes":       list[str],                              # matching prioritario
    "supplier_items": list[{"supplier": str, "supplier_part_no": str}],  # código del proveedor
}
```
Uso típico desde el matcher del OCR:
```python
from sistema_industrial.ocr_suppliers.catalog import build_item_catalog
catalogo = build_item_catalog(item_group="Ferretería")   # o sin filtro para todo
```
Prioridad de matching sugerida (heredada del OCR V9): `supplier_part_no` / `barcode` > descripción.

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
Punto que **Atlas invoca tras crear los Items nuevos del OCR**:
```python
from sistema_industrial.tango_sync.article_export import generate_tango_import_excel
res = generate_tango_import_excel(item_codes=nuevos_codigos_ocr)   # ferretería 06-
# -> {"file_url", "file_name", "count", "item_codes", "gaps"}
```
- Carga la **plantilla oficial de Tango** (bundleada en `tango_sync/tango_templates/`) y **pega solo las filas** en la hoja "Artículos", preservando las 80 hojas de lookup + `_metadata`. **No fabrica el xlsx de cero.**
- Devuelve el **`file_url`** de un File privado de Frappe (para descargar/revisar/subir a Tango a mano — Regla 8, no sube nada).
- Requiere `openpyxl` en el bench (dep del OCR).

## Pendiente (otros dueños)
- Motor OCR server-side (QR AFIP + layout + parsing) en `frappe.enqueue` — **OCR**.
- DocTypes `si_supplier_*` (equivalencias, invoice_ocr) — **OCR / Atlas**.
- Página web de revisión/confirmación (Regla 8) — **Vega**.
- Puente de alta a Tango — zona fiscal, OK Constantino.
