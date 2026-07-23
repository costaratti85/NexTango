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

### 2. Custom field del layout aprendido — `custom_fields.py`
- **`Supplier.si_ocr_layout`** (fieldtype **JSON**, read-only, no-copy): guarda las zonas/posiciones de la factura que el OCR aprende por proveedor/CUIT. Vacío hasta la primera pasada.
- Se crea **idempotente en cada `bench migrate`** vía `after_migrate` → `ensure_ocr_custom_fields()` (declarado en `hooks.py`). Reproducible y versionado.

## Pendiente (otros dueños)
- Motor OCR server-side (QR AFIP + layout + parsing) en `frappe.enqueue` — **OCR**.
- DocTypes `si_supplier_*` (equivalencias, invoice_ocr) — **OCR / Atlas**.
- Página web de revisión/confirmación (Regla 8) — **Vega**.
- Puente de alta a Tango — zona fiscal, OK Constantino.
