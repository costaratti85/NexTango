#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# RESTORE DE DATOS — NexTango  (NO instala el código/programa)
# ═══════════════════════════════════════════════════════════════════════════
# Repone SOLO los DATOS (hechos con backup_datos.sh) DENTRO de un programa ya
# instalado: base del site + archivos + planos + encryption_key + token Tango.
# PRE-REQUISITO: el PROGRAMA ya tiene que estar instalado (ver install_programa.sh).
#
# ⚠️ DESTRUCTIVO sobre el site destino: PISA su base. NO correr contra un site
#    de producción sin querer. Para probar, usá un site aislado (ej. test.local).
# Uso:  ./restore_datos.sh <dir-backup> [site]
# ═══════════════════════════════════════════════════════════════════════════
set -euo pipefail

BACKUP_DIR=${1:?"Uso: restore_datos.sh <dir-backup> [site]"}
SITE=${2:-erp.local}
BENCH=${BENCH:-/home/costa/.local/bin/bench}
BENCH_DIR=${BENCH_DIR:-/home/costa/frappe-bench}
cd "$BENCH_DIR"

DB=$(ls "$BACKUP_DIR"/*-database.sql.gz | head -1)
PUB=$(ls "$BACKUP_DIR"/*-files.tar 2>/dev/null | grep -v private | head -1 || true)
PRIV=$(ls "$BACKUP_DIR"/*-private-files.tar | head -1)
CONF=$(ls "$BACKUP_DIR"/*-site_config_backup.json | head -1)

echo ">>> Restaurando en site '$SITE' desde $BACKUP_DIR"
read -rp "Esto PISA la base de '$SITE'. Escribí el nombre del site para confirmar: " ok
[ "$ok" = "$SITE" ] || { echo "Cancelado."; exit 1; }

"$BENCH" --site "$SITE" restore "$DB" \
  ${PUB:+--with-public-files "$PUB"} \
  --with-private-files "$PRIV"

echo ">>> Reponiendo encryption_key + config de Tango (CRÍTICO para leer datos encriptados)"
python3 - "$CONF" "sites/$SITE/site_config.json" <<'PY'
import json, sys
src = json.load(open(sys.argv[1]))
dst = json.load(open(sys.argv[2]))
for k in ("encryption_key", "tango_base_url", "tango_company"):
    if k in src:
        dst[k] = src[k]
json.dump(dst, open(sys.argv[2], "w"), indent=1)
print("  encryption_key + tango: repuestos")
PY

echo ">>> Planos + nexus.env (token Tango)"
tar xzf "$BACKUP_DIR/planos.tar.gz" -C "$HOME"
sudo cp "$BACKUP_DIR/frappe-bench-nexus.env" /etc/frappe-bench-nexus.env

echo ">>> migrate + build"
"$BENCH" --site "$SITE" migrate
"$BENCH" build --app sistema_industrial
"$BENCH" --site "$SITE" clear-cache

echo "OK. Restore completo en '$SITE'. Verificá: /app/panel-decorativo, y una cotización con total > 0."
