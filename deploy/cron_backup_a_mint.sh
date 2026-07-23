#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# BACKUP AUTOMÁTICO (cron) — corre EN EL SERVER
# ═══════════════════════════════════════════════════════════════════════════
# 1) corre backup_datos.sh (genera el backup de DATOS en el server)
# 2) copia a la Mint de Constantino por rsync (con catch-up: si algún día la
#    Mint estuvo apagada, la próxima corrida sube los que falten)
# 3) verifica la integridad de la copia EN la Mint (gzip/tar/credenciales)
# 4) reintenta la copia si falla, y deja todo registrado en un log
# 5) retención: conserva los últimos N en el server y en la Mint (no borra a ciegas)
#
# Es solo lectura de producción para el backup; la parte destructiva es SOLO
# borrar backups viejos más allá de N (retención autorizada por Constantino).
#
# Programación: ver crontab (instalado por instalar_cron_backup.sh). Frecuencia
# y retención son ajustables por variables (ver DATOS.md).
# ═══════════════════════════════════════════════════════════════════════════
set -uo pipefail
export PATH=/usr/local/bin:/usr/bin:/bin:/home/costa/.local/bin:$PATH   # cron trae PATH mínimo

TOOLS_DIR=$(dirname "$(readlink -f "$0")")
BACKUP_SCRIPT=${BACKUP_SCRIPT:-$TOOLS_DIR/backup_datos.sh}
SERVER_BACKUPS=${SERVER_BACKUPS:-/home/costa/backups}
MINT_USER=${MINT_USER:-costa}
MINT_HOST=${MINT_HOST:-190.190.190.139}
MINT_DIR=${MINT_DIR:-/home/costa/backups}
SSH_KEY=${SSH_KEY:-/home/costa/.ssh/id_backup}
LOG=${LOG:-/home/costa/backups/backup_cron.log}
RETENTION=${RETENTION:-10}          # últimos N backups (server y Mint); rango sugerido 7-14
RETRIES=${RETRIES:-3}

SSHOPT="-i $SSH_KEY -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=10"
log(){ echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

log "═══ inicio backup automático ═══"

# ── 1. backup ──────────────────────────────────────────────────────────────
if ! bash "$BACKUP_SCRIPT" >>"$LOG" 2>&1; then
  log "ERROR: backup_datos.sh FALLÓ. Abortando (no hay nada nuevo que copiar)."; exit 1
fi
LATEST=$(ls -dt "$SERVER_BACKUPS"/nextango-* 2>/dev/null | head -1)
[ -n "$LATEST" ] || { log "ERROR: no encuentro el backup recién creado."; exit 1; }
NAME=$(basename "$LATEST")
log "backup creado en server: $LATEST"

# ── 2. copia a la Mint (rsync con catch-up + reintentos) ────────────────────
ok=0
for try in $(seq 1 "$RETRIES"); do
  log "copia a Mint intento $try/$RETRIES → $MINT_USER@$MINT_HOST:$MINT_DIR/"
  # copia TODOS los nextango-* (rsync salta los ya presentes -> catch-up si la Mint estuvo apagada)
  if ssh $SSHOPT "$MINT_USER@$MINT_HOST" "mkdir -p '$MINT_DIR'" 2>>"$LOG" && \
     rsync -a -e "ssh $SSHOPT" "$SERVER_BACKUPS"/nextango-* \
       "$MINT_USER@$MINT_HOST:$MINT_DIR/" >>"$LOG" 2>&1; then
    ok=1; break
  fi
  log "  intento $try falló; reintento en 30s"; sleep 30
done
if [ "$ok" != 1 ]; then
  log "ERROR: no se pudo copiar a la Mint tras $RETRIES intentos."
  log "  El backup SÍ existe en el server ($LATEST). Copiar manual cuando la Mint esté disponible."
  exit 2
fi

# ── 3. verificación de integridad EN la Mint ────────────────────────────────
log "verificando integridad de la copia en la Mint ($NAME)…"
VERIFY=$(ssh $SSHOPT "$MINT_USER@$MINT_HOST" "bash -s '$MINT_DIR/$NAME'" <<'REMOTE'
D="$1"; err=0
gzip -t "$D"/*-database.sql.gz 2>/dev/null || { echo "FAIL database.sql.gz"; err=1; }
gzip -t "$D"/planos.tar.gz 2>/dev/null || { echo "FAIL planos.tar.gz"; err=1; }
for t in "$D"/*-files.tar; do tar -tf "$t" >/dev/null 2>&1 || { echo "FAIL $(basename "$t")"; err=1; }; done
grep -q '"encryption_key"' "$D"/*-site_config_backup.json 2>/dev/null || { echo "FAIL encryption_key"; err=1; }
grep -q 'APP_INSTANCE_ID=' "$D"/frappe-bench-nexus.env 2>/dev/null || { echo "FAIL APP_INSTANCE_ID"; err=1; }
[ "$err" = 0 ] && echo "OK"
REMOTE
)
if ! echo "$VERIFY" | grep -q '^OK$'; then
  log "ERROR: la copia en la Mint NO pasó la verificación: $VERIFY"; exit 3
fi
log "copia en la Mint OK e íntegra: $MINT_HOST:$MINT_DIR/$NAME"

# ── 4. retención (últimos N en server y Mint; nunca borra el más nuevo) ──────
log "retención: conservar últimos $RETENTION (server y Mint)"
ls -dt "$SERVER_BACKUPS"/nextango-* 2>/dev/null | tail -n +$((RETENTION+1)) | while read -r old; do
  log "  server: borro viejo $(basename "$old")"; rm -rf "$old"
done
ssh $SSHOPT "$MINT_USER@$MINT_HOST" \
  "ls -dt '$MINT_DIR'/nextango-* 2>/dev/null | tail -n +$((RETENTION+1)) | xargs -r rm -rf" \
  2>>"$LOG" && log "  Mint: retención aplicada" || log "  WARN: no pude aplicar retención en la Mint"

log "═══ fin OK ═══"
