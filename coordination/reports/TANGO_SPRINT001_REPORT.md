# TANGO Sprint 001 — Reporte Final

**Agente:** Tango  
**Fecha:** 2026-07-02  
**Sprint objetivo:** GVA14 probe + sync masivo + 3 decisiones de Constantino  

---

## Resumen ejecutivo

- **8318 clientes creados** en ERPNext desde Tango (primer run)
- **110 fallidos** en primer run (ver sección errores)
- **Segundo run en curso** — idempotente, va a crear los 110 restantes y actualizar los 8318
- Las **3 decisiones de Constantino** implementadas en código y configuradas en ERPNext

---

## TASK_003 — Probe GVA14 (completado)

### Hallazgos

| Campo | Resultado |
|---|---|
| Process ID clientes (GVA14) | **2117** |
| Total de registros | **8,426** (respuesta API) / 8,428 reales |
| Formato respuesta API | `{"resultData": {"list": [...]}, "succeeded": true}` |

### Campos reales del API (descubiertos por probe)

| Campo Tango | Python | Nota |
|---|---|---|
| `COD_GVA14` | `code` | Clave principal |
| `RAZON_SOCI` | `name` (primero) | Nombre truncado (no RAZON_SOCIAL) |
| `NOM_COM` | `name` (fallback) | Nombre comercial |
| `CUIT` | `cuit` | OK |
| `DOMICILIO` | `address` | OK |
| `LOCALIDAD` | `city` | OK |
| `GVA18_DESCRIPCION` | `province` | No PROVINCIA |
| `C_POSTAL` | `postal_code` | No COD_POST |
| `COD_CATEGORIA_IVA` | `vat_condition` | No CONDICION_IVA |
| `GVA01_DESC_COND` | `payment_condition` | No CONDICION_PAGO |
| `E_MAIL` | `email` | No EMAIL |
| `TELEFONO_1` | `phone` | No TELEFONO |
| `ID_GVA14` | `tango_id` | FK interna |
| `CUPO_CREDI` | `credit_limit` | No LIMITE_CRED |
| `HABILITADO` | `is_active` | Boolean True/False (no INHABILITADO "S"/"N") |
| `PORC_DESC` | `discount` | Decisión Constantino #1 |

### Bugs encontrados y corregidos

1. **Formato de respuesta incorrecto**: el código buscaba `data`, `items`, `result`. Tango usa `resultData.list`.
2. **RAZON_SOCIAL truncado**: el campo real es `RAZON_SOCI` (10 chars max en DB Tango).
3. **INHABILITADO no existe**: el campo es `HABILITADO` (bool), no `INHABILITADO` "S"/"N".
4. **Todos los field names mismatched**: ver tabla arriba.

---

## TANGO_RUN_SYNC_MASIVO — Primer run (completado)

### Resultados

| Métrica | Valor |
|---|---|
| Clientes descargados de Tango | 8,428 |
| Creados en ERPNext | **8,318** |
| Actualizados | 0 |
| Fallidos | **110** |
| Duración | 956.9 segundos (~16 min) |

### Causa de los 110 errores

**109 errores — `InvalidPhoneNumberError` (HTTP 417)**

Tango almacena texto libre en el campo teléfono:
- `"gabriel 156733-3500"` — nombre antes del número
- `"Tesoreria Javier 733-1450"` — texto descriptivo
- `"4856-1775 / 4857 3349"` — múltiples números con separador
- `"4826-5568;4313-5313"` — separador punto y coma
- `"4501-9900 int 204 Andrea"` — extensión interna + nombre
- `"es el mismo de garplast"` — texto puro, sin número
- etc.

ERPNext rechaza cualquier teléfono que no sea un número limpio.

**1 error — `MySQLdb.OperationalError: Unknown column 'si_tango_discount'`**

El custom field `si_tango_discount` fue creado vía REST API **durante** el primer run. Frappe actualizó su meta pero la columna MySQL no existía todavía. El `on_update()` del Custom Field no ejecutó correctamente la primera vez.

**Solución aplicada entre runs:**

1. `_sanitize_phone()` y `_sanitize_email()` agregados a `customer_push.py` — extraen el primer número/email válido del texto libre de Tango.
2. Activación manual del schema: `PUT /api/resource/Custom Field/Customer-si_tango_discount` → Frappe ejecutó `on_update()` → columna MySQL creada → verificado con cliente de prueba.

### Segundo run (completado)

| Métrica | Valor |
|---|---|
| Creados | **110** (los que fallaron en run 1) |
| Actualizados | **8,302** |
| Fallidos | **16** (todos 404 por newlines en nombre) |
| Total | **8,428** |

**Estado final: 8,428 de 8,428 clientes presentes en ERPNext.** ✓

Los 16 fallos restantes son clientes con `\n` en el nombre almacenado en Frappe — cleanup planificado para Sprint 002.

---

## Decisiones de Constantino — Implementación

### 1. Descuentos por defecto (PORC_DESC)

- Campo `discount: float = 0.0` en `TangoCustomer` (schemas.py)
- Mapeado desde `PORC_DESC` en `get_customers()` (http_client.py)
- Custom Field `si_tango_discount` (Percent) creado en doctype Customer
- Incluido en `_build_customer_doc()` → se sincroniza en cada run
- **Uso futuro**: cuando se abra un presupuesto para un cliente, Vega/UI debe leer `si_tango_discount` del Customer y pre-cargar el descuento. Eso está fuera del scope de Tango.

