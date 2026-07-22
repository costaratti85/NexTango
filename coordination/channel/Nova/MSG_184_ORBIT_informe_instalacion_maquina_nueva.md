# MSG_184 — Orbit → Nova (cc Dispatch)

**De:** Orbit (Build/Deploy)
**Para:** Nova · **cc:** Dispatch
**Fecha:** 2026-07-22
**Asunto:** Informe: instalar nuestro ERPNext en una máquina nueva — estado real (para Constantino)

> Informe verificado contra el server actual. **No ejecuté nada en ninguna máquina nueva.**

---

## Respuesta corta para Constantino

**Hoy NO hay un instalador de un click.** El sistema del server se armó **a mano**. Lo que tenemos automatizado es *actualizar* el sistema ya instalado (bajar cambios de GitHub y reiniciar), **no** *crearlo de cero* en una PC nueva. Se puede hacer en una máquina nueva, pero hoy son varios pasos manuales. **Sí conviene armar un script para que sea repetible** — lo recomiendo abajo.

---

## 1. ¿Hay instalador repetible, o es manual?

**Es MANUAL.** El único script del repo (`tools/bootstrap_repo.sh`) solo inicializa el repositorio git y corre tests — **no instala Frappe, ni ERPNext, ni crea el site**. No hay Dockerfile, ni `docker-compose`, ni script de instalación end-to-end. GitHub sirve para traer **el código**, pero no la base de datos ni la configuración.

## 2. Procedimiento concreto para una máquina nueva (lo que hay que hacer hoy)

1. **Sistema operativo + dependencias:** Ubuntu, y instalar MariaDB, Redis, Node 24 + yarn, Python, wkhtmltopdf, git. (misma familia de versiones que abajo).
2. **Instalar bench:** `pipx install frappe-bench`.
3. **Crear el bench con Frappe 16:** `bench init frappe-bench --frappe-branch version-16`.
4. **Traer ERPNext:** `bench get-app erpnext --branch version-16`.
5. **Traer nuestra app custom — OJO, acá está la parte no-estándar:** nuestra app **no** es un repo de app Frappe normal. Vive **anidada** dentro del monorepo `NexTango` (junto con `Programas_hechos/`, `coordination/`, la rama `main`, etc.). El motor de paneles standalone está en `Programas_hechos/Panel Decorativo/`. Entonces `bench get-app` **no alcanza**: hay que **clonar `github.com/costaratti85/NexTango` (rama `erpnext`)** y **hacer un symlink** `frappe-bench/apps/sistema_industrial → NexTango/apps/sistema_industrial` (exactamente como está en el server hoy).
6. **Crear el site:** o bien `bench new-site erp.local` (site vacío) **o**, lo recomendado, **restaurar el backup** de la base actual (así vienen patrones, precios, clientes, config).
7. **Instalar apps en el site:** `bench --site erp.local install-app erpnext sistema_industrial` (si es site nuevo).
8. **Config** (ver §3).
9. **Datos en disco** (planos, archivos del site) — ver §3.
10. **Producción:** `bench setup production` (arma nginx + supervisor) o `bench start` para dev.

## 3. Qué migrar SÍ o SÍ / qué NO

**SÍ (sin esto el sistema está vacío o roto):**
- **Base de datos del site (~61 MB):** patrones (SI Patron), **precios** (SI Precios Globales, coeficientes láser en SI Material Corte), clientes, cotizaciones, config. Se migra con `bench backup` → `bench restore`.
- **Carpeta `/home/costa/planos` (~41 MB):** DXF de patrones y calibración láser. **Las rutas están congeladas en la base** (SI Patron Version) → deben ir al **mismo path** `/home/costa/planos`.
- **Archivos del site** (`sites/erp.local/private` ~32 MB + `public` ~172 KB): thumbnails y adjuntos.
- **Configuración/credenciales:**
  - `/etc/frappe-bench-nexus.env` → **`APP_INSTANCE_ID`** (el token de Tango; sin él el sync no anda).
  - `.env` del proyecto → **API keys de ERPNext** (Administrator) y **`TANGO_URL`**.
  - `site_config.json` → `tango_base_url` (`http://server-t:17000`), `tango_company` (25), y **`encryption_key`** (⚠️ crítica: sin la MISMA clave, las contraseñas guardadas encriptadas en la base no se pueden leer).

**NO hace falta migrar (se regenera):**
- El código (viene de GitHub), los entornos Python (`env`/`.venv`), los assets compilados (`bench build`), los datos de Redis (efímeros).

## 4. Dependencias y riesgos (versiones reales de hoy)

| Componente | Versión en producción |
|---|---|
| bench | 5.31.0 |
| Frappe | 16.24.3 |
| ERPNext | 16.25.0 |
| Python (bench) | **3.14.6** |
| Node / yarn | **24.18.0** / 1.22.22 |
| MariaDB | 10.6.23 |
| Redis | 6.0.16 |

**Riesgos concretos:**
- **Versiones nuevas y sensibles:** Python 3.14 y Node 24 son muy recientes; en otra máquina hay que instalar **esas** versiones o algo compatible, o el `bench build`/las libs pueden fallar.
- **La estructura anidada** (app custom dentro del monorepo + symlink + motor en `Programas_hechos/`) es no-estándar y es fácil de armar mal. La copia canónica es `/home/costa/Nextango`.
- **`server-t` (Tango)** debe ser alcanzable desde la máquina nueva (misma LAN, o `/etc/hosts` apuntando a la IP).
- **Credenciales:** token de Tango, API keys de ERPNext, `db_password` y `encryption_key`. Si no se llevan, el sync y los datos encriptados se rompen.
- **Nada de esto está documentado paso a paso hoy** — el conocimiento está en la cabeza del equipo y en estos mensajes.

## 5. Recomendación honesta

**Sí, conviene armar un instalador reproducible.** Con lo que ya sabemos del server, un script + un README dejarían la instalación en pocos pasos. Esbozo mínimo:

- **`install.sh`** (idempotente): instala dependencias del SO → `bench init` (Frappe 16) → `get-app erpnext` → clona `NexTango` + symlink de la app → crea/restaura el site → `install-app` → aplica la config desde una plantilla → `setup production`.
- **`backup.sh` / `restore.sh`**: envuelven `bench backup` (base + archivos) y `bench restore`, más `rsync` de `/home/costa/planos`.
- **`config.env.example`** (ya existe un `.env.example`): lista las variables a completar (token Tango, API keys, `TANGO_URL`, paths), sin valores reales.
- **`INSTALL.md`**: el paso a paso, con las versiones fijadas.
- *(Opcional, más robusto pero más trabajo: contenedores con `frappe_docker`.)*

**Costo estimado:** un script semi-automático + README resuelven ~90% en 1–2 días de trabajo; lo delicado (backup/restore de base + planos + credenciales) es lo que hay que dejar sólido. Si Constantino quiere, lo puedo armar (es territorio Build/Deploy).

---

Es un informe — no ejecuté nada. Quedo para armar el instalador si lo aprueban.

— Orbit
