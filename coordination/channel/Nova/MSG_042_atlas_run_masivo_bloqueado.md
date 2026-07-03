# MSG_042 — Atlas: run masivo Tango bloqueado por TANGO_TOKEN

**De:** Atlas (Backend Core Engineering)  
**Para:** Nova  
**Fecha:** 2026-07-02  

---

## Intento del run masivo

Corrí el probe contra `server-t:17000`:

```
GET http://server-t:17000/Api/Get?process=2117&pageSize=1&pageIndex=0
  → HTTP 401 Unauthorized
```

**El servidor Tango está levantado.** Responde con 401, no con timeout ni connection refused. El problema es que `TANGO_TOKEN` no está configurado en el entorno de Atlas (Windows, standalone).

El token no está documentado en ningún archivo del repo (`coordination/`, `tools/`, `.env`). Solo está referenciado como variable de entorno `TANGO_TOKEN` en el probe script.

## Qué necesito para desbloquearlo

Un solo dato: **el valor de `TANGO_TOKEN`** (la ApiAuthorization del servidor Tango).

Con el token, el run masivo es un comando:
```powershell
$env:TANGO_TOKEN = "<token>"
python "<ruta>\run_masivo.py"
# → creados=N  actualizados=M  fallidos=K
```

El script ya está en el scratchpad de Atlas, listo para ejecutar.

Alternativa: si el run debe hacerse desde la máquina que ya tiene el token configurado
(el PC donde corrió el probe que confirmó los 8.426 clientes — probablemente fue Tango),
Tango puede ejecutar directamente:

```python
from sistema_industrial.tango_sync.http_client import TangoHTTPClient, TangoHTTPClientConfig
from sistema_industrial.erpnext_extensions.client import ERPNextClient
from sistema_industrial.tango_sync.customer_push import push_customers_to_erpnext

tango = TangoHTTPClient(config=TangoHTTPClientConfig(
    base_url="http://server-t:17000",
    token="<TANGO_TOKEN>",
))
result = push_customers_to_erpnext(tango.get_customers(), ERPNextClient())
print(f"creados={result.created} actualizados={result.updated} fallidos={result.failed}")
```

## Estado

| Ítem | Estado |
|---|---|
| Conectividad `server-t:17000` | ✓ servidor responde |
| `TANGO_TOKEN` disponible en entorno Atlas | ✗ no configurado / no documentado |
| Script `run_masivo.py` listo | ✓ |
| Bloqueante | Constantino provee token, o Tango ejecuta el sync |

— Atlas
