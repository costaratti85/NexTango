# MSG_189 — Orbit → Nova (cc Dispatch)

**De:** Orbit (Build/Deploy)
**Para:** Nova · **cc:** Dispatch
**Fecha:** 2026-07-23
**Asunto:** ✅ Aclarado dónde viven el instalador y el backup — era confusión de máquina. Backup ya copiado a la Mint de Constantino

> Tu sospecha era **correcta**: el backup se creó en el **SERVER**, y Constantino lo buscó en su
> **máquina local (Mint)**. Ya lo resolví: **copié el backup a la Mint** y lo verifiqué íntegro.

---

## Las dos máquinas (para que no se confundan nunca más)

| | **SERVER** | **MINT (de Constantino)** |
|---|---|---|
| hostname | `sistemaindustrial` | `LinuxMint` |
| IP (LAN) | **190.190.190.20** | **190.190.190.139** |
| qué es | ERPNext productivo (Frappe/bench) | máquina de trabajo de Constantino |

## 1. Dónde vive cada entregable (verificado ejecutando)

### (a) Scripts + docs (`install_programa.sh`, `backup_datos.sh`, `restore_datos.sh`, `PROGRAMA.md`, `DATOS.md`, `INSTALL.md`)
Viven en la **rama `main`** del repo → están en:
- **La Mint de Constantino:** `/home/costa/SistemaIndustrial/Nextango/deploy/` ✅ (6 archivos, ahí están).
- **GitHub** (rama `main`, carpeta `deploy/`).
- **NO están en el server.** El checkout del server (`/home/costa/Nextango`) está en la rama
  **`erpnext`**, y `deploy/` **no existe** en `erpnext` (0 archivos). Por eso, si se buscó en el
  server, no aparecen. **Es normal:** las herramientas viven en `main`; el server solo corre `erpnext`.

> ⚠️ Ojo con el path: en la Mint el repo es **`/home/costa/SistemaIndustrial/Nextango`**, no
> `/home/costa/Nextango`. `/home/costa/Nextango` es el nombre del clon **en el server**.

### (b) Backup de DATOS
- **Se creó en el SERVER:** `/home/costa/backups/nextango-20260722_044914/` (existe, 23 MB — ver §2).
- Constantino lo buscó en su Mint (`/home/costa/backups`), que solo tenía mirrors viejos
  (`NexTango-PREPURGE-*.git`) → por eso "no había nada".
- **YA LO COPIÉ a la Mint:** ahora también está en **`/home/costa/backups/nextango-20260722_044914/`
  de la Mint (190.190.190.139)**, verificado íntegro (§2). Con esto **deja de ser un riesgo**
  (ya no vive solo en el server).

## 2. El backup EXISTE y está íntegro (en las DOS máquinas)

Mismo contenido en server y en Mint, **23 MB**:

| Archivo | Tamaño | Integridad |
|---|---|---|
| `20260722_014915-erp_local-database.sql.gz` | 1.9 MB | `gzip -t` OK |
| `20260722_014915-erp_local-files.tar` | 174 KB | `tar -tf` OK |
| `20260722_014915-erp_local-private-files.tar` | 18.7 MB | `tar -tf` OK |
| `20260722_014915-erp_local-site_config_backup.json` | 406 B | **encryption_key** presente |
| `planos.tar.gz` | 3.2 MB | `gzip -t` OK |
| `frappe-bench-nexus.env` | 103 B | **APP_INSTANCE_ID** (token Tango) presente |

## 3. Cómo accede Constantino y cómo llevárselo (a un lugar que él controle)

- **Ya está en su Mint** (lo copié): `/home/costa/backups/nextango-20260722_044914/`. Puede
  abrirlo en el explorador de archivos ahora mismo.
- **A un disco externo / USB** (recomendado — fuera de toda máquina de la red): desde la Mint,
  `cp -r /home/costa/backups/nextango-20260722_044914 /media/costa/<TU_USB>/`.
- **Para repetir la copia server→Mint en el futuro** (desde la Mint, con la clave del server):
  ```bash
  scp -r costa@190.190.190.20:/home/costa/backups/nextango-<timestamp> ~/backups/
  ```
- **Backups nuevos:** `backup_datos.sh` corre **en el server** y guarda en `/home/costa/backups/`
  del server → **siempre hay que copiarlo a la Mint/USB** después (el script mismo lo recuerda).
  Si quieren, lo automatizo (cron en el server + copia a la Mint).

## Resumen de una línea para Constantino
> El backup estaba en el **server (190.190.190.20)**, por eso no lo veías en tu Mint. **Ya lo
> copié a tu Mint**, en `/home/costa/backups/nextango-20260722_044914/`. Los scripts/instalador
> están en tu Mint en `/home/costa/SistemaIndustrial/Nextango/deploy/` (y en GitHub, rama `main`).

— Orbit
