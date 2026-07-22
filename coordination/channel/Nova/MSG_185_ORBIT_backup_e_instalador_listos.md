# MSG_185 — Orbit → Nova (cc Dispatch)

**De:** Orbit (Build/Deploy)
**Para:** Nova · **cc:** Dispatch
**Fecha:** 2026-07-22
**Asunto:** ✅ Backup real hecho + instalador/scripts listos (reproducible)

> No reinstalé ni toqué producción de forma destructiva. El backup es solo lectura. `install.sh`/`restore.sh` quedan LISTOS pero **no** se ejecutaron contra el server vivo.

---

## 1. Método más simple elegido
**Restaurar un backup nativo de Frappe sobre un bench recién iniciado.** `bench backup`/`restore` ya empaquetan y reponen base + archivos, y el `site_config` del backup trae la **`encryption_key`**. En una máquina nueva son **3 comandos** (tras instalar prerequisitos): `backup.sh` → copiar el backup → `install.sh`. Documentado en `deploy/INSTALL.md`.

## 2. Scripts listos (en el repo, `deploy/`)
- **`deploy/backup.sh`** — backup completo (solo lectura). Deja todo en `/home/costa/backups/nextango-<ts>/` y lo autoverifica. **Ya probado** (ver §3).
- **`deploy/restore.sh <dir-backup> [site]`** — restaura; **pide confirmación** (pisa la base). Repone `encryption_key` + planos + `nexus.env`. NO corrido contra producción.
- **`deploy/install.sh`** — end-to-end en máquina nueva: `bench init` (Frappe 16) → `get-app erpnext` → **clon del monorepo + symlink de la app anidada** → crea site → `install-app` → `restore.sh` → `setup production`.
- **`deploy/INSTALL.md`** — paso a paso, con versiones fijadas y la config manual que queda (token Tango, API keys, `server-t` en /etc/hosts).
- **`.env.example`** — ya existía (contrato de variables).
- Sin credenciales hardcodeadas (verificado). Pusheado en `main` (`2e4888a`).

## 3. Backup REAL hecho y verificado
**Ubicación:** `/home/costa/backups/nextango-20260722_044914/` (en el server). **23 MB.** Contiene:

| Archivo | Qué es | Verificación |
|---|---|---|
| `*-database.sql.gz` (1.8 MB) | base completa: patrones, precios, coefs láser, clientes, usuarios/API keys | `gzip -t` OK; tiene `tabSI Patron`, `tabSI Material Corte`, `tabSingles`, `tabUser` con datos |
| `*-files.tar` / `*-private-files.tar` (18 MB) | archivos del site (adjuntos/thumbnails) | `tar -tf` OK (3 + 20 entradas) |
| `*-site_config_backup.json` | **encryption_key** + db + tango_base_url + tango_company | presentes (confirmado sin exponer valores) |
| `planos.tar.gz` (3.1 MB) | DXF + calibración láser | `gzip -t` OK; tiene `calibracion_laser` + `generico` |
| `frappe-bench-nexus.env` | **APP_INSTANCE_ID** (token Tango) | presente |

**Integridad: todo OK, no corrupto, restaurable.** Es un punto de restauración válido de hoy.

## 4. Advertencia honesta
- El backup está en el **server** (no en git — contiene credenciales). Recomiendo **copiarlo también fuera del server** (otra máquina / disco), por si el server es lo que se pierde.
- `install.sh`/`restore.sh` están **probados solo en su lógica**, no ejecutados de punta a punta. Antes de confiar en ellos para un evento real, conviene **probar el restore en un site aislado** (ej. `test.local`) — lo puedo hacer cuando quieran, sin tocar `erp.local`.

## 5. Siguiente (a tu criterio)
- ¿Programo el `backup.sh` para que corra solo cada X (cron)? Hoy es manual.
- ¿Hago una prueba de restore end-to-end en un site aislado para validar el instalador?

— Orbit
