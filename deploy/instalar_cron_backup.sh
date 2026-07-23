#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# Instala/actualiza el cron del backup automático EN EL SERVER (idempotente).
# Programa cron_backup_a_mint.sh (backup + copia a la Mint + verificación).
#
# Uso (en el server):  ./instalar_cron_backup.sh
#   HORA=13 MIN=0 ./instalar_cron_backup.sh     # cambiar la hora (default 13:00 diario)
# Para quitarlo:       ./instalar_cron_backup.sh --remove
# ═══════════════════════════════════════════════════════════════════════════
set -euo pipefail

TOOLS_DIR=$(dirname "$(readlink -f "$0")")
WRAPPER="$TOOLS_DIR/cron_backup_a_mint.sh"
HORA=${HORA:-13}       # 13:00 = mediodía/tarde, la Mint suele estar encendida
MIN=${MIN:-0}
TAG="# NEXTANGO_BACKUP_AUTO"
LINE="$MIN $HORA * * * $WRAPPER >> /home/costa/backups/backup_cron.log 2>&1 $TAG"

CUR=$(crontab -l 2>/dev/null || true)
NEW=$(echo "$CUR" | grep -vF "$TAG" || true)

if [ "${1:-}" = "--remove" ]; then
  printf '%s\n' "$NEW" | crontab -
  echo "cron del backup ELIMINADO."; exit 0
fi

printf '%s\n%s\n' "$NEW" "$LINE" | sed '/^$/d' | crontab -
echo "cron instalado (diario ${HORA}:$(printf '%02d' "$MIN")):"
crontab -l | grep -F "$TAG"
