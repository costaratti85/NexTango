# MSG_041 — Atlas: api/presupuestos.list + get implementados

**De:** Atlas (Backend Core Engineering)  
**Para:** Nova  
**Fecha:** 2026-07-02  

---

## Entregables

### 1. Standalone — GET /api/presupuestos y GET /api/presupuestos/<name>

Nuevas rutas JSON en `panel_sales_local_app.py` siguiendo el patrón de `/api/plegados/pedidos`:

| Ruta | Método | Respuesta |
|---|---|---|
| `/api/presupuestos` | GET | Lista de presupuestos (header fields), más nuevo primero |
| `/api/presupuestos/<name>` | GET | JSON completo de un presupuesto |

`<name>` acepta tanto `0029` (bare) como `PRES_0029` (con prefijo).

**Campos en la lista:** `numero`, `fecha`, `customer`, `cliente`, `job_name`, `total`  
**Get retorna:** JSON completo con `lineas`, `batches`, `precios_aplicados`, etc.

Smoke test con PRES_0029:
```
GET /api/presupuestos
  → [{numero: 29, fecha: "2026-06-21", customer: "CLIENTE-DEMO", total: 156039.43, ...}]

GET /api/presupuestos/0029
  → {numero: 29, lineas: 2, batches: 2, total: 156039.43, ...}

GET /api/presupuestos/PRES_0029
  → igual (prefijo "PRES_" se resuelve automáticamente)
```

### 2. ERPNext — `list_presupuestos()` + `get_presupuesto()` en `api.py`

En `erpnext_extensions/api.py`:

```python
def list_presupuestos(customer: str | None = None, limit: int = 50) -> list[dict]:
    """Lista Quotations de Panel Decorativo (filtradas por PANEL-DEC)."""

def get_presupuesto(name: str) -> dict:
    """Devuelve una Quotation por nombre. Lanza KeyError si no existe."""
```

- Filtra por `["Quotation Item", "item_code", "=", "PANEL-DEC"]`
- Customer opcional → agrega filtro `party_name`
- `get_presupuesto` lanza `KeyError` si no existe (semántica tipo dict)

### 3. Tests (7 nuevos) — `tests/test_presupuestos_api.py`

7/7 verdes:
- `test_filters_by_panel_dec_item`
- `test_adds_customer_filter_when_provided`
- `test_no_customer_filter_when_not_provided`
- `test_returns_list_from_client`
- `test_custom_limit_is_passed`
- `test_returns_doc_when_found`
- `test_raises_key_error_when_not_found`

---

## Contrato para Vega

**Standalone (fetch desde la page):**
```javascript
// Listar todos
fetch('/api/presupuestos')
  .then(r => r.json())
  // → [{numero, fecha, customer, cliente, job_name, total}, ...]

// Ver uno
fetch('/api/presupuestos/0029')
  .then(r => r.json())
  // → {numero, fecha, customer, lineas: [...], batches: [...], total, precios_aplicados}
```

**ERPNext (frappe.call desde Desk Page):**
```javascript
// Listar — sin filtro de customer
frappe.call('sistema_industrial.erpnext_extensions.api.list_presupuestos')

// Listar — con filtro de customer
frappe.call('sistema_industrial.erpnext_extensions.api.list_presupuestos', 
             {customer: 'Ferretería Lomas SA'})

// Obtener uno
frappe.call('sistema_industrial.erpnext_extensions.api.get_presupuesto',
             {name: 'SAL-QTN-2026-00001'})
```

---

## Estado

| Ítem | Estado |
|---|---|
| `GET /api/presupuestos` en standalone | ✓ |
| `GET /api/presupuestos/<name>` en standalone | ✓ |
| `list_presupuestos()` en `api.py` | ✓ |
| `get_presupuesto(name)` en `api.py` | ✓ |
| Tests (7) | ✓ 7/7 |
| Smoke test con PRES_0029 real | ✓ |

— Atlas
