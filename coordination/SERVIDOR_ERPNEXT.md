# Servidor ERPNext — Datos de acceso

## Acceso SSH

| Campo | Valor |
|---|---|
| Host | 190.190.190.20 |
| Usuario SSH | costa |
| Contraseña SSH | sunshine |
| Hardware | Gigabyte GA-J1800N-D2P, Intel Celeron J1800 (2 cores), 8GB RAM |
| Disco | 54GB total, ~44GB libres al inicio |

```bash
ssh costa@190.190.190.20
```

## ERPNext

| Campo | Valor |
|---|---|
| URL | http://190.190.190.20 |
| Nombre del site | erp.local |
| Usuario | administrator |
| Contraseña | ErpAdmin_2026 |

## Base de datos

| Campo | Valor |
|---|---|
| Motor | MariaDB 10.6 |
| Usuario root | root |
| Contraseña root | ErpNextDB_2026 |

## Stack instalado

| Componente | Versión |
|---|---|
| Ubuntu | 22.04.5 LTS |
| Frappe | v16 (version-16) |
| ERPNext | v16 (version-16) |
| Python | 3.14.6 (vía ppa:deadsnakes/ppa) |
| Node.js | 24.18.0 |
| yarn | 1.22.22 |
| MariaDB | 10.6 |
| nginx | 1.18.0 |
| Supervisor | 4.2.1 |
| frappe-bench | 5.31.0 |

## Rutas clave en el servidor

```
/home/costa/frappe-bench/                     — bench root
/home/costa/frappe-bench/sites/erp.local/     — site data
/home/costa/frappe-bench/sites/assets/        — assets estáticos
/home/costa/frappe-bench/config/nginx.conf    — config nginx (con fixes manuales)
/home/costa/frappe-bench/config/supervisor.conf — config supervisor (con fixes manuales)
/home/costa/frappe-bench/logs/                — logs de workers
/etc/nginx/conf.d/frappe-bench.conf           — symlink al nginx.conf
/etc/supervisor/conf.d/frappe-bench.conf      — symlink al supervisor.conf
/tmp/erpnext_install.log                      — log completo de la instalación
```

## Estado actual (2026-07-01)

**Instalación completa. Todos los servicios corriendo.**

```
nginx                                                    active
supervisor                                               active
mariadb                                                  active
redis-server                                             active
frappe-bench-redis:frappe-bench-redis-cache              RUNNING
frappe-bench-redis:frappe-bench-redis-queue              RUNNING
frappe-bench-web:frappe-bench-frappe-web                 RUNNING (gunicorn :8000)
frappe-bench-web:frappe-bench-node-socketio              RUNNING (:9000)
frappe-bench-workers:frappe-bench-frappe-long-worker-0   RUNNING
frappe-bench-workers:frappe-bench-frappe-schedule        RUNNING
frappe-bench-workers:frappe-bench-frappe-short-worker-0  RUNNING
```

- `http://190.190.190.20` → página de login ERPNext ✓
- Login administrator / ErpAdmin_2026 → `{"message":"Logged In"}` vía API ✓
- Assets CSS/JS: 200 ✓
- Company, moneda, plan de cuentas: **pendiente de configurar**

## Fixes manuales aplicados (no regen sin re-aplicar)

Si se regeneran los configs con `bench setup nginx` o `bench setup supervisor`, hay que volver a aplicar:

1. **nginx.conf** — `access_log ... main` → `access_log ... combined`  
   (Ubuntu nginx no define el formato `main`)

2. **supervisor.conf** — `command=None ` → `command=/home/costa/.local/bin/bench `  
   (bench 5.31 no resuelve su propio path en entorno no-interactivo)

3. **Permisos assets:**
   ```bash
   chmod o+x /home/costa
   chmod -R o+rX /home/costa/frappe-bench/sites/assets/
   chmod -R o+rX /home/costa/frappe-bench/apps/frappe/frappe/public/
   chmod -R o+rX /home/costa/frappe-bench/apps/erpnext/erpnext/public/
   ```

## Tango API — credenciales

| Campo | Valor |
|---|---|
| Servidor | `http://server-t:17000` |
| APP_INSTANCE_ID (ApiAuthorization) | `<APP_INSTANCE_ID>` |
| Company | `25` |
| Process clientes (GVA14) | `2117` |
| Process artículos (STA11) | `87` |
| Process movimientos stock | `12567` (endpoint `GetApiLiveQueryData`) |

Token encontrado 2026-07-01 en `Programas_hechos/OCR Proveedores/Token.txt`.

### Token como variable de entorno `APP_INSTANCE_ID` (2026-07-02)

El token de Tango está expuesto a los procesos del servidor como `APP_INSTANCE_ID` en **dos lugares** (los dos hacen falta):

1. **`/etc/environment`** → `APP_INSTANCE_ID="..."`. Sirve para **shells interactivos** (login SSH). Verificado: `echo $APP_INSTANCE_ID` devuelve el token.
2. **`/etc/frappe-bench-nexus.env`** (chmod 600, root) + drop-in systemd `/etc/systemd/system/supervisor.service.d/nexus-env.conf` con `EnvironmentFile=-/etc/frappe-bench-nexus.env`. Esto es lo que hace que **los workers de Frappe** (gunicorn/queue bajo supervisor) vean la variable.

