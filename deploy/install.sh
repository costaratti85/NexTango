#!/usr/bin/env bash
# Instalación de NexTango (ERPNext + app custom) en una máquina NUEVA.
# Deja el sistema levantado a partir de un backup hecho con backup.sh.
# NO correr contra el server de producción. Leer INSTALL.md antes.
#
# Prerequisitos del SO (Ubuntu) — instalar ANTES (ver INSTALL.md §1):
#   MariaDB 10.6, Redis, Node 24 + yarn, Python 3.x, wkhtmltopdf, git, pipx
#
# Uso:
#   BACKUP_DIR=/ruta/al/backup ADMIN_PW=... DB_ROOT_PW=... ./install.sh
set -euo pipefail

FRAPPE_BRANCH=${FRAPPE_BRANCH:-version-16}
REPO=${REPO:-https://github.com/costaratti85/NexTango.git}
REPO_BRANCH=${REPO_BRANCH:-erpnext}
SITE=${SITE:-erp.local}
BENCH_DIR=${BENCH_DIR:-$HOME/frappe-bench}
MONOREPO=${MONOREPO:-$HOME/Nextango}
: "${ADMIN_PW:?Definí ADMIN_PW}"
: "${DB_ROOT_PW:?Definí DB_ROOT_PW}"

echo "[1/6] bench + Frappe $FRAPPE_BRANCH"
command -v bench >/dev/null || pipx install frappe-bench
bench init "$BENCH_DIR" --frappe-branch "$FRAPPE_BRANCH"
cd "$BENCH_DIR"

echo "[2/6] ERPNext"
bench get-app erpnext --branch "$FRAPPE_BRANCH"

echo "[3/6] app custom (anidada en el monorepo) -> clon + symlink"
# La app NO es un repo Frappe estándar: vive en NexTango/apps/sistema_industrial
git clone -b "$REPO_BRANCH" "$REPO" "$MONOREPO"
ln -sfn "$MONOREPO/apps/sistema_industrial" "$BENCH_DIR/apps/sistema_industrial"
grep -qx sistema_industrial sites/apps.txt || echo sistema_industrial >> sites/apps.txt

echo "[4/6] crear site + instalar apps"
bench new-site "$SITE" --admin-password "$ADMIN_PW" --mariadb-root-password "$DB_ROOT_PW"
bench --site "$SITE" install-app erpnext sistema_industrial

echo "[5/6] restaurar datos (si hay backup)"
if [ -n "${BACKUP_DIR:-}" ]; then
  "$(dirname "$(readlink -f "$0")")/restore.sh" "$BACKUP_DIR" "$SITE"
else
  echo "  (sin BACKUP_DIR: site vacío; cargar planos/config a mano — ver INSTALL.md)"
fi

echo "[6/6] config + producción"
echo "  >> Completar credenciales: copiar .env.example a .env y llenar (token Tango, API keys, TANGO_URL)."
echo "  >> Mapear 'server-t' (Tango) en /etc/hosts si no resuelve."
bench setup production "$(id -un)" || echo "  (setup production requiere sudo; ver INSTALL.md §6)"

echo "OK. Verificá /app/panel-decorativo y una cotización con total > 0."
