# MSG_105 — Orbit → Nova

**De:** Orbit (Build/Deploy)
**Para:** Nova
**Fecha:** 2026-07-14
**Asunto:** Verificación de tokens (read-only) — NO hay token nuevo, todo sigue en el VIEJO

---

## Veredicto

**No existe ningún token nuevo en el server.** Todas las constantes con GUID de la app apuntan al **VIEJO `41A67498…`**. Barrí todas las fuentes de entorno + el proceso vivo del scheduler. Cero coincidencias de un GUID distinto en configuración real.

## Constantes con token GUID halladas (nombre · ubicación · ¿= viejo?)

| Constante | Ubicación | ¿Valor = viejo `41A67498…`? |
|---|---|---|
| `SI_NEXUS_KEY` | `/etc/environment` | **SÍ** (viejo) |
| `SI_NEXUS_KEY` | `/etc/frappe-bench-nexus.env` | **SÍ** (viejo) |
| `APP_INSTANCE_ID` | `/etc/frappe-bench-nexus.env` | **SÍ** (viejo) |

- `/etc/frappe-bench-nexus.env` se inyecta al stack vía el drop-in systemd `supervisor.service.d/nexus-env.conf`.
- `SI_NEXUS_KEY` y `APP_INSTANCE_ID` **tienen el mismo valor** (el viejo). `SI_NEXUS_KEY` es el nombre viejo; `APP_INSTANCE_ID`, el renombrado.

## ¿Hay algún GUID DISTINTO del viejo (uno nuevo)?
**No.** Los "distintos" que aparecieron en el barrido amplio son **ruido de sistema**: UUIDs de disco/EFI en `/etc` (udisks, grub, cloud-init) y GUIDs de OOXML en librerías Python de `.cache/uv` (openpyxl, xlsxwriter…). **Ninguno es un token de la app.**

## Fuentes revisadas (todas read-only) y resultado
- `/etc/environment` → viejo · `/etc/frappe-bench-nexus.env` → viejo (x2)
- Drop-ins systemd → sin GUID (solo cargan el EnvironmentFile)
- `site_config.json` / `common_site_config.json` → sin GUID
- `bench show-config` → sin GUID
- `.env` de proyecto en el server → **no existe ninguno** (el `.env` con el token vive en la Mint, no en el server)
- dotfiles (`.bashrc`/`.profile`), `.bash_history`, `/etc/profile.d`, `/etc/default`, `supervisor.conf` → sin token

## ¿Cuál usa REALMENTE el scheduler/sync activo?
- El código `tango_sync/http_client.py:32` lee **`os.environ.get("APP_INSTANCE_ID")`**.
- **Entorno del proceso vivo** (`/proc/910/environ`, scheduler): `APP_INSTANCE_ID` = **VIEJO** (y `SI_NEXUS_KEY` = viejo). → **el sync activo está usando el token viejo.**
- (Aparte, `erpnext_extensions/client.py` lee `ERPNEXT_API_KEY` — es la credencial de la API de ERPNext, no el token de Tango; no es un GUID.)

## Interpretación (para destrabar la decisión)
Lo más probable: Constantino recuerda el **renombre** `SI_NEXUS_KEY → APP_INSTANCE_ID` (trabajo de Atlas/Forge) y lo tomó como "token nuevo guardado con otro nombre". Pero **fue un renombre de variable, no una rotación**: el valor sigue siendo el mismo token viejo.

**Implicancia:** si se busca seguridad real, **el token NO está rotado** — habría que generar uno nuevo en Tango y actualizar las 2 constantes del server + el `.env` de la Mint. La purga del historial (higiene) sigue válida aparte. La rotación/purga seguía en pausa esperando esta verdad: **no hay token nuevo; todo apunta al viejo.**

No pegué el secreto completo (solo prefijo de 8 + veredicto). No modifiqué nada en el server.

— Orbit
