# Instalador de PROGRAMA (código/entorno) — NexTango

> **Esto es "el programa".** Levanta el SOFTWARE desde cero. **No contiene datos.**
> Es reproducible desde GitHub y se corre **una vez por máquina**.
> Los DATOS se cargan **después y por separado** → ver [DATOS.md](DATOS.md).

Script: **`install_programa.sh`**

---

## Qué instala

deps del SO (MariaDB/Redis/Node/Python) → `bench init` (Frappe/ERPNext) → app custom
desde GitHub + symlink → config desde plantilla → **site vacío** → modo producción.

## 1. Prerequisitos del SO (Ubuntu) — instalar ANTES

Versiones que hoy corre producción (usar estas o compatibles):

| Componente | Versión |
|---|---|
| Frappe / ERPNext | **version-16** (16.24.x / 16.25.x) |
| bench | 5.31 |
| Python (bench env) | 3.14 |
| Node + yarn | **24.x** + 1.22 |
| MariaDB | 10.6 |
| Redis | 6.x |

Instalar: `mariadb-server` (con `mysql_secure_installation` y `utf8mb4`), `redis-server`,
Node 24 (nvm/nodesource) + `npm i -g yarn`, `python3` + `python3-dev`, `wkhtmltopdf`
(qt patched), `git`, `pipx`.

> ⚠️ Python 3.14 y Node 24 son recientes. Instalá **esas** versiones (o compatibles), o el
> `bench build` / algunas libs pueden fallar.

## 2. Correr el instalador

```bash
ADMIN_PW='<clave admin nueva>' \
DB_ROOT_PW='<root de mariadb>' \
./install_programa.sh
```

Hace: `bench init` (Frappe 16) → `get-app erpnext` → **clona el monorepo `NexTango` y
symlinkea la app** (`apps/sistema_industrial` → `NexTango/apps/sistema_industrial`, porque la
app está **anidada**, no es un repo Frappe estándar) → crea el site **vacío** → `install-app`
→ `bench setup production`.

## 3. Config manual que queda por completar

- Copiar `.env.example` → `.env` y llenar: `ERPNEXT_BASE_URL`, `ERPNEXT_API_KEY/SECRET`,
  `TANGO_URL`, `APP_INSTANCE_ID`.
- Que **`server-t` (Tango)** resuelva desde la máquina nueva: agregar su IP de la LAN a
  `/etc/hosts`, o usar la IP directa en `TANGO_URL`.

## 4. Qué NO trae este instalador (a propósito)

- **Nada de datos**: ni patrones, ni precios, ni planos, ni clientes, ni la `encryption_key`.
  Eso es responsabilidad de [DATOS.md](DATOS.md) y se hace **al final**.
- Tampoco hace falta llevar código (viene de GitHub), entornos Python, assets compilados
  (`bench build`) ni datos de Redis (efímeros): se regeneran solos.

## 5. Siguiente paso (obligatorio para tener datos)

El site queda **vacío**. Para cargar los datos reales:

```bash
./restore_datos.sh <dir-backup> erp.local      # ver DATOS.md
```
