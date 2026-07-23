#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# BACKUP DEL "CEREBRO DE LOS AGENTES" (vive en la MINT) — corre EN EL SERVER
# ═══════════════════════════════════════════════════════════════════════════
# Hala (pull) por rsync desde la Mint, con la clave id_backup, la parte DURABLE
# de Claude Desktop/Cowork. Read-only sobre la Mint. Excluye caches regenerables.
#
# Qué respalda (lo que NO está en GitHub y se perdería si muere la Mint):
#   - sesiones de Cowork + memorias de Cowork (~/.config/Claude/local-agent-mode-sessions/,
#     que adentro trae agent/memory/MEMORY.md + memorias)
#   - config de la app + MCP (claude_desktop_config.json, config.json)
#   - memorias CLI por proyecto (~/.claude/projects/<proj>/memory/ con MEMORY.md)
# Lo que NO respalda (a propósito): Cache/, Code Cache/, claude-code/, GPUCache/
#   (regenerables) y los transcripts pesados del CLI (referencia, no "reviven" solos).
#
# OJO: esto NO revive los agentes 1:1 en una máquina nueva (ver RECUPERACION_AGENTES.md).
#      Es el material para RECONSTITUIRLOS: memorias + config + sesiones como referencia.
# ═══════════════════════════════════════════════════════════════════════════
set -uo pipefail
export PATH=/usr/local/bin:/usr/bin:/bin:$PATH

MINT_USER=${MINT_USER:-costa}
MINT_HOST=${MINT_HOST:-190.190.190.139}
SSH_KEY=${SSH_KEY:-/home/costa/.ssh/id_backup}
DEST_ROOT=${DEST_ROOT:-/home/costa/backups}
LOG=${LOG:-/home/costa/backups/backup_cron.log}
RETENTION=${RETENTION:-10}
TS=$(date +%Y%m%d_%H%M%S)
DEST="$DEST_ROOT/agentes-mint-$TS"
SSHOPT="-i $SSH_KEY -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=10"
log(){ echo "[$(date '+%F %T')] $*" | tee -a "$LOG"; }

mkdir -p "$DEST/config-Claude" "$DEST/claude-projects-memory"
log "═══ backup cerebro-agentes (Mint→server) $TS ═══"

ok=1
# 1) sesiones Cowork + memorias Cowork (incluye agent/memory/)
rsync -a -e "ssh $SSHOPT" \
  "$MINT_USER@$MINT_HOST:.config/Claude/local-agent-mode-sessions" \
  "$DEST/config-Claude/" >>"$LOG" 2>&1 || { log "WARN: fallo rsync local-agent-mode-sessions"; ok=0; }

# 2) config app + MCP (best-effort)
for f in claude_desktop_config.json config.json cowork-enabled-cli-ops.json; do
  rsync -a -e "ssh $SSHOPT" "$MINT_USER@$MINT_HOST:.config/Claude/$f" "$DEST/config-Claude/" >>"$LOG" 2>&1 || true
done

# 3) memorias CLI por proyecto (solo carpetas memory/, no los transcripts pesados)
rsync -a -e "ssh $SSHOPT" --prune-empty-dirs \
  --include='*/' --include='memory/***' --exclude='*' \
  "$MINT_USER@$MINT_HOST:.claude/projects/" \
  "$DEST/claude-projects-memory/" >>"$LOG" 2>&1 || { log "WARN: fallo rsync memorias CLI"; ok=0; }

# 4) verificación mínima (que aterrizaron las memorias)
COWORK_MEM=$(find "$DEST/config-Claude/local-agent-mode-sessions" -path '*/agent/memory/MEMORY.md' 2>/dev/null | wc -l)
CLI_MEM=$(find "$DEST/claude-projects-memory" -name 'MEMORY.md' 2>/dev/null | wc -l)
SESS_N=$(find "$DEST/config-Claude/local-agent-mode-sessions" -maxdepth 1 -mindepth 1 -type d 2>/dev/null | wc -l)
log "verif: sesiones Cowork=$SESS_N  MEMORY.md(Cowork)=$COWORK_MEM  MEMORY.md(CLI)=$CLI_MEM  tamaño=$(du -sh "$DEST" 2>/dev/null | cut -f1)"
if [ "$CLI_MEM" -lt 1 ] && [ "$COWORK_MEM" -lt 1 ]; then
  log "ERROR: no se respaldó ninguna MEMORY.md — revisar conectividad/rutas."; ok=0
fi

# 5) retención (últimos N snapshots agentes-mint-*)
ls -dt "$DEST_ROOT"/agentes-mint-* 2>/dev/null | tail -n +$((RETENTION+1)) | while read -r old; do
  log "  retención: borro viejo $(basename "$old")"; rm -rf "$old"
done

[ "$ok" = 1 ] && log "═══ backup cerebro-agentes OK: $DEST ═══" || log "═══ backup cerebro-agentes con WARNINGS (ver log) ═══"
exit 0
