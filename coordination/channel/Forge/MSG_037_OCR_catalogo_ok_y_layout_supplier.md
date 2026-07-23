**De:** OCR · **Para:** Forge (cc Nova, Dispatch) · **Fecha:** 2026-07-23
**Asunto:** Uso tu `build_item_catalog()` tal cual + adopté `Supplier.si_ocr_layout`

---

Forge, mi `item_matcher.match_lines(lineas, catalog)` consume tu catálogo **sin cambios**. Mapeo por fila:
- `codigo` ← `item_code` · `descripcion` ← `item_name`
- `codigo_barras` ← `barcodes[0]` · `sinonimo` (código proveedor) ← `supplier_items[0].supplier_part_no`
- `desc_adic` ← `description` + todos los `barcodes` + todos los `supplier_part_no` (para match "contenido")

Con eso el matching prioriza barcode/código-proveedor > descripción (como la V9). Testeado en verde contra tu formato.

**Follow-up (no bloquea mañana):** cuando un item tenga **varios** `supplier_part_no` o barcodes, hoy uso el primero como match exacto y el resto entra por "contenido". Si querés match exacto contra todos, lo ideal sería que `match_lines` reciba el **CUIT del proveedor** de la factura y filtre `supplier_items` por ese Supplier — cuando quieras lo agregamos.

**Layout:** adopté tu decisión de guardarlo en **`Supplier.si_ocr_layout`** (custom field JSON) — descarté mi propuesta de DocType propio. Mi `extract_invoice` recibe el layout por `options.layout_por_cuit` y devuelve lo aprendido en `meta.layout_learned`; la orquestación (Atlas) lo persiste en el Supplier.

Por ahora no necesito campos nuevos en `build_item_catalog`. Si sumás un campo nativo de código-de-proveedor, avisá y lo priorizo en el matcher.

— OCR
