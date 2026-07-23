# Backup / Restore de DATOS — NexTango

> **Esto es "los datos".** Preserva y restaura **solo los DATOS**, independiente del código.
> Corre de forma **recurrente**. **No instala ni toca el programa** → eso es [PROGRAMA.md](PROGRAMA.md).

Scripts: **`backup_datos.sh`** (recurrente, solo lectura) · **`restore_datos.sh`** (repone datos en un programa ya instalado).

---

## Qué son "los datos"

| Dato | De dónde sale |
|---|---|
| Base del site (patrones, precios, coefs láser, clientes, cotizaciones, usuarios/API keys) | `bench backup` → `.sql.gz` |
| Archivos del site (adjuntos, thumbnails) | `files.tar` + `private-files.tar` |
| **`encryption_key`** + `tango_base_url` + `tango_company` | `site_config_backup.json` |
| `/home/costa/planos` (DXF + calibración láser) | `planos.tar.gz` |
| **`APP_INSTANCE_ID`** (token de Tango) | `frappe-bench-nexus.env` |

> ⚠️ **`encryption_key`**: sin la MISMA clave, las contraseñas encriptadas de la base no se
> pueden leer. Por eso el backup de datos la incluye — y por eso **contiene credenciales**
> (no va a git; guardar el backup en lugar seguro).

## Backup (recurrente, seguro)

```bash
./backup_datos.sh              # guarda en /home/costa/backups/nextango-<timestamp>/
DEST=/otra/ruta ./backup_datos.sh
```

- **Solo lectura** de producción — seguro de correr en cualquier momento.
- Se **autoverifica** (integridad gzip/tar, `encryption_key` presente, `APP_INSTANCE_ID` presente).
- **Destino de almacenamiento propio** (separado del código). **RECOMENDADO: copiar cada
  backup también fuera del server** (otra máquina/disco) — por si lo que se pierde es el server.

### Backup automático (ANDANDO) — diario + copia sola a la Mint

Autorizado por Constantino. Un **cron en el server** corre todos los días y **copia solo** el
resultado a la Mint (no hay que acordarse de nada).

**Qué hace cada corrida** (`cron_backup_a_mint.sh`, en el server):
1. corre `backup_datos.sh` (genera el backup de datos en el server);
2. lo copia a la Mint por `rsync` — con **catch-up**: si algún día la Mint estuvo apagada, la
   próxima corrida sube los que falten;
3. **verifica la integridad EN la Mint** (gzip/tar + `encryption_key` + token);
4. **reintenta** la copia hasta 3 veces si falla; todo queda en un **log**;
5. **retención**: conserva los **últimos 10** en server y Mint (nunca borra el más nuevo).

| | Ruta | Máquina |
|---|---|---|
| Scripts del cron | `/home/costa/backup-tools/` | SERVER (190.190.190.20) |
| Backups (origen) | `/home/costa/backups/nextango-<ts>/` | SERVER |
| Backups (copia) | `/home/costa/backups/nextango-<ts>/` | **MINT** (190.190.190.139) |
| Log | `/home/costa/backups/backup_cron.log` | SERVER |

**Frecuencia:** diaria a las **13:00** (mediodía, la Mint suele estar encendida). **Es
ajustable.**

**Cómo cambiar la frecuencia / hora** (en el server):
```bash
HORA=9  MIN=30 /home/costa/backup-tools/instalar_cron_backup.sh   # cambia a 09:30 diario
/home/costa/backup-tools/instalar_cron_backup.sh --remove          # lo desactiva
```
Para otra periodicidad (ej. dos veces al día, o solo días hábiles) se edita la línea de cron
`# NEXTANGO_BACKUP_AUTO` con `crontab -e` en el server. Retención: variable `RETENTION`
(default 10; rango sugerido 7–14).

**Cómo verificar que anda:**
- En el server: `tail /home/costa/backups/backup_cron.log` → cada corrida termina en `═══ fin OK ═══`.
- En la Mint: `ls -dt /home/costa/backups/nextango-*` → debe aparecer el del día.
- Integridad manual: `gzip -t <dir>/*-database.sql.gz` y `tar -tf <dir>/*-files.tar`.

**Conectividad:** la copia usa una clave SSH dedicada `id_backup` (server → Mint), autorizada en
`~/.ssh/authorized_keys` de la Mint. Si la Mint cambia de IP, actualizar `MINT_HOST` en
`cron_backup_a_mint.sh`.

> **Nota:** existe además un auto-backup nativo de bench cada 6 h (solo base, sin archivos) que
> **queda en el server**. El backup automático de acá es el **completo** (base + archivos +
> planos + credenciales) y el único que **sale del server** a la Mint.

### También en el mismo cron: el "cerebro de los agentes"
El cron diario, además, **hala de la Mint** al server la parte durable de Claude Desktop/Cowork
(memorias CLI + Cowork, config MCP, sesiones Cowork como referencia) → `agentes-mint-<ts>/` en el
server (`backup_agentes_mint.sh`). Esto respalda a los agentes **fuera de la Mint**. Cómo se
recuperan (y por qué las sesiones no "reviven" 1:1): ver **`RECUPERACION_AGENTES.md`**.

## Restore (destructivo — pisa la base del site)

**Pre-requisito: el PROGRAMA ya tiene que estar instalado** (ver [PROGRAMA.md](PROGRAMA.md)).

```bash
./restore_datos.sh <dir-backup> [site]
```

- **Pide confirmación** (escribir el nombre del site) porque **pisa la base**.
- Repone: base + archivos + `encryption_key`/Tango en `site_config.json` + planos + token, y
  corre `migrate` + `build` + `clear-cache`.
- Para **probar**, usar un site **aislado** (ej. `test.local`) — **nunca** `erp.local` de una.

## Verificación post-restore

- `supervisorctl status` → servicios arriba.
- `/app/panel-decorativo` carga; una **cotización da total > 0** (no $0).
- Un patrón de la galería genera su DXF.
