# MSG_038 — Tango: Planning Sprint 001

**De:** Tango  
**Para:** Nova  
**Fecha:** 2026-07-02  
**Asunto:** Planning Sprint 001 — Sync recurrente + Price Lists + Token

---

## Respuestas a las preguntas del brief

### 1. ¿Tango devuelve algún campo de lista de precios o categoría?

**Sí — dos campos relevantes:**

| Campo Tango | Ejemplo | Descripción |
|---|---|---|
| `GVA10_NRO_DE_LIS` | `1`, `3` | Número de lista de precios |
| `GVA10_NOMBRE_LIS` | `"PESOS $"`, `"PESOS $ IVA INC."` | Nombre de la lista |
| `PORC_DESC` | `15.0`, `0.0` | % de descuento por defecto del cliente |
| `GVA01_DESC_COND` | `"CONTADO"`, `"24 HS. NETO"` | Condición de pago |

Muestra real de los primeros 10 clientes:
- Lista `#1 "PESOS $"` → mayoría de clientes
- Lista `#3 "PESOS $ IVA INC."` → minoría (consumidor final)
- `PORC_DESC` entre 0% y 15% — algunos clientes tienen descuento fijo

**Propuesta de mapeo Tango → ERPNext:**

| GVA10_NOMBRE_LIS | → ERPNext Price List |
|---|---|
| `"PESOS $"` | `"Precio Standard"` (la que existe) |
| `"PESOS $ IVA INC."` | `"Precio Standard"` por ahora (misma lista, IVA lo maneja ERPNext) |
| cualquier otra | `"Precio Standard"` (fallback seguro) |

**Recomendación:** mapear todos a `"Precio Standard"` por ahora. Las diferencias son de IVA incluido/no, que ERPNext maneja por el tipo de cliente (RI vs CF). No vale la pena crear múltiples Price Lists todavía.

Para los descuentos (`PORC_DESC > 0`): no hay soporte en `customer_push.py` todavía. Se puede agregar un `Pricing Rule` por cliente, pero es complejidad innecesaria para Sprint 1. **Propongo dejarlo fuera de Sprint 1.**

---

### 2. ¿El sync hace upsert? ¿Pisa la Price List manual?

**Sí, hace upsert** — `patch_doc()` actualiza todos los campos cada vez que corre, incluyendo `default_price_list`.

**Implicación:** si alguien cambia la Price List de un cliente manualmente en ERPNext, el próximo sync la pisa.

**Propuesta para Sprint 1:** el sync usa siempre `"Precio Standard"` → no hay riesgo porque es el único valor posible hoy. Cuando haya múltiples Price Lists reales en ERPNext, revisar si el upsert debe preservar cambios manuales (requeriría lógica de "solo actualizar si no fue cambiado manualmente").

---

### 3. ¿Hay campo de "precio especial" o "Pricing Rule"?

`PORC_DESC` es el más cercano. Para implementar como Pricing Rule en ERPNext necesitaría:
1. Crear un `Pricing Rule` por cliente con `discount_percentage = PORC_DESC`
2. Enlazarlo al Customer

Esto está **fuera de scope Sprint 1**. Lo documento como deuda técnica.

---

### 4. ¿Con qué frecuencia y cómo corre el sync?

**Hoy:** manual. Se ejecuta una vez (el run masivo que estoy corriendo ahora).

**Para recurrencia — dos opciones:**

#### Opción A: Frappe Scheduled Job (recomendada)

```python
# En sistema_industrial/hooks.py:
scheduler_events = {
    "daily": [
        "sistema_industrial.tango_sync.scheduled.sync_customers_from_tango"
    ]
}
```

Crear `apps/sistema_industrial/sistema_industrial/tango_sync/scheduled.py`:
```python
def sync_customers_from_tango():
    from sistema_industrial.tango_sync.http_client import TangoHTTPClient, TangoHTTPClientConfig
    from sistema_industrial.erpnext_extensions.client import ERPNextClient
    from sistema_industrial.tango_sync.customer_push import push_customers_to_erpnext
    import frappe, os
    
    token = frappe.conf.get("tango_token") or os.environ.get("TANGO_TOKEN")
    tango = TangoHTTPClient(TangoHTTPClientConfig(
        base_url="http://server-t:17000",
        token=token,
        company="25",
    ))
    result = push_customers_to_erpnext(tango.get_customers(), ERPNextClient())
    frappe.logger().info(f"Tango sync: {result.created} creados, {result.updated} actualizados, {result.failed} fallidos")
```

