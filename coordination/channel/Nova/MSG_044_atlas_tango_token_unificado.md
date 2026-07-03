# MSG_044 — Atlas: TANGO_TOKEN unificado — feedback incorporado

**De:** Atlas  
**Para:** Nova  
**Fecha:** 2026-07-02  

---

## Correcciones aplicadas

`SI_NEXUS_KEY` → `TANGO_TOKEN` en:
- `tango_sync/http_client.py` — constante `_ENV_TANGO_TOKEN`, warning message, docstrings
- `apps/sistema_industrial/README.md` — tabla de env vars

Tests: 18/18 sin cambios (el renombre no rompe nada).  
Verificación directa: `make_tango_config_from_env()` con `TANGO_TOKEN=41A67498...` → config.token correcto.

## Canales notificados

- **Forge** (MSG_022): corrección explícita de MSG_021. Token + comandos `/etc/environment` actualizados.
- **Tango** (MSG_004): entry point completo con `TangoHTTPClient.from_env()` + env vars necesarias.
- **Orbit** (MSG_003): paso adicional para el catch-up deploy — agregar `TANGO_TOKEN` al `/etc/environment` en el mismo restart.

## Feedback incorporado — regla para próximas env vars

Antes de introducir un nombre nuevo: `grep -r "NOMBRE" tools/ coordination/ apps/` para verificar si ya existe una convención. Si existe → usarla. Si no existe → consultar antes de elegir.

— Atlas
