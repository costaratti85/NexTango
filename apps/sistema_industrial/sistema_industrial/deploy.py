"""Utilidades de deploy.

bump_page_cache — invalidar la caché client-side de las Desk Pages.
ensure_home_shortcut_panel_decorativo — shortcut de un clic en el Workspace "Home".
generate_version_stamp — window.SI_VERSION para las 6 páginas (VEGA_MOSTRAR_VERSION_EN_PAGINAS).

Contexto (bug "página en blanco", 2026-07-02): Frappe cachea el script de
cada Desk Page en localStorage (`_page:<name>`, pageview.js) y solo lo purga
cuando cambia el `modified` del doc Page (desk.js compara boot.page_info
contra la copia local). Deployar cambios de .js/.html de una page NO toca el
doc Page, así que los browsers que ya la visitaron quedan con el script viejo
para siempre.

Ejecutar después de todo deploy que cambie .js/.html de páginas:

    bench --site erp.local execute sistema_industrial.deploy.bump_page_cache

Opcionalmente con nombres puntuales:

    bench --site erp.local execute sistema_industrial.deploy.bump_page_cache \
        --args "['panel-decorativo']"
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from subprocess import check_output

import frappe


def bump_page_cache(*names):
    """Bumpea `modified` de las Pages del módulo para purgar la caché localStorage.

    Sin argumentos: todas las Pages del módulo Sistema Industrial.
    """
    if not names:
        names = [
            p.name
            for p in frappe.get_all("Page", filters={"module": "Sistema Industrial"})
        ]
    if not names:
        return {"bumped": []}

    frappe.db.sql(
        "update tabPage set modified=NOW(6) where name in %(names)s",
        {"names": tuple(names)},
    )
    frappe.db.commit()
    frappe.clear_cache()
    return {"bumped": list(names)}


def ensure_home_shortcut_panel_decorativo():
    """Agrega un shortcut a Panel Decorativo en el Workspace "Home" nativo de
    Frappe (MSG_022 de Nova) — el que carga apenas se entra al Desk, sin
    depender de que el usuario navegue primero al Workspace "Sistema
    Industrial". Idempotente: no duplica si ya existe.

    Ejecutar:
        bench --site erp.local execute \
            sistema_industrial.deploy.ensure_home_shortcut_panel_decorativo
    """
    label = "Panel Decorativo"
    doc = frappe.get_doc("Workspace", "Home")
    if any(s.label == label for s in doc.shortcuts):
        return {"changed": False}

    doc.append(
        "shortcuts",
        {"label": label, "link_to": "panel-decorativo", "type": "Page", "color": "Blue"},
    )

    content = json.loads(doc.content or "[]")
    insert_at = 0
    for i, block in enumerate(content):
        if block.get("type") == "header":
            insert_at = i + 1
            break
    content.insert(
        insert_at,
        {"id": "siPanelDecHome", "type": "shortcut", "data": {"shortcut_name": label, "col": 3}},
    )
    doc.content = json.dumps(content)
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {"changed": True}


def generate_version_stamp():
    """Genera public/js/version_stamp.js con window.SI_VERSION = {commit, deployed_at}.

    VEGA_MOSTRAR_VERSION_EN_PAGINAS (MSG_035 de Nova). Reimplementado acá en
    vez de usar tools/generate_version_stamp.py de Forge (MSG_061) porque ese
    script: (1) nunca se commiteó ni pusheó — solo existía sin trackear en el
    worktree local de main, no en el servidor; (2) escribía a
    <repo_root>/public/js/, una ruta que Frappe no sirve — el árbol real que
    bench build escanea es apps/sistema_industrial/sistema_industrial/public/;
    (3) corría contra la rama main, que tiene un commit de sistema_industrial
    completamente distinto y desincronizado del que realmente se sirve
    (erpnext) — el hash mostrado hubiera sido el equivocado.

    Corre DENTRO de la rama erpnext (deploy.py vive en
    apps/sistema_industrial/sistema_industrial/, git encuentra la raíz del
    repo hacia arriba solo), así que el commit que capturamos es siempre el
    que realmente está deployado.

    Ejecutar ANTES de bench build (el asset se sirve desde ahí):

        bench --site erp.local execute sistema_industrial.deploy.generate_version_stamp
    """
    app_dir = Path(__file__).parent
    commit = check_output(
        ["git", "rev-parse", "--short", "HEAD"], cwd=str(app_dir)
    ).decode().strip()
    deployed_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    stamp_file = app_dir / "public" / "js" / "version_stamp.js"
    stamp_file.parent.mkdir(parents=True, exist_ok=True)
    stamp_file.write_text(
        "window.SI_VERSION = " + json.dumps({"commit": commit, "deployed_at": deployed_at}) + ";\n"
    )
    return {"commit": commit, "deployed_at": deployed_at, "path": str(stamp_file)}
