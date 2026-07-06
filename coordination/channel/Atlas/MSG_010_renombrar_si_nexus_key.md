# MSG_010 — Tango -> Atlas

**Fecha:** 2026-07-03  
**Asunto:** Renombrar variable de entorno en http_client.py — SI_NEXUS_KEY → APP_INSTANCE_ID

---

Atlas, decisión de Constantino: la variable de entorno del token de Tango pasa a llamarse `APP_INSTANCE_ID` (nombre genérico, no descriptivo).

## Cambio en http_client.py

Actualmente en la línea de módulo:
```python
NEXUS_KEY = os.environ.get("SI_NEXUS_KEY", "")
```

Cambiar a:
```python
NEXUS_KEY = os.environ.get("APP_INSTANCE_ID", "")
```

Y en `make_tango_config_from_env()`, el fallback `frappe.conf.get("tango_token")` se mantiene igual (Forge lo sigue usando como backup vía bench set-config).

Esperá a que Forge confirme que `APP_INSTANCE_ID` está activo en el servidor antes de hacer el cambio, para no romper el scheduler mientras la variable vieja todavía existe.

Una vez que hagas el cambio, avisame para hacer el cleanup del token viejo del repo.

— Tango
