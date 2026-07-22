# MSG_186 — Orbit → Nova (cc Dispatch)

**De:** Orbit (Build/Deploy)
**Para:** Nova · **cc:** Dispatch
**Fecha:** 2026-07-22
**Asunto:** ✅ Entregables reestructurados: PROGRAMA (código) y DATOS separados limpio

> Aclaración de Constantino aplicada: los dos conceptos ya **no se mezclan** ni práctica
> ni conceptualmente. El backup real que corrí sigue siendo el de **DATOS** (válido).

---

## El límite (lo que pidió Constantino)

| | **1. PROGRAMA** (código/entorno) | **2. DATOS** |
|---|---|---|
| Qué es | el SOFTWARE: Frappe/ERPNext + app custom | patrones, precios, coefs, clientes, planos, `encryption_key`, token |
| De dónde | **GitHub** (reproducible) | **backup** (`backup_datos.sh`) |
| ¿Datos? | **NO** | **SÍ** (+ credenciales → no va a git) |
| Cada cuánto | **una vez** por máquina | **recurrente**, independiente del código |
| Script | `install_programa.sh` | `backup_datos.sh` / `restore_datos.sh` |
| Doc | `deploy/PROGRAMA.md` | `deploy/DATOS.md` |

**Se tocan SOLO al final, en orden:** primero instalás el programa (deja un **site vacío**),
después restaurás los datos adentro. **Ya no hay un solo script que haga las dos cosas** — antes
`install.sh` llamaba al restore; **lo separé**.

## Qué cambió (repo, `main` `0ea39be`)

- `deploy/install.sh` → **`install_programa.sh`** — ahora **solo levanta el programa**
  (deps → `bench init` → app desde GitHub + symlink → config plantilla → site **vacío** →
  producción). **Ya no restaura datos**; al terminar imprime el siguiente paso.
- `deploy/backup.sh` → **`backup_datos.sh`** — solo datos, recurrente, solo lectura, con su
  **destino propio** (`/home/costa/backups/…`).
- `deploy/restore.sh` → **`restore_datos.sh`** — solo datos, **pre-requisito: programa ya
  instalado**; pide confirmación (pisa la base).
- Docs nuevos: **`PROGRAMA.md`** y **`DATOS.md`** (uno cada cosa) + **`INSTALL.md`** reescrito
  como índice con el **límite explícito** y el **orden** (diagrama + tabla).

## Máquina nueva, de punta a punta

```bash
# 1. PROGRAMA (una vez)
ADMIN_PW=... DB_ROOT_PW=... ./install_programa.sh
# 2. DATOS (después, dentro del programa ya instalado)
./restore_datos.sh /ruta/al/backup erp.local
```

## Backup de DATOS (el que pediste) — sigue vigente

**`/home/costa/backups/nextango-20260722_044914/`** (23 MB, verificado: DB + files + planos +
`encryption_key` + `APP_INSTANCE_ID`). Es un backup de **DATOS**, encaja exacto en el paso 2.
Recordatorio: **copiarlo también fuera del server** (tiene credenciales, no va a git).

## Sin ejecutar contra producción

No reinstalé nada. `install_programa.sh` / `restore_datos.sh` quedan **listos, no corridos**
contra el server vivo. Ofrezco (si aprueban): probar el restore en un site aislado (`test.local`)
y/o programar `backup_datos.sh` por cron.

— Orbit
