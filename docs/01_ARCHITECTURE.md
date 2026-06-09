# Architecture

## Decisión

SistemaIndustrial será una app Frappe instalada sobre ERPNext.

## Regla

La lógica comercial y operativa vive en Frappe.
Los motores industriales pesados pueden vivir como librerías, workers o servicios auxiliares si conviene.

## Módulos base

- presets
- quoting
- cutting
- tango_sync
- pricing_sync
- ocr_suppliers
- stock_sync
- erpnext_extensions
