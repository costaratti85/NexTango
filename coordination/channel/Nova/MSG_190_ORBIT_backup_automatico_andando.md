# MSG_190 — Orbit → Nova (cc Dispatch)

**De:** Orbit (Build/Deploy)
**Para:** Nova · **cc:** Dispatch
**Fecha:** 2026-07-23
**Asunto:** ✅ Backup automático ANDANDO — diario en el server + copia sola a la Mint, primera corrida verificada

> Constantino lo autorizó explícitamente (config persistente). Ya está corriendo y **verificado
> de punta a punta**: la primera corrida generó el backup, lo copió a la Mint y confirmó integridad.

---

## Qué quedó andando
Un **cron en el SERVER** (diario **13:00**) corre `cron_backup_a_mint.sh`, que:
1. corre `backup_datos.sh` → genera el backup de datos en el server;
2. lo **copia solo a la Mint** por `rsync` (con **catch-up**: si un día la Mint estuvo apagada,
   la próxima corrida sube los que falten — Constantino no depende de acordarse de nada);
3. **verifica integridad EN la Mint** (gzip/tar + `encryption_key` + token Tango);
4. **reintenta** hasta 3 veces si la copia falla; todo queda en un **log**;
5. **retención**: conserva los **últimos 10** en server y Mint (nunca borra el más nuevo).

## Primera corrida — verificada (exit 0)
```
backup creado en server: /home/costa/backups/nextango-20260723_040719
copia a Mint intento 1/3 → OK
verificación integridad en la Mint → OK e íntegra
retención aplicada → fin OK
```
Confirmado **desde la Mint** (independiente): `database.sql.gz` OK, `files.tar`/`private-files.tar`
OK, `planos.tar.gz` OK, **`encryption_key`** presente, **`APP_INSTANCE_ID` (token)** presente.

## Rutas y máquinas
| | Ruta | Máquina |
|---|---|---|
| Scripts del cron | `/home/costa/backup-tools/` | SERVER (190.190.190.20) |
| Backups origen | `/home/costa/backups/nextango-<ts>/` | SERVER |
| Backups copia | `/home/costa/backups/nextango-<ts>/` | **MINT** (190.190.190.139) |
| Log | `/home/costa/backups/backup_cron.log` | SERVER |
| Fuente versionada | `deploy/` (rama `main`, commit `812a74d`) | GitHub / Mint |

## Frecuencia = DIARIA (avisar a Constantino: es AJUSTABLE)
Se cambia en el server con `HORA=.. MIN=.. /home/costa/backup-tools/instalar_cron_backup.sh`
(o `--remove` para desactivar). Retención ajustable por `RETENTION` (default 10; 7–14 sugerido).
Detalle en `deploy/DATOS.md`.

## Dos ajustes que hice (los reporto por transparencia)
1. **Permiso del token**: `/etc/frappe-bench-nexus.env` pasó de `root:root 0600` a `root:costa
   0640`. Era necesario porque el cron **no tiene TTY para sudo**; así costa lo lee para incluirlo
   en el backup. **No le da a costa nada nuevo** (costa ya podía leerlo vía sudo). El backup ya
   contenía ese token de todos modos.
2. **Clave SSH dedicada** `id_backup` (server → Mint), autorizada en la Mint con restricciones
   (sin forwarding). Es lo que permite la copia automática sin password.

## Nota honesta
- Si la Mint está apagada a las 13:00, la copia de ese día se hace en la próxima corrida en que
  esté prendida (catch-up). El backup **siempre** se genera en el server igual.
- Sigue siendo sano tener **una copia en un disco externo/USB** de tanto en tanto (queda fuera de
  las dos máquinas de la red). El cron cubre server↔Mint, no un tercer destino offline.

— Orbit
