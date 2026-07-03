# MSG_040 — Atlas: sync Tango → ERPNext completado

**De:** Atlas (Backend Core Engineering)  
**Para:** Nova  
**Fecha:** 2026-07-01  

---

## Entregables

### 1. Custom Fields en Customer (creados en servidor)

| Campo | Tipo | Prop |
|---|---|---|
| `si_tango_code` | Data | search_index=1 |
| `si_tango_id` | Int | — |

Creados via REST `POST /api/resource/Custom Field`. Frappe aplicó el schema inmediatamente (no requirió `bench migrate` explícito — mismo comportamiento que `is_billing_contact`).

### 2. `ERPNextClient` — métodos nuevos (`client.py`)

| Método | Qué hace |
|---|---|
| `patch_doc(doctype, name, data)` | PUT genérico — actualiza campos de cualquier doc |
| `list_docs(doctype, filters, fields, limit)` | GET con filtros JSON — retorna lista de docs |
| `find_customer_by_tango_code(code)` | Lookup por `si_tango_code`; retorna dict o None |

`list_quotations()` fue refactorizado para llamar `list_docs()` — sin cambio de interfaz.

### 3. `tango_sync/customer_push.py` (nuevo módulo)

Función principal:

```python
push_customers_to_erpnext(
    customers: list[TangoCustomer],
    client: ERPNextClient,
    *,
    default_price_list: str = "Precio Standard",
    default_customer_group: str = "Commercial",
) -> CustomerSyncResult
```

Lógica:
- **Lookup por `si_tango_code`** (= COD_GVA14) — los clientes manuales de ERPNext (sin `si_tango_code`) nunca son tocados.
- **Si no existe** → `create_doc("Customer", ...)` — result.created += 1
- **Si existe** → `patch_doc("Customer", erpnext_name, ...)` — result.updated += 1
- **Errores individuales** no detienen el sync — se registran en result.errors y la iteración continúa.

Mapeo IVA → Customer Group / Type:

| vat_condition | customer_group | customer_type |
|---|---|---|
| CF | Individual | Individual |
| RI / RS / MO / EX | Commercial | Company |
| None / desconocido | `default_customer_group` | Company |

`is_active=False` → `disabled=1` en ERPNext.

### 4. Tests (`tests/test_tango_customer_push.py`)

14 tests, 100% verdes:
- 8 tests de `_build_customer_doc` (mapeo de IVA, disabled, si_tango_code, price_list)
- 6 tests de `push_customers_to_erpnext` (create, update, error isolation, result counts, disabled propagation)

---

## Smoke test live contra servidor

```
Ronda 1 — crear 3 clientes de prueba:
  creados=3  actualizados=0  fallidos=0

Ronda 2 — re-sync idempotente:
  creados=0  actualizados=3  fallidos=0   <- sin duplicados

Lookup por si_tango_code:
  SMOKE-001 -> Ferretería Lomas SA   disabled=0  (RI, activo)
  SMOKE-002 -> Juan Perez            disabled=0  (CF, activo)
  SMOKE-003 -> Empresa Inactiva SRL  disabled=1  (MO, inactivo)
```

Los 3 clientes de smoke test quedan en ERPNext. Forge puede limpiarlos si lo desea, o dejarlos como datos de referencia.

---

## Prerequisito para producción

Antes de sincronizar los 8.426 clientes de Tango, Tango debe implementar la lógica de pull que entrega la lista completa (`TangoHTTPClient.get_customers()` ya existe — solo falta conectarlo al orquestador de sync).

El entry point para el sync masivo es:

```python
from sistema_industrial.erpnext_extensions.client import ERPNextClient
from sistema_industrial.tango_sync.http_client import TangoHTTPClient
from sistema_industrial.tango_sync.customer_push import push_customers_to_erpnext

tango = TangoHTTPClient(...)
erpnext = ERPNextClient()
customers = tango.get_customers()
result = push_customers_to_erpnext(customers, erpnext)
print(f"Sync: {result.created} creados, {result.updated} actualizados, {result.failed} fallidos")
```

---

## Estado

| Ítem | Estado |
|---|---|
| Custom Fields `si_tango_code` / `si_tango_id` en Customer | ✓ creados en servidor |
| `ERPNextClient.patch_doc` + `list_docs` + `find_customer_by_tango_code` | ✓ |
| `tango_sync/customer_push.py` | ✓ |
| Tests (14) | ✓ 14/14 |
| Smoke test live — create + idempotent update + lookup | ✓ |

— Atlas
