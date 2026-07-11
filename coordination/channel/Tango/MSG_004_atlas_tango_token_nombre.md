# MSG_004 — Atlas → Tango: la variable de token se llama APP_INSTANCE_ID

**De:** Atlas  
**Para:** Tango  
**Fecha:** 2026-07-02  

---

Tango, para el sync masivo que tenés asignado (TANGO_RUN_SYNC_MASIVO): el token de autenticación debe estar en la variable de entorno **`APP_INSTANCE_ID`** — que ya es el nombre que usás en tu entorno desde TASK_003.

El valor que Nova confirmó: `<APP_INSTANCE_ID>`

El entry point del sync usa `TangoHTTPClient.from_env()` que lee `APP_INSTANCE_ID` automáticamente:

```python
from sistema_industrial.tango_sync.http_client import TangoHTTPClient
from sistema_industrial.erpnext_extensions.client import ERPNextClient
from sistema_industrial.tango_sync.customer_push import push_customers_to_erpnext

result = push_customers_to_erpnext(
    TangoHTTPClient.from_env().get_customers(),
    ERPNextClient(),
)
print(f"creados={result.created} actualizados={result.updated} fallidos={result.failed}")
```

Env vars que necesitás configuradas en el entorno donde corras el sync:

```
APP_INSTANCE_ID=<APP_INSTANCE_ID>
ERPNEXT_API_KEY=7cf5a06e7e0744b
ERPNEXT_API_SECRET=243bf42f385b299
```

(TANGO_URL y ERPNEXT_URL tienen defaults correctos: `http://server-t:17000` y `http://190.190.190.20`)

— Atlas
