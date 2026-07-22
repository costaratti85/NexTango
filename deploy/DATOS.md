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

### (Opcional) programarlo

Se puede dejar corriendo solo (cron). Hoy es **manual** a propósito; pedir si se quiere automatizar.

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
