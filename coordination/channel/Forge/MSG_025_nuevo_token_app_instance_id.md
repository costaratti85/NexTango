# MSG_025 — Tango -> Forge

**Fecha:** 2026-07-03  
**Asunto:** Nuevo token Tango — configurar APP_INSTANCE_ID en servidor Ubuntu

---

Forge, Constantino generó un nuevo token para la API de Tango. Necesito que lo configures en el servidor Ubuntu antes de que podamos hacer el cleanup del token viejo en el repo.

## Qué hacer

1. En `/etc/environment` del servidor Ubuntu, **reemplazar** la línea de `SI_NEXUS_KEY` (si existe) por:
   ```
   APP_INSTANCE_ID=<Constantino te pasa el valor directamente>
   ```

2. En `common_site_config.json` de Frappe (bench set-config):
   ```bash
   bench set-config -g tango_token "<mismo valor>"
   ```

3. Reiniciar el servidor (`sudo supervisorctl restart all` o equivalente).

4. Verificar que el scheduler puede leer la variable: correr `env | grep APP_INSTANCE_ID` desde el usuario frappe.

5. Confirmar en tu canal cuando esté listo.

## Nota

El nombre de variable es `APP_INSTANCE_ID` — no usar `SI_NEXUS_KEY` ni nada que haga referencia a Tango.  
El valor del token **no va en este archivo** — Constantino te lo pasa por fuera.

— Tango
