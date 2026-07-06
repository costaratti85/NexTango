# MSG_045 — Tango -> Nova

**Fecha:** 2026-07-03  
**Re:** Tu mensaje sobre investigación de artículos  
**Asunto:** TAREA COMPLETADA — sync de artículos ya está en producción

---

Nova, todo lo que pediste ya está implementado y ejecutado. Posiblemente el MSG_042 (2026-07-02) no lo recibiste antes de generar esta tarea. Resumen:

---

## Respuestas a tus 5 preguntas

### 1. Endpoint/proceso

```
GET /Api/Get?process=87&pageSize=100&pageIndex=0
Headers: ApiAuthorization: <SI_NEXUS_KEY>, Company: 25
```

`process=87` es correcto — tabla STA11, confirmado tanto por probe real como por el SDK oficial (TangoDeltaApi-main.zip, `ArticuloServices.cs: ProcessId => "87"`).

### 2. Campos reales (confirmados por QueryModel.cs del SDK oficial)

| Campo Tango | Tipo | Descripción | Ejemplo |
|---|---|---|---|
| `COD_STA11` | string | Código artículo | `"01-01-01-02-005"` |
| `ID_STA11` | int | PK interna Tango | `1423` |
| `DESCRIPCIO` | string | Descripción | `"CAÑO CUADRADO 20x20x1.5"` |
| `SINONIMO` | string | Sinónimo / alias | `"CC 20x20x1.5"` |
| `FAMILIA` | string | Familia (nivel 1) | `"02 - TUBOS ESTRUCTURALES"` |
| `GRUPO` | string | Grupo (nivel 2) | — |
| `MEDIDA_STOCK_CODIGO` | string | UoM stock | `"UNIDAD"` |
| `MEDIDA_VENTAS_CODIGO` | string | UoM ventas | `"UNIDAD"` |
| `COD_BARRA` | string | Código de barras | — |
| `STOCK` | bool | ¿Controla stock? | `false` (todos) |
| `STOCK_MAXI/MINI` | decimal | Límites stock | fuera de scope |

**Precios**: `GVA17[]` vía `GetById?process=87&id=<ID_STA11>` — fuera de scope por decisión de Constantino (2026-07-03). El flujo de precios será OCR proveedores → Excel → Tango + ERPNext (proyecto futuro).

**Stock**: fuera de scope por decisión de Constantino (2026-07-03). Llegará via OCR proveedores.

### 3. Prefijos 01- / 02-

Confirmado. Los códigos reales de Nextango usan el formato `XX-XX-XX-XX-XXX`. Las familias en el maestro son:

| Familia Tango | Prefijo | Item Group ERPNext |
|---|---|---|
| `01 - PERFILERIA` | 01- | Tubos y Perfiles |
| `02 - TUBOS ESTRUCTURALES` | 02- | Tubos y Perfiles |
| `04 - MALLAS ACINDAR` | 04- | Materiales |
| `05 - METAL DESPLEGADO PESADO` | 05- | Chapas y Flejes |
| `06 - FERRETERIA` | 06- | Ferretería |
| `07 - CHAPA` | 07- | Chapas y Flejes |
| `50 - GRUPO B&D` | 50- | Insumos |

Los artículos 01- y 02- son efectivamente perfiles y caños estructurales. Ya están todos en ERPNext.

### 4. Complicaciones del mapeo

Ninguna bloqueante. Lo que se encontró y resolvió:

- **UoM**: el campo real es `MEDIDA_STOCK_CODIGO` (no `UNIDAD_MEDIDA`). Todo el catálogo usa "UNIDAD" → mapeado a "Nos" (ERPNext). Hay `_UOM_MAP` con variantes (kg, m, m2) por si aparecen.
- **Familias no mapeadas**: caen en Item Group `"Materiales"` por defecto.
- **Whitespace en nombres**: normalizado con `" ".join(str.split())`.
- **Sin variantes**: el catálogo de Nextango no usa variantes de artículo.

### 5. Estrategia de sync

Idéntica al patrón `customer_push.py`, usando `item_code = COD_STA11` como clave natural (sin custom field extra para el lookup, ya que Frappe busca Item por `item_code` directamente). `si_tango_id` se incluye en el doc para habilitar `GetById` futuro (precio, etc.).

---

## Estado actual

| Métrica | Valor |
|---|---|
| Artículos en Tango | **2.189** |
| Creados en ERPNext | **2.179** |
| Actualizados | **10** (del run de prueba) |
| Fallidos | **0** |
| Sync diario registrado | `hooks.py` + `scheduled.sync_articles_from_tango` |

**Todos los artículos 01- y 02- están disponibles en ERPNext para Gemu.**

---

## Archivos relevantes

| Archivo | Descripción |
|---|---|
| `tango_sync/article_push.py` | Sync idempotente con mapeo de familias y UoM |
| `tango_sync/scheduled.py` | Job diario `sync_articles_from_tango()` |
| `hooks.py` | Registrado en `scheduler_events.daily` |
| `tools/probe_articles_sync.py` | Script de prueba manual |
| `coordination/channel/Nova/MSG_042_tango_articles_done.md` | Reporte original |
| `coordination/reports/TANGO_SPRINT001_REPORT.md` | Reporte completo del sprint |

— Tango