> **IMPORTANTE:** `/etc/environment` por sí solo **NO** llega a los workers de Frappe — lo lee PAM en logins interactivos, no supervisord (arrancado por systemd en el boot). `bench restart` reinicia solo los hijos, que heredan el entorno viejo de supervisord. Para que un cambio de `APP_INSTANCE_ID` impacte a los workers hay que editar `/etc/frappe-bench-nexus.env` y `sudo systemctl restart supervisor` (no alcanza `bench restart`).
>
> En código Frappe: `os.environ["APP_INSTANCE_ID"]`. Verificado 2026-07-02 leyendo `/proc/<gunicorn_pid>/environ`.

---

## API Keys — integración REST

Generadas 2026-07-01 vía `POST /api/method/frappe.core.doctype.user.user.generate_keys`.  
Frappe v16 genera hashes de 15 chars (comportamiento correcto de esta versión).

| Campo | Valor |
|---|---|
| Usuario | administrator |
| API Key | `7cf5a06e7e0744b` |
| API Secret | `243bf42f385b299` |
| Header completo | `Authorization: token 7cf5a06e7e0744b:243bf42f385b299` |

> **Nota:** El API Secret solo se devuelve en el momento de generación. Si se regeneran las keys, actualizar este archivo.

---

## Estado ERPNext post-TASK_045 (2026-07-01)

| Recurso | Estado |
|---|---|
| Empresa "Nextango" | Creada — ARS / Argentina / Manufacturing |
| Empresa "Hijos de Segundo Ratti SRL" | Creada por setup wizard — queda inactiva |
| Item `PANEL-DEC` | Creado — Panel Decorativo / grupo: Products |
| API Keys administrator | Generadas (ver sección API Keys arriba) |
| Bootstrap (grupos, depósitos, UoMs, cost centers) | **Completo** — ejecutado 2026-07-01 |
| Item `PANEL-DEC` grupo | Movido a "Paneles Decorativos" 2026-07-01 |

---

## Estructura /planos/ y datos operativos

- **`/home/costa/planos/generico/patrones/`** — 5 DXF históricos copiados 2026-07-02 (Aconcagua, Cosmos, Hexagonal, Subte, Philo_editado). `chmod o+rX`.
- **`nextango_planos_path` = `/home/costa/planos`** en site_config.json.
- **`daily_prices.json`** vive en `/home/costa/Nextango/Programas_hechos/Panel Decorativo/` (NO commiteado — es dato diario). La migración `migrate_materiales.run` lo lee de ahí. Para actualizar precios: reescribir ese archivo + `bench execute sistema_industrial.migrate.migrate_materiales.run --kwargs "{'overwrite': True}"`.
- **28 materiales** cargados con precio (SI Material Corte). Láser 60 $/s (SI Precios Globales).

## Túnel Cloudflare (acceso externo)

Levantado 2026-07-02 para acceso de Constantino desde fuera de la red:

| Campo | Valor |
|---|---|
| URL actual | https://farming-trans-shirt-surgeon.trycloudflare.com |
| Proceso | `cloudflared tunnel --url http://localhost:80` (nohup, pid en el server) |
| Log | `/home/costa/cloudflared_tunnel.log` |

> **Advertencias:** (1) Es un *quick tunnel* — la URL es efímera: si el proceso muere o el server se reinicia, hay que relanzarlo y **la URL cambia**. Para una URL estable hace falta una cuenta Cloudflare con túnel nombrado + systemd. (2) El proceso NO sobrevive reboots (no hay unit de systemd). Relanzar con:
> ```bash
> nohup cloudflared tunnel --url http://localhost:80 > /home/costa/cloudflared_tunnel.log 2>&1 &
> grep -o "https://.*trycloudflare.com" /home/costa/cloudflared_tunnel.log | head -1
> ```

## Notas de instalación

- **Python 3.14** requerido: Frappe v16 exige `Python>=3.14,<3.15`. 3.10 y 3.12 fallan.
- **`python3.14-tk` instalado (2026-07-02):** el motor de paneles importa `tkinter`. OJO: el paquete es `python3.14-tk` (deadsnakes, versión del bench), NO `python3-tk` (que instala para el 3.10 del sistema y no sirve).
- **Node.js 24** requerido: Frappe v16 exige `node>=24`. Node 18 falla en `yarn install`.
- `bench setup production` se hizo manualmente (conflicto de entornos Python/sudo). El sistema funciona igual.
- El archivo `/etc/sudoers.d/costa-nopasswd` (NOPASSWD temporal) fue eliminado al terminar la instalación.
- ~~`sistema_industrial` app NO instalada~~ **App instalada 2026-07-01** (Fase 0 Sprint 001):
  - Repo clonado en `/home/costa/Nextango` (rama `erpnext`, monorepo)
  - Symlink: `/home/costa/frappe-bench/apps/sistema_industrial → /home/costa/Nextango/apps/sistema_industrial`
  - `bench --site erp.local list-apps` → frappe 16.24.3, erpnext 16.25.0, sistema_industrial 0.1.0
  - 6 DocTypes migrados: SI Preset, SI Client Piece, SI Cut Piece, SI Cut Batch, SI Tango Price Cache, SI Linear Cut Request
  - Deploy de actualizaciones: `cd /home/costa/Nextango && git pull && cd /home/costa/frappe-bench && bench --site erp.local migrate && bench restart`
  - Backup pre-instalación: `20260701_220634-erp_local-*` en `sites/erp.local/private/backups/`
