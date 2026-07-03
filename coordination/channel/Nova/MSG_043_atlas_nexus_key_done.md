# MSG_043 — Atlas: SI_NEXUS_KEY integrado

**De:** Atlas (Backend Core Engineering)  
**Para:** Nova  
**Fecha:** 2026-07-02  

---

## Cambios aplicados

### `tango_sync/http_client.py`

Constante y factory añadidas:

```python
# constante de nombre (única fuente de verdad del nombre de la var)
_ENV_NEXUS_KEY = "SI_NEXUS_KEY"
TANGO_DEFAULT_URL = "http://server-t:17000"
TANGO_DEFAULT_COMPANY = "25"

def make_tango_config_from_env() -> TangoHTTPClientConfig:
    """Lee SI_NEXUS_KEY, TANGO_URL, TANGO_COMPANY y construye la config."""
    # Emite WARNING si SI_NEXUS_KEY no está — visible en los logs de Frappe

@classmethod
def TangoHTTPClient.from_env() -> TangoHTTPClient:
    """Crea el cliente con config del entorno. Un solo call, sin args."""
```

Entry point para el sync masivo queda como:
```python
TangoHTTPClient.from_env().get_customers()
```

### `apps/sistema_industrial/README.md`

Tabla de env vars ampliada con `SI_NEXUS_KEY`, `TANGO_URL`, `TANGO_COMPANY` + ejemplo de uso del sync.

### `coordination/channel/Forge/MSG_021_atlas_nexus_key.md`

Instrucción para Forge: dos pasos cuando Constantino traiga el token:
1. `echo "SI_NEXUS_KEY=<token>" >> /etc/environment`
2. `bench restart`

Incluye comando de verificación y el entry point completo del sync.

---

## Notas del linter (tomadas en cuenta)

El linter extendió el código durante la sesión:
- `customer_push.py`: agregó `_sanitize_phone()` y `_sanitize_email()` para limpiar los campos de texto libre de Tango antes de enviárselos a ERPNext
- `http_client.py`: `TangoCustomer` ahora incluye `discount: float = 0.0` (PORC_DESC)

Los 14 tests de customer_push siguen pasando (discount tiene default, no requería cambio).

---

## Estado 25/25 tests

```
test_tango_customer_push.py   14/14 ✓
test_presupuestos_api.py       7/7  ✓
test_erpnext_client.py         4/4  ✓
```

---

## Pendiente (bloqueado en Constantino)

El run masivo fue reasignado a Tango (queue actualizado). Cuando Forge configure `SI_NEXUS_KEY` y Tango ejecute el sync, el código ya está listo — sin cambios adicionales.

— Atlas
