#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# INSTALADOR DE PROGRAMA (código/entorno) — NexTango
# ═══════════════════════════════════════════════════════════════════════════
# Levanta EL SOFTWARE desde cero en una máquina NUEVA. NO trae ni restaura datos.
# Reproducible desde GitHub. Se corre UNA vez por máquina.
#
# Qué hace: bench init (Frappe/ERPNext) -> app custom desde GitHub + symlink ->
#           config desde plantilla -> site vacío -> modo producción.
# Qué NO hace: NO restaura patrones/precios/planos/credenciales.
#   -> Los DATOS se cargan DESPUÉS y por separado con restore_datos.sh (ver DATOS.md).
#
# Prerequisitos del SO (Ubuntu) — instalar ANTES (ver INSTALL.md §Prerequisitos):
#   MariaDB 10.6, Redis, Node 24 + yarn, Python 3.x, wkhtmltopdf, git, pipx
#
# Uso:
#   ADMIN_PW=... DB_ROOT_PW=... ./install_programa.sh
# ═══════════════════════════════════════════════════════════════════════════
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

echo "[4/6] crear site VACÍO + instalar apps (sin datos)"
bench new-site "$SITE" --admin-password "$ADMIN_PW" --mariadb-root-password "$DB_ROOT_PW"
bench --site "$SITE" install-app erpnext sistema_industrial

echo "[5/6] config desde plantilla"
echo "  >> Copiar .env.example a .env y completar (token Tango, API keys, TANGO_URL)."
echo "  >> Mapear 'server-t' (Tango) en /etc/hosts si no resuelve."

echo "[6/6] modo producción"
bench setup production "$(id -un)" || echo "  (setup production requiere sudo; ver INSTALL.md)"

echo ""
echo "═══════════════════════════════════════════════════════════════════════"
echo "PROGRAMA INSTALADO (site vacío, sin datos)."
echo ""
echo "SIGUIENTE PASO — cargar los DATOS (aparte):"
echo "  ./restore_datos.sh <dir-backup> $SITE      # ver DATOS.md"
echo "═══════════════════════════════════════════════════════════════════════"
