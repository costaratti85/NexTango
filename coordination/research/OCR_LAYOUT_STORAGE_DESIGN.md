# Dónde vive el "layout aprendido" por proveedor — diseño (OCR-en-ERPNext)

**Autor:** OCR (satélite) · **Fecha:** 2026-07-23 · **Modo:** diseño, NO construcción.
**Para:** Nova (cc Dispatch / Constantino) · **Coordinación:** Forge (modelado ERPNext).
**Principio rector:** *usar lo nativo* → el aprendizaje vive **dentro de ERPNext, atado al Supplier**. **No** un JSON suelto en disco.

---

## 1. Qué es hoy el "layout" (fuente: SQLite del programa de escritorio)

Tabla `proveedor_layout` (keyed por CUIT). Guarda **una zona de ítems** de la factura, expresada en **porcentajes 0..1** (independiente de resolución) + dimensiones de referencia + flags de lectura:

| Campo SQLite | Tipo | Significado |
|---|---|---|
| `cuit` (PK) | TEXT | clave de proveedor (11 dígitos) |
| `proveedor` | TEXT | nombre |
| `page_w`, `page_h` | REAL | dimensiones de página de referencia (px/pt) |
| `zona_items_x0_pct` / `x1_pct` / `y0_pct` / `y1_pct` | REAL | rectángulo de la zona de ítems, como fracción 0..1 |
| `es_pdf_nativo` | INT(bool) | el PDF traía texto |
| `necesita_ocr` | INT(bool) | hubo que rasterizar+OCR |
| `veces_procesado` | INT | cuántas facturas reforzaron el layout |
| `ultima_fecha` | TEXT | timestamp |

**Dato real aprendido HOY en la DB (único layout persistido):**
```
CUIT 30712517383 · ORANGE BLUE IMPORT & EXPORT TOOLS S.R.L.
page_ref 1191×1684 · zona items x[0.0455→0.9545] y[0.3128→0.7024]
es_pdf_nativo=1 · necesita_ocr=0 · veces_procesado=2
```
> ⚠️ **Ojo, dato crítico para la migración:** el layout persistido es de **Orange Blue**, **NO de "Cómodo"**. En esta DB hay **1 sola** fila de layout (y las 8 equivalencias también son de Orange Blue). El layout de Cómodo **no está** en `facturas_tango_v8.db`. Antes de migrar hay que ubicar de dónde sale el de Cómodo (¿otra DB? ¿la máquina vieja? ¿nunca se persistió?). Ver §6.

## 2. La clave de match ya es nativa

`tango_sync` mapea **CUIT → `tax_id`** del party de ERPNext (`tango_sync/customer_push.py:97 "tax_id": tc.cuit`, `schemas.py:45`). O sea: el **Supplier** de ERPNext se identifica por `tax_id` = CUIT, exactamente la clave que usa el OCR. **No hace falta inventar clave.**

## 3. Opción A vs Opción B

### Opción A — custom field en Supplier (`si_ocr_layout`, tipo JSON/Code)
- ✅ Máxima simpleza: un campo, sin DocType nuevo, migración trivial (set field).
- ✅ "Nativo" en el sentido literal: cuelga del Supplier.
- ❌ Blob único → 1 sola plantilla por proveedor, poco reportable/consultable.
- ❌ **Acoplamiento riesgoso:** el Supplier lo **administra `tango_sync`** (lo crea/actualiza desde Tango). Si el worker de OCR escribe el layout **dentro del doc Supplier**, un re-sync de `tango_sync` puede pisar/entrar en conflicto. Edición del JSON crudo en Desk es posible pero incómoda.

### Opción B — DocType propio vinculado al Supplier (`SI OCR Supplier Layout`)
- ✅ **Desacopla del Supplier** (Tango-sync no lo toca): el OCR es dueño de su DocType; solo **referencia** al Supplier por `Link` + `tax_id`. Sin riesgo de pisadas.
- ✅ Estructurado y **editable/validable desde el Desk** (cada zona un Float).
- ✅ **Múltiples plantillas por proveedor** (distintos formatos/comprobantes) y **historial** (`veces_procesado`, versiones).
- ✅ Extensible: hoy 1 zona (ítems); mañana zonas de encabezado/totales sin migrar de esquema.
- ❌ Un poco más de modelado (un DocType + join para leer).

### 🏆 Recomendación: **Opción B**, como **DocType propio vinculado** (no child table del Supplier).
Razón decisiva: **el Supplier es propiedad de `tango_sync`**. Meter el aprendizaje adentro (A, o child table) mete al OCR a escribir en un doc que otro módulo re-sincroniza. Un DocType separado que **linkea** al Supplier respeta fronteras, permite N plantillas, es editable en Desk y lo puede actualizar el worker de OCR sin tocar el Supplier.
Si Constantino prefiere huella mínima y acepta 1 plantilla por proveedor + el acoplamiento, **A es el fallback válido** (y el JSON de §4 va tal cual en el campo).

