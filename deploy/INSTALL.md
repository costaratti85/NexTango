# Reinstalar / instalar NexTango — guía paso a paso

**Objetivo:** levantar el sistema completo (ERPNext + app custom `sistema_industrial`) en
la misma máquina o en una nueva, en la menor cantidad de pasos, a partir de un **backup**.

## Método más simple elegido

> **Restaurar un backup nativo de Frappe sobre un bench recién iniciado.**

Es lo más simple porque `bench backup`/`bench restore` ya empaquetan y reponen base + archivos,
y el `site_config` del backup trae la `encryption_key` (sin la cual los datos encriptados no se
leen). Todo lo demás (código, entornos, assets) se regenera desde GitHub y `bench build`.

**En una máquina nueva son 3 comandos** (después de instalar prerequisitos):
```bash
./deploy/backup.sh                        # (en el server viejo, o usar un backup ya hecho)
scp -r backup/  nueva-maquina:/ruta/       # llevar el backup
BACKUP_DIR=/ruta/backup ADMIN_PW=... DB_ROOT_PW=... ./deploy/install.sh
```

## 1. Prerequisitos del SO (Ubuntu) — instalar antes

Versiones que hoy corre producción (usar estas o compatibles):

| Componente | Versión |
|---|---|
| Frappe / ERPNext | **version-16** (16.24.x / 16.25.x) |
| bench | 5.31 |
| Python (bench env) | 3.14 |
| Node + yarn | **24.x** + 1.22 |
| MariaDB | 10.6 |
| Redis | 6.x |

Instalar: `mariadb-server` (con `mysql_secure_installation` y config `utf8mb4`), `redis-server`,
Node 24 (via nvm o nodesource) + `npm i -g yarn`, Python 3 + `python3-dev`, `wkhtmltopdf` (con
qt patched), `git`, `pipx`. (El "easy install" de Frappe también sirve para el paso 1.)

## 2. Instalación automática

```bash
BACKUP_DIR=/ruta/al/backup \
ADMIN_PW='<clave admin nueva>' \
DB_ROOT_PW='<root de mariadb>' \
./deploy/install.sh
```
`install.sh` hace: `bench init` (Frappe 16) → `get-app erpnext` → **clona el monorepo `NexTango`
y symlinkea la app** (`apps/sistema_industrial` → `NexTango/apps/sistema_industrial`, porque la
app está anidada, no es un repo Frappe estándar) → crea el site → `install-app` → llama a
`restore.sh` → `bench setup production`.

## 3. Qué restaura `restore.sh` (lo crítico)

- **Base del site** (`bench restore` del `.sql.gz`): patrones, precios, coeficientes láser, clientes, cotizaciones, usuarios/API keys.
- **Archivos** del site (public + private).
- **`encryption_key`** + `tango_base_url` + `tango_company` → los repone en `site_config.json` desde el `site_config_backup.json` del backup. **Sin la misma `encryption_key`, las contraseñas encriptadas de la base no se pueden desencriptar.**
- **`/home/costa/planos`** (DXF + calibración láser; rutas congeladas en la base → mismo path).
- **`/etc/frappe-bench-nexus.env`** → `APP_INSTANCE_ID` (token de Tango; sin él no anda el sync).

## 4. Config manual que queda por completar

- Copiar `.env.example` → `.env` y llenar: `ERPNEXT_BASE_URL`, `ERPNEXT_API_KEY/SECRET`, `TANGO_URL`, `APP_INSTANCE_ID`.
- Que **`server-t` (Tango)** resuelva desde la máquina nueva: agregar a `/etc/hosts` su IP de la LAN, o usar la IP directa en `TANGO_URL`.

## 5. Qué NO hace falta llevar

Código (viene de GitHub), entornos Python (`env`, `.venv`), assets compilados (`bench build`),
datos de Redis (efímeros). Se regeneran solos.

## 6. Verificación post-restore

- `bench --site erp.local doctor` / `supervisorctl status` → servicios arriba.
- `/app/panel-decorativo` carga; una **cotización da total > 0** (no $0).
- Un patrón de la galería genera su DXF.

## Scripts

- `deploy/backup.sh` — backup completo (solo lectura; seguro). Deja todo en `/home/costa/backups/nextango-<ts>/` y lo verifica.
- `deploy/restore.sh <dir-backup> [site]` — restaura. **Pide confirmación** (pisa la base del site). Usar site aislado para probar.
- `deploy/install.sh` — instalación end-to-end en máquina nueva.

> Los scripts son un punto de partida sólido y probados en su parte de **backup** (ver el backup real ya generado). El `install.sh`/`restore.sh` NO se corrieron contra producción; probar el restore en un site/entorno aislado antes de confiar en él para un evento real.
