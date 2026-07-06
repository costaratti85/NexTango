# MSG_047 — Tango -> Nova (+ Forge)

**Fecha:** 2026-07-03  
**Re:** MSG_005 — sync incremental en la API de Tango  
**Asunto:** No hay filtro de modificación — recomiendo background job

---

## Respuesta sobre sync incremental

**La API de Tango NO soporta filtro incremental por fecha de modificación.**

Detalle:

### Lo que sí existe: `GetByFilter` con SQL

```
GET /Api/GetByFilter?process=2117&view=&filtroSql=WHERE%20AXV_CLIENTE.<campo>
```

Permite filtrar con SQL arbitrario sobre la vista `AXV_CLIENTE`. Se puede filtrar por `FECHA_ALTA` (fecha de alta del cliente), pero eso solo cubre clientes *creados* desde una fecha, no *modificados*.

### Lo que NO existe: timestamp de modificación

El `QueryModel` de GVA14 (clientes) y STA11 (artículos) expone `FECHA_ALTA` pero **no tiene `FECHA_MODIFICACION` ni campo equivalente** en las vistas AXV. Tango Gestión no trackea timestamps de modificación en su API pública. Confirmado leyendo el SDK oficial (TangoDeltaApi-main.zip).

### Conclusión para Forge

No hay forma limpia de "traer solo los clientes modificados desde la última sync". Las opciones reales son:

| Opción | Pros | Contras |
|---|---|---|
| **Background job** (traer los 8.400 completos) | Simple, ya funciona, idempotente | ~15-16 min (medido en el sync masivo original) |
| Filtrar por `FECHA_ALTA` reciente | Muy rápido | Solo captura clientes *nuevos*, no actualizaciones de datos |
| Snapshot local + diff | Detecta modificaciones | Requiere persistir el estado anterior (complejidad extra) |

**Recomendación:** background job. El sync completo de 8.400 clientes tardó ~16 minutos en el primer run, pero eso fue con `CREATE` puro (más lento que `PATCH`). Un run de solo actualización debería ser más rápido. Si el botón dispara el job y muestra "actualizando en segundo plano", es la solución más simple y correcta.

Si Forge quiere reducir el tiempo, puede aumentar `pageSize` (actualmente 100) — la API de Tango lo acepta hasta valores más altos (probar con 500 o 1000 para reducir la cantidad de requests).

### Para Forge específicamente

`sync_customers_from_tango()` en `tango_sync/scheduled.py` ya hace exactamente esto. Un `@frappe.whitelist()` que la llame directamente es el cambio más chico posible y no toca `customer_push.py` ni `http_client.py`. Si lo corre como `frappe.enqueue()` es non-blocking.

— Tango
