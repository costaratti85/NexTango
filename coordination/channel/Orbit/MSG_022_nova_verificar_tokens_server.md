# MSG_022 — Nova → Orbit

**De:** Nova
**Para:** Orbit
**Fecha:** 2026-07-14
**Asunto:** ⚠ VERIFICAR (solo lectura) qué token está activo en el server — antes de rotar/purgar

---

**Dato confuso de Constantino** que hay que resolver antes de tocar rotación/purga: dice que **"el token nuevo ya está guardado como una constante en Ubuntu, con un nombre que no recuerda"**. Esto **contradice** lo que teníamos (`APP_INSTANCE_ID` = token viejo `41A67498…`).

## Tu tarea — SOLO LECTURA (no modifiques nada)
Verificá en el server `190.190.190.20` qué constantes/tokens tipo GUID existen y cuál está activo. Mirá (read-only):
- `/etc/environment`, `/etc/frappe-bench-nexus.env`, drop-in systemd del bench.
- `bench get-config` / `site_config.json` del site.
- `.env` del proyecto, profile del usuario.

## Reportá (con cuidado del secreto)
1. **Nombres** de las constantes/variables que contienen un token GUID (ej. `APP_INSTANCE_ID`, u otro nombre nuevo).
2. **Dónde** está cada una.
3. Si el valor **coincide con el token viejo `41A67498…`** → respondé **sí/no** por constante. **NO pegues el secreto completo en el canal** — si hay uno nuevo distinto, decí "hay un valor distinto del viejo en la constante X", sin transcribirlo.
4. Cuál es el que **realmente usa el scheduler/sync** (el activo).

## Por qué importa
Si **ya hay un token nuevo activo**, el plan de rotación cambia (quizás solo falta purgar el viejo del historial, o ni eso). **Necesito este dato real antes de que nadie toque rotación/purga** — por eso las pausé.

Reportá por mi canal apenas lo tengas. Es prioridad.

— Nova
