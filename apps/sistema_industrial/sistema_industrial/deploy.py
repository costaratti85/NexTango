"""Utilidades de deploy.

bump_page_cache — invalidar la caché client-side de las Desk Pages.
ensure_home_shortcut_panel_decorativo — shortcut de un clic en el Workspace "Home".

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
