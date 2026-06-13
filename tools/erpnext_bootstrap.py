#!/usr/bin/env python3
"""
Bootstrap ERPNext with the minimum structure needed for this metalworking company.

Creates via the Frappe REST API:
  - Item Groups (hierarchy: root → family → group)
  - Warehouses
  - UoMs (units of measure)
  - Cost Centers

Safe to re-run: each resource is only created if it doesn't already exist (409 = skip).

Usage:
    python tools/erpnext_bootstrap.py
    python tools/erpnext_bootstrap.py --url http://erpnext.local:8080 --user administrator --password admin
    python tools/erpnext_bootstrap.py --dry-run   # print what would be created, no HTTP calls
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

# -----------------------------------------------------------------------
# Defaults
# -----------------------------------------------------------------------
DEFAULT_URL = "http://erpnext.local:8080"
DEFAULT_USER = "administrator"
DEFAULT_PASSWORD = "admin"
DEFAULT_COMPANY = "Nextango"        # must match the company created in ERPNext
DEFAULT_COMPANY_ABR = "NXT"


# -----------------------------------------------------------------------
# Structure definition
# -----------------------------------------------------------------------

ITEM_GROUPS = [
    # (name, parent)
    # Level 1 — families
    ("Materiales", "All Item Groups"),
    ("Servicios", "All Item Groups"),
    ("Piezas", "All Item Groups"),
    ("Insumos", "All Item Groups"),
    # Level 2 — groups under Materiales
    ("Chapas y Flejes", "Materiales"),
    ("Tubos y Perfiles", "Materiales"),
    ("Barras", "Materiales"),
    # Level 2 — groups under Servicios
    ("Corte Láser", "Servicios"),
    ("Corte Plasma", "Servicios"),
    ("Oxicorte", "Servicios"),
    ("Plegado", "Servicios"),
    ("Grabado", "Servicios"),
    # Level 2 — groups under Piezas
    ("Paneles Decorativos", "Piezas"),
    ("Piezas Cortadas", "Piezas"),
    ("Piezas Plegadas", "Piezas"),
    # Level 2 — Insumos
    ("Ferretería", "Insumos"),
    ("Consumibles", "Insumos"),
]

WAREHOUSES = [
    # (warehouse_name, parent_warehouse)  parent=None → company default root
    ("Almacén Principal - NXT", None),
    ("Materia Prima - NXT", "Almacén Principal - NXT"),
    ("Producción WIP - NXT", "Almacén Principal - NXT"),
    ("Producto Terminado - NXT", "Almacén Principal - NXT"),
    ("Merma y Retazos - NXT", "Almacén Principal - NXT"),
    ("Devoluciones - NXT", None),
]

UOMS = [
    # name
    "kg",
    "g",
    "m",
    "m2",
    "m3",
    "mm",
    "hora",
    "minuto",
    "unidad",
    "pieza",
    "lote",
    "plancha",
]

COST_CENTERS = [
    # (name, parent)
    ("Producción - NXT", f"{DEFAULT_COMPANY} - {DEFAULT_COMPANY_ABR}"),
    ("Corte Láser - NXT", "Producción - NXT"),
    ("Corte Plasma - NXT", "Producción - NXT"),
    ("Oxicorte - NXT", "Producción - NXT"),
    ("Plegado - NXT", "Producción - NXT"),
    ("Administración - NXT", f"{DEFAULT_COMPANY} - {DEFAULT_COMPANY_ABR}"),
]


# -----------------------------------------------------------------------
# REST client helpers
# -----------------------------------------------------------------------

@dataclass
class ERPNextClient:
    base_url: str
    user: str
    password: str
    dry_run: bool = False
    _sid: str = ""

    def login(self) -> None:
        if self.dry_run:
            print("[dry-run] Would login as", self.user)
            return
        data = urllib.parse.urlencode({
            "usr": self.user,
            "pwd": self.password,
        }).encode()
        req = urllib.request.Request(
            f"{self.base_url}/api/method/login",
            data=data,
            method="POST",
        )
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        with urllib.request.urlopen(req, timeout=10) as resp:
            # Extract session cookie
            cookie_header = resp.headers.get("Set-Cookie", "")
            for part in cookie_header.split(";"):
                part = part.strip()
                if part.startswith("sid="):
                    self._sid = part.split("=", 1)[1]
                    break
        print(f"Logged in to {self.base_url}")

    def _request(self, method: str, path: str, body: dict | None = None) -> dict | None:
        url = f"{self.base_url}{path}"
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")
        if self._sid:
            req.add_header("Cookie", f"sid={self._sid}")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code == 409:
                return {"__already_exists": True}
            body_text = e.read().decode("utf-8", errors="replace")
            print(f"  HTTP {e.code} {method} {path}: {body_text[:200]}", file=sys.stderr)
            return None

    def exists(self, doctype: str, name: str) -> bool:
        result = self._request("GET", f"/api/resource/{urllib.parse.quote(doctype)}/{urllib.parse.quote(name)}")
        return result is not None and "__already_exists" not in result

    def create(self, doctype: str, doc: dict) -> bool:
        name = doc.get("name") or doc.get("item_group_name") or doc.get("warehouse_name") or doc.get("uom_name") or ""
        if self.dry_run:
            print(f"  [dry-run] Would create {doctype}: {name}")
            return True
        result = self._request("POST", f"/api/resource/{urllib.parse.quote(doctype)}", doc)
        if result is None:
            print(f"  FAILED: {doctype} '{name}'", file=sys.stderr)
            return False
        if result.get("__already_exists"):
            print(f"  skip (exists): {doctype} '{name}'")
            return True
        print(f"  created: {doctype} '{name}'")
        return True


# -----------------------------------------------------------------------
# Bootstrap routines
# -----------------------------------------------------------------------

def bootstrap_item_groups(client: ERPNextClient) -> None:
    print("\n=== Item Groups ===")
    for name, parent in ITEM_GROUPS:
        client.create("Item Group", {
            "doctype": "Item Group",
            "item_group_name": name,
            "parent_item_group": parent,
            "is_group": 0,
        })


def bootstrap_warehouses(client: ERPNextClient, company: str) -> None:
    print("\n=== Warehouses ===")
    for wh_name, parent in WAREHOUSES:
        doc: dict = {
            "doctype": "Warehouse",
            "warehouse_name": wh_name,
            "company": company,
        }
        if parent:
            doc["parent_warehouse"] = parent
        client.create("Warehouse", doc)


def bootstrap_uoms(client: ERPNextClient) -> None:
    print("\n=== Units of Measure ===")
    for uom in UOMS:
        client.create("UOM", {
            "doctype": "UOM",
            "uom_name": uom,
        })


def bootstrap_cost_centers(client: ERPNextClient, company: str) -> None:
    print("\n=== Cost Centers ===")
    for cc_name, parent in COST_CENTERS:
        client.create("Cost Center", {
            "doctype": "Cost Center",
            "cost_center_name": cc_name,
            "parent_cost_center": parent,
            "company": company,
            "is_group": 0,
        })


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap ERPNext minimum structure")
    parser.add_argument("--url", default=os.environ.get("ERPNEXT_URL", DEFAULT_URL))
    parser.add_argument("--user", default=os.environ.get("ERPNEXT_USER", DEFAULT_USER))
    parser.add_argument("--password", default=os.environ.get("ERPNEXT_PASSWORD", DEFAULT_PASSWORD))
    parser.add_argument("--company", default=os.environ.get("ERPNEXT_COMPANY", DEFAULT_COMPANY))
    parser.add_argument("--company-abbr", default=DEFAULT_COMPANY_ABR)
    parser.add_argument("--dry-run", action="store_true", help="Print what would be created, no HTTP calls")
    parser.add_argument("--skip-uoms", action="store_true")
    parser.add_argument("--skip-warehouses", action="store_true")
    parser.add_argument("--skip-item-groups", action="store_true")
    parser.add_argument("--skip-cost-centers", action="store_true")
    args = parser.parse_args()

    # Patch cost centers to use correct company name
    global COST_CENTERS
    root_cc = f"{args.company} - {args.company_abbr}"
    COST_CENTERS = [
        (name, root_cc if parent == f"{DEFAULT_COMPANY} - {DEFAULT_COMPANY_ABR}" else parent)
        for name, parent in COST_CENTERS
    ]

    client = ERPNextClient(base_url=args.url, user=args.user, password=args.password, dry_run=args.dry_run)
    if not args.dry_run:
        client.login()

    if not args.skip_item_groups:
        bootstrap_item_groups(client)
    if not args.skip_warehouses:
        bootstrap_warehouses(client, args.company)
    if not args.skip_uoms:
        bootstrap_uoms(client)
    if not args.skip_cost_centers:
        bootstrap_cost_centers(client, args.company)

    print("\nDone.")


if __name__ == "__main__":
    main()