### 2. Sync diario

- `apps/sistema_industrial/sistema_industrial/tango_sync/scheduled.py` — nuevo módulo con `sync_customers_from_tango()`
- `hooks.py` actualizado con `scheduler_events.daily`
- Lee token de `frappe.conf.get("si_nexus_key")` o `os.environ.get("SI_NEXUS_KEY")`
- **Pendiente de Forge**: `bench migrate` para que Frappe registre el scheduler, y `supervisorctl restart`

### 3. SI_NEXUS_KEY (naming final)

- La variable de entorno se llama **SI_NEXUS_KEY** — decisión de Nova (override sobre propuesta original de Constantino que era SI_NEXUS_KEY)
- `make_tango_config_from_env()` lee `frappe.conf.get("tango_token")` primero, luego `os.environ.get("SI_NEXUS_KEY")`
- `SERVIDOR_ERPNEXT.md` documentado con el valor del token (Nova lo actualizó)
- `MSG_022` + `MSG_023` enviados a Forge para configurar en Ubuntu + bench set-config
- **Pendiente de Forge**: `/etc/environment` + `bench set-config tango_token "..."` + restart + cleanup del repo

---

## Archivos modificados / creados

| Archivo | Cambio |
|---|---|
| `tango_sync/http_client.py` | PROCESS_CLIENTES=2117, _extract_records() para resultData.list, field names reales, discount, SI_NEXUS_KEY |
| `tango_sync/schemas.py` | discount field, docstring con field mapping real |
| `tango_sync/customer_push.py` | _sanitize_phone(), _sanitize_email(), si_tango_discount en doc |
| `tango_sync/scheduled.py` | **NUEVO** — sync diario para Frappe scheduler |
| `tango_sync/customer_push.py` | creado en sesión anterior por Atlas, refactorizado por Tango |
| `hooks.py` | scheduler_events.daily |
| `tools/probe_tango_clientes.py` | SI_NEXUS_KEY, _extract_records compatible |
| `coordination/SERVIDOR_ERPNEXT.md` | Tango API section + SI_NEXUS_KEY |
| `coordination/channel/Forge/MSG_022_tango_nexus_key.md` | Instrucciones para Forge |

---

## Nota: cliente 000598 (edge case)

Cliente ALANIZ SANTIAGO FERNANDO (código 000598) tiene newlines en el campo RAZON_SOCI de Tango. El primer run lo creó en ERPNext con `name` = "ALANIZ SANTIAGO FERNANDO\nALANIZ SANTIAGO FERNANDO\nALANIZ F" (con newlines reales). Frappe no puede resolver este nombre via URL en el PUT → el segundo run y todos los syncs futuros fallan al actualizarlo.

**Fix ya aplicado** en `http_client.py:get_customers()`: normalización de whitespace con `" ".join(str.split())` → los nuevos clientes nunca tendrán este problema. El cliente 000598 ya existente en ERPNext necesita ser borrado y recreado manualmente (o el daily sync del día siguiente lo creará como nuevo cliente tras el delete).

---

## Sync artículos Tango → ERPNext (completado 2026-07-02)

### Resultados

| Métrica | Valor |
|---|---|
| Artículos en Tango (STA11, process 87) | **2.189** |
| Creados en ERPNext | **2.179** |
| Actualizados (subset de prueba) | **10** |
| Fallidos | **0** |

**Todos los artículos presentes en ERPNext con 0 errores.**

### Mapeo de campos

| Campo Tango | Campo ERPNext | Decisión |
|---|---|---|
| `COD_STA11` | `item_code` | Clave natural (sin custom field) |
| `DESCRIPCIO` | `item_name` + `description` | Whitespace normalizado |
| `FAMILIA` | `item_group` | 7 familias → 5 grupos existentes |
| `MEDIDA_STOCK_CODIGO` ("UNIDAD") | `stock_uom` = "Nos" | Único UoM del catálogo |
| — | `is_stock_item` = 0 | Catálogo, no inventario |

### Archivos creados/modificados

- `tango_sync/article_push.py` — push idempotente con `_FAMILIA_TO_ITEM_GROUP`
- `tango_sync/scheduled.py` — `sync_articles_from_tango()` agregada
- `hooks.py` — job diario registrado
- `tools/probe_articles_sync.py` — script de prueba

---

## Pendientes para próximo sprint

| Item | Bloqueado por | Prioridad |
|---|---|---|
| Scheduler diario activo en server | Forge (bench migrate + restart, MSG_022) | Alta |
| SI_NEXUS_KEY en /etc/environment | Forge (MSG_022 + MSG_023) | Alta |
| Cleanup token del repo | **Tango** — bloqueado hasta confirmación de Forge | Alta |
| Discount UI en presupuestos | Vega — leer si_tango_discount al abrir presupuesto | Media |
| Precios de artículos (GVA45/STA30) | A confirmar con Constantino — ¿expone Tango? | Media |
| CUIT dedup risk | 8,318 clientes sin CUIT → name = COD_GVA14 si hay colisión | Baja |

---

*Reporte generado por Tango — 2026-07-02*
