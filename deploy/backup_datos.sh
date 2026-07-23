#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# BACKUP DE DATOS — NexTango  (NO toca el código/programa)
# ═══════════════════════════════════════════════════════════════════════════
# Preserva SOLO los DATOS: base del site (patrones, precios, coefs, clientes),
# /home/costa/planos, archivos del site, y credenciales/encryption_key.
# Solo lectura de producción — seguro de correr. Corre de forma RECURRENTE,
# independiente del código. Genera un punto de restauración autoverificado.
#
# Destino de almacenamiento propio (separado del código):
#   por defecto  /home/costa/backups/nextango-<timestamp>/
#   -> RECOMENDADO: copiar cada backup TAMBIÉN fuera del server (otra máquina/disco).
#
# Uso:  ./backup_datos.sh              (server; guarda en /home/costa/backups/nextango-<ts>)
#       DEST=/ruta ./backup_datos.sh   (destino custom)
# ═══════════════════════════════════════════════════════════════════════════
set -euo pipefail

SITE=${SITE:-erp.local}
BENCH=${BENCH:-/home/costa/.local/bin/bench}
BENCH_DIR=${BENCH_DIR:-/home/costa/frappe-bench}
PLANOS=${PLANOS:-/home/costa/planos}
NEXUS_ENV=${NEXUS_ENV:-/etc/frappe-bench-nexus.env}
TS=$(date +%Y%m%d_%H%M%S)
DEST=${DEST:-/home/costa/backups/nextango-$TS}

mkdir -p "$DEST"
cd "$BENCH_DIR"

echo "[1/4] bench backup --with-files ..."
"$BENCH" --site "$SITE" backup --with-files

BK="$BENCH_DIR/sites/$SITE/private/backups"
PREFIX=$(ls -t "$BK"/*-database.sql.gz | head -1 | sed 's|.*/||; s|-database.sql.gz||')
echo "[2/4] copiando set $PREFIX -> $DEST"
cp "$BK/${PREFIX}"* "$DEST/"

echo "[3/4] planos + config critica"
tar czf "$DEST/planos.tar.gz" -C "$(dirname "$PLANOS")" "$(basename "$PLANOS")"
# nexus.env (token Tango): leer sin sudo si es posible (necesario en cron, que no tiene TTY);
# fallback a sudo para uso interactivo si el archivo fuera root-only.
if cp "$NEXUS_ENV" "$DEST/frappe-bench-nexus.env" 2>/dev/null; then
  :
else
  sudo cp "$NEXUS_ENV" "$DEST/frappe-bench-nexus.env"
  sudo chown "$(id -un):$(id -gn)" "$DEST/frappe-bench-nexus.env"
fi

echo "[4/4] verificación"
gzip -t "$DEST/${PREFIX}-database.sql.gz"
gzip -t "$DEST/planos.tar.gz"
for t in "$DEST"/*-files.tar; do tar -tf "$t" >/dev/null; done
python3 -c "import json,glob; d=json.load(open(glob.glob('$DEST/*site_config_backup.json')[0])); assert 'encryption_key' in d, 'FALTA encryption_key'; print('  encryption_key: OK')"
grep -q 'APP_INSTANCE_ID=' "$DEST/frappe-bench-nexus.env" && echo "  APP_INSTANCE_ID: OK"

echo "OK. Backup en: $DEST  ($(du -sh "$DEST" | cut -f1))"
echo "Contiene: database.sql.gz, files.tar, private-files.tar, site_config_backup.json (con encryption_key), planos.tar.gz, frappe-bench-nexus.env"
