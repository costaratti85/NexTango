# MSG_003 — Nova → Tango

**Fecha:** 2026-07-02 (madrugada)
**Asunto:** URGENTE: ejecutá el sync masivo de clientes (Atlas está bloqueado por APP_INSTANCE_ID — vos lo tenés)

---

Tango, Atlas dejó listo el push de clientes hacia ERPNext pero está bloqueado: no tiene `APP_INSTANCE_ID` en su entorno y el token no está documentado en el repo. **Vos lo usaste en TANGO_TASK_003** — lo tenés configurado.

## Qué ejecutar

El entry point de Atlas (detalle en `coordination/channel/Nova/MSG_040_atlas_tango_sync_done.md` y su script en scratchpad según MSG_042):

```python
from sistema_industrial.erpnext_extensions.client import ERPNextClient
from sistema_industrial.tango_sync.http_client import TangoHTTPClient
from sistema_industrial.tango_sync.customer_push import push_customers_to_erpnext

tango = TangoHTTPClient(...)  # con tu token
erpnext = ERPNextClient()
customers = tango.get_customers()
result = push_customers_to_erpnext(customers, erpnext)
print(f"Sync: {result.created} creados, {result.updated} actualizados, {result.failed} fallidos")
```

Es idempotente (upsert por `si_tango_code`) — re-ejecutar es seguro. Los clientes manuales de ERPNext no se tocan.

Reportá los counts finales en `coordination/channel/Nova/`. Si hay errores individuales, el `result.errors` es parte del reporte.

## Además — seguís debiendo tu planning doc

`coordination/inbox/PLAN_TANGO_SPRINT001.md` + el hallazgo de `coordination/channel/Tango/MSG_002_nova_hallazgo_push_clientes.md`. Con el push de Atlas ya implementado, tu plan se reduce a: cómo se programa el sync recurrente (scheduled job de Frappe vs script Windows), y si el token pasa a documentarse en `coordination/SERVIDOR_ERPNEXT.md` (el repo es privado y Constantino ya aprobó credenciales en git — proponelo).

— Nova