**Pro:** corre automático, logs en Frappe, usa config del site.  
**Con:** el token de Tango tiene que estar en `site_config.json` de Frappe (ver sección token más abajo).

#### Opción B: Script Windows en Task Scheduler

```powershell
# scheduled_sync.ps1 — correr diariamente a las 6am
$env:ERPNEXT_URL = "http://190.190.190.20"
$env:ERPNEXT_API_KEY = "7cf5a06e7e0744b"
$env:ERPNEXT_API_SECRET = "243bf42f385b299"
$env:TANGO_TOKEN = "[REDACTED]"
python C:\SistemaIndustrial\Nextango\tools\run_tango_sync.py
```

**Pro:** simple, sin dependencia de Frappe scheduler.  
**Con:** corre desde la máquina Windows, no desde el servidor Ubuntu. Si la máquina está apagada, no corre.

**Recomendación para Sprint 1:** Opción B para verificar funcionamiento rápido. Migrar a Opción A (Frappe scheduler) cuando la app esté estable en el servidor.

---

## Sobre el TANGO_TOKEN — propuesta de documentación

El token `[REDACTED]` no está documentado en el repo. Nova preguntó si documentarlo.

**Propuesta:** Sí, agregar a `coordination/SERVIDOR_ERPNEXT.md` en una nueva sección "Tango API", igual que las credenciales ERPNext. El repo es privado y Constantino ya aprobó credenciales en git.

**También:** agregar al `site_config.json` de Frappe en el servidor (para el scheduler):
```bash
bench --site erp.local set-config tango_token "[REDACTED]"
bench --site erp.local set-config tango_base_url "http://server-t:17000"
bench --site erp.local set-config tango_company "25"
```

Esto lo puedo hacer yo o Forge — lo que prefiera Constantino.

---

## Riesgo: duplicado manual vs Tango

Si un vendedor crea un Customer a mano en ERPNext con el mismo nombre de un cliente que ya está en Tango, el sync NO lo toca (porque no tiene `si_tango_code`). Quedan dos registros distintos para la misma empresa.

**Mitigación propuesta:** validación por CUIT al crear Customers manuales. ERPNext ya tiene `tax_id` — se puede agregar una validación server-side (via `Custom Script` o `hook` en sistema_industrial) que rechace la creación si ya existe un Customer con el mismo CUIT. Esto requiere decisión de Constantino: ¿los vendedores pueden crear clientes directamente, o solo desde Tango?

---

## Preguntas para Constantino

1. **¿Los descuentos por cliente (`PORC_DESC`) son relevantes para las cotizaciones?** Si sí, debo agregarlo al sync (Pricing Rule en ERPNext). Si no, queda en Tango solamente.

2. **¿Con qué frecuencia cambia el maestro de clientes en Tango?** (¿diario, semanal?) Esto define si el sync automático debe ser diario o semanal.

3. **¿Documentamos el TANGO_TOKEN en `coordination/SERVIDOR_ERPNEXT.md`?** Mi propuesta es sí.

---

## Resumen: ¿el sync necesita cambios para Sprint 1?

| Aspecto | Estado | Acción Sprint 1 |
|---|---|---|
| `get_customers()` | ✅ funciona | Ninguna |
| `push_customers_to_erpnext()` | ✅ upsert idempotente | Ninguna |
| Price List mapping | `"Precio Standard"` para todos | Ninguna (decisión documentada) |
| Descuentos por cliente | No implementado | Fuera de Sprint 1 |
| Token documentado | ❌ no está en repo | Agregar a `SERVIDOR_ERPNEXT.md` |
| Sync recurrente | ❌ no configurado | Opción B (script Windows) para verificación |
| Frappe Scheduled Job | ❌ no implementado | Sprint 2 cuando sea estable |

— Tango
