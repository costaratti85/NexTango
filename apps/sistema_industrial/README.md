# sistema_industrial

App Frappe/ERPNext para SistemaIndustrial Nextango.

## Variables de entorno

| Variable | Descripción | Default |
|---|---|---|
| `ERPNEXT_URL` | URL base del servidor ERPNext | `http://190.190.190.20` |
| `ERPNEXT_API_KEY` | API key del usuario de integración (provisto por Forge) | — |
| `ERPNEXT_API_SECRET` | API secret del usuario de integración (provisto por Forge) | — |
| `APP_INSTANCE_ID` | Token ApiAuthorization del servidor Tango (configurado en `/etc/environment` por Forge) | — |
| `TANGO_URL` | URL base del servidor Tango | `http://server-t:17000` |
| `TANGO_COMPANY` | Número de empresa en Tango | `25` |

### Primer POST real a ERPNext

Una vez que Forge entregue las API keys (TASK_045):

```bash
export ERPNEXT_URL=http://190.190.190.20
export ERPNEXT_API_KEY=<api_key>
export ERPNEXT_API_SECRET=<api_secret>
```

### Sync Tango → ERPNext

Requiere `APP_INSTANCE_ID` configurado. Uso más simple:

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

Desde Python:

```python
from sistema_industrial.erpnext_extensions.api import send_quotation
from sistema_industrial.quoting.quotation_builder import build_erpnext_quotation_payload

payload = build_erpnext_quotation_payload(quotation, price_cache)
result = send_quotation(payload)
print(result["name"])  # ej: QUOT-0001
```