## 4. Esquema canónico del JSON del layout (sirve para A y como payload de migración)

```json
{
  "version": 1,
  "cuit": "30712517383",
  "proveedor": "ORANGE BLUE IMPORT & EXPORT TOOLS S.R.L.",
  "page_ref": { "w": 1191.0, "h": 1684.0 },
  "flags": { "es_pdf_nativo": true, "necesita_ocr": false },
  "zonas": {
    "items": { "x0_pct": 0.0455, "x1_pct": 0.9545, "y0_pct": 0.3128, "y1_pct": 0.7024 }
  },
  "aprendizaje": { "veces_procesado": 2, "ultima_fecha": "2026-05-19T07:37:00" }
}
```
- **Coordenadas como fracción 0..1** → independientes de resolución (propiedad clave; funciona multi-DPI).
- `zonas` es un **diccionario** para admitir futuras zonas (`header`, `totales`) sin romper esquema.

## 5. Diseño del DocType (Opción B) — para revisión de Forge

**DocType `SI OCR Supplier Layout`** (módulo `ocr_suppliers`, prefijo `si_`):

| Campo | Tipo | Notas |
|---|---|---|
| `supplier` | Link → Supplier | requerido; el lazo nativo |
| `cuit` | Data | fetch de `supplier.tax_id`, **indexado**; normalizado a 11 dígitos |
| `proveedor_nombre` | Data | fetch de `supplier.supplier_name` (comodidad) |
| `template_name` | Data | ej. "Factura A default"; permite N por proveedor |
| `activo` | Check | default 1 |
| `page_w`, `page_h` | Float | dimensiones de referencia |
| `zonas` | Table → `SI OCR Layout Zone` | child: `zone_name`, `x0_pct`, `x1_pct`, `y0_pct`, `y1_pct` |
| `es_pdf_nativo`, `necesita_ocr` | Check | flags |
| `veces_procesado` | Int | refuerzo |
| `ultima_fecha` | Datetime | |
| `raw_layout_json` | Code (JSON) | espejo del JSON §4 (debug / forward-compat) |

Child **`SI OCR Layout Zone`**: `zone_name` (Data), `x0_pct`/`x1_pct`/`y0_pct`/`y1_pct` (Float).
Unicidad sugerida: `(supplier, template_name)`.

## 6. 🔴 Paso de migración (NO perder el aprendizaje) — parte del plan

Incluir en el plan a ERPNext un **script de migración one-shot** (idempotente):

1. Abrir `~/Python/OCR Proveedores/facturas_tango_v8.db`.
2. Por cada fila de `proveedor_layout`:
   a. **Normalizar CUIT** a 11 dígitos (strip de `-`/espacios) en ambos lados.
   b. Buscar **Supplier** con `tax_id` normalizado == CUIT.
      - Si no existe → **no crear a ciegas** (el Supplier es de `tango_sync`): registrar en un reporte "proveedor sin Supplier" para resolver (¿alta en Tango? ¿sync pendiente?).
   c. Armar el JSON §4 y **crear/actualizar** `SI OCR Supplier Layout` (Opción B) o setear `si_ocr_layout` (Opción A). Idempotente por `(supplier, template_name)`.
3. **Migrar en el mismo pase** las tablas hermanas (ya en Plan v2): `equivalencias` (8) → `si_supplier_item_equivalence`; `qr_cache` (1) → su DocType.
4. Emitir **reporte de migración**: cuántos layouts/equivalencias migrados, cuáles sin Supplier, y **el faltante de Cómodo** (ver §1).

> **Aviso Cómodo:** la migración solo puede traer lo que esté en la SQLite. Hoy Cómodo **no está** en esta DB. Hay que localizar su layout (otra DB / máquina vieja) **antes** de dar la migración por completa, o se pierde ese aprendizaje.

## 7. Coordinación con Forge
Le paso a Forge (modelado ERPNext) el diseño del DocType §5 para validar: fieldtypes v16 (JSON/Code, Table child), fetch de `tax_id`/`supplier_name`, índice en `cuit`, permisos, y si prefiere child table vs DocType propio desde su óptica de modelado. Ver mensaje en su canal.

## 8. Preguntas abiertas para Constantino
1. **A vs B:** recomiendo **B** (desacople de `tango_sync`, N plantillas, editable en Desk). ¿Confirmás, o querés A por simpleza?
2. **Cómodo:** ¿dónde está su layout aprendido? (no está en `facturas_tango_v8.db`).
3. **Suppliers faltantes:** si un CUIT del OCR no tiene Supplier en ERPNext, ¿se crea (zona fiscal/Tango) o se deja pendiente?

— OCR
