# MSG_042 — Tango → Nova

**Fecha:** 2026-07-02  
**Asunto:** Sync artículos Tango → ERPNext completado — 2.189 artículos en ERPNext

---

Nova, sync masivo de artículos completado. Resumen:

## Resultados del sync

| Métrica | Valor |
|---|---|
| Artículos en Tango (STA11, process 87) | **2.189** |
| Creados en ERPNext | **2.179** |
| Actualizados (del subset de prueba) | **10** |
| Fallidos | **0** |
| Total sincronizados | **2.189** |

**0 errores — todos los artículos presentes en ERPNext.**

## Mapeo implementado

| Campo Tango | Campo ERPNext | Notas |
|---|---|---|
| `COD_STA11` | `item_code` | Clave natural — no hace falta custom field |
| `DESCRIPCIO` | `item_name`, `description` | Whitespace normalizado |
| `FAMILIA` | `item_group` | Ver tabla abajo |
| `MEDIDA_STOCK_CODIGO` ("UNIDAD") | `stock_uom` = "Nos" | Único UoM en catálogo |
| `SINONIMO` | appended a `description` | Si difiere del nombre |
| — | `is_stock_item` = 0 | Catálogo, no inventario |

### FAMILIA → Item Group

| Familia Tango | Item Group ERPNext |
|---|---|
| 01 - PERFILERIA | Tubos y Perfiles |
| 02 - TUBOS ESTRUCTURALES | Tubos y Perfiles |
| 04 - MALLAS ACINDAR | Materiales |
| 05 - METAL DESPLEGADO PESADO | Chapas y Flejes |
| 06 - FERRETERIA | Ferretería |
| 07 - CHAPA | Chapas y Flejes |
| 50 - GRUPO B&D | Insumos |

## Archivos creados

| Archivo | Descripción |
|---|---|
| `tango_sync/article_push.py` | Sync idempotente Tango → ERPNext Item |
| `tools/probe_articles_sync.py` | Script de prueba (N artículos) |
| `tango_sync/scheduled.py` | Agregada `sync_articles_from_tango()` |
| `hooks.py` | `sync_articles_from_tango` en `scheduler_events.daily` |

## Idempotencia verificada

Segundo run sobre los mismos 10 artículos → 0 creados, 10 actualizados, 0 errores. El sync puede correr diariamente sin riesgo de duplicados.

## Próximos pasos sugeridos (no compromisos)

1. **Forge**: `bench migrate` para registrar el nuevo job diario de artículos en el scheduler.
2. **Constantino/Vega**: Ahora que los Items existen en ERPNext, se pueden usár en cotizaciones y BOM. ¿Hay un campo de precio de compra por artículo en Tango (GVA45 o STA30)?

— Tango
