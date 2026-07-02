"""Migración de patrones al DocType SI Patron.

Migra:
  - Patrones paramétricos builtin (Tresbolillo, Cuadriculado, Cuadriculado Square)
  - Patrones de archivo de pattern_library.json (Subte, Philo, Cosmos, Hexagonal, Aconcagua)

Uso:
    bench --site erp.local execute sistema_industrial.migrate.migrate_patrones.run
    bench --site erp.local execute sistema_industrial.migrate.migrate_patrones.run \
        --kwargs '{"overwrite": true}'

    # Parche de paths tras copiar DXF al servidor (Forge MSG_029):
    bench --site erp.local execute sistema_industrial.migrate.migrate_patrones.fix_dxf_paths
"""
import json
from pathlib import Path


# Nombres exactos de los DXF copiados a /planos/generico/patrones/ por Forge (MSG_029).
_DXF_FILENAMES = {
    "Subte":      "subte Offx84 Offy84.dxf",
    "Philo":      "Philo_editado.dxf",
    "Cosmos":     "Cosmos OffXY 500.dxf",
    "Hexagonal":  "Hexagonal offx 19 offy 32.91.dxf",
    "Aconcagua":  "Aconcagua OFF XY 85.dxf",
}


_PARAMETRICOS = [
    {
        "name": "Tresbolillo",
        "tipo": "Paramétrico",
        "visibilidad": "Público",
        "descripcion": "Perforación circular en tresbolillo (hexagonal offset)",
        "parametros": {"forma": "tresbolillo", "step_x": None, "step_y": None},
    },
    {
        "name": "Cuadriculado",
        "tipo": "Paramétrico",
        "visibilidad": "Público",
        "descripcion": "Perforación circular en grilla cuadrada",
        "parametros": {"forma": "cuadriculado", "step_x": None, "step_y": None},
    },
    {
        "name": "Cuadriculado Square",
        "tipo": "Paramétrico",
        "visibilidad": "Público",
        "descripcion": "Perforación cuadrada en grilla cuadrada",
        "parametros": {"forma": "cuadriculado_square", "step_x": None, "step_y": None},
    },
]


def run(overwrite=False):
    """Migra patrones builtin y de archivo al DocType SI Patron.

    overwrite=True: actualiza registros existentes.
    overwrite=False: salta los que ya existen.

    Retorna: {"inserted": N, "updated": M, "skipped": K, "errors": [...]}
    """
    import frappe

    counts = {"inserted": 0, "updated": 0, "skipped": 0}
    errors = []

    # Patrones paramétricos builtin
    for p in _PARAMETRICOS:
        try:
            result = _upsert(p, overwrite, frappe)
            counts[result] += 1
        except Exception as exc:
            errors.append({"name": p["name"], "error": str(exc)})

    # Patrones de archivo desde pattern_library.json
    lib_file = _find_pattern_library()
    if lib_file is None:
        errors.append({"name": "pattern_library.json", "error": "Archivo no encontrado"})
    else:
        try:
            library = json.loads(lib_file.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append({"name": "pattern_library.json", "error": str(exc)})
            library = {}

        for name, entry in library.items():
            if entry.get("type") != "dxf":
                continue
            p = {
                "name": name,
                "tipo": "Archivo",
                "visibilidad": "Público",
                "descripcion": "",
                "archivo_dxf": entry.get("file_path", ""),
                "parametros": {
                    "step_x": entry.get("step_x"),
                    "step_y": entry.get("step_y"),
                },
            }
            try:
                result = _upsert(p, overwrite, frappe)
                counts[result] += 1
            except Exception as exc:
                errors.append({"name": name, "error": str(exc)})

    frappe.db.commit()
    return {**counts, "errors": errors}


def _upsert(p, overwrite, frappe):
    """Inserta o actualiza un SI Patron. Retorna 'inserted', 'updated' o 'skipped'."""
    name = p["name"]
    parametros_json = json.dumps(p["parametros"], ensure_ascii=False)

    if frappe.db.exists("SI Patron", name):
        if not overwrite:
            return "skipped"
        doc = frappe.get_doc("SI Patron", name)
        doc.tipo = p["tipo"]
        doc.visibilidad = p["visibilidad"]
        doc.descripcion = p.get("descripcion", "")
        doc.parametros = parametros_json
        if p.get("archivo_dxf"):
            doc.archivo_dxf = p["archivo_dxf"]
        doc.save(ignore_permissions=True)
        return "updated"

    payload = {
        "doctype": "SI Patron",
        "name": name,
        "tipo": p["tipo"],
        "visibilidad": p["visibilidad"],
        "descripcion": p.get("descripcion", ""),
        "parametros": parametros_json,
    }
    if p.get("archivo_dxf"):
        payload["archivo_dxf"] = p["archivo_dxf"]
    doc = frappe.get_doc(payload)
    doc.insert(ignore_permissions=True)
    return "inserted"


def _find_pattern_library():
    try:
        from sistema_industrial.presets.legacy_panel_adapter import find_legacy_panel_dir
        p = find_legacy_panel_dir() / "pattern_library.json"
        return p if p.exists() else None
    except Exception:
        return None


def fix_dxf_paths():
    """Actualiza los 5 SI Patron de archivo al path real en /planos/ del servidor.

    Corre DESPUÉS de que Forge copió los DXF a /home/costa/planos/generico/patrones/.
    Lee nextango_planos_path de site_config. Cada save dispara el versionado:
    se congela el path viejo en SI Patron Version y el master queda con el path nuevo.

    Retorna: {"updated": [...], "skipped": [...], "errors": [...]}
    """
    import frappe

    planos_path = frappe.conf.get("nextango_planos_path")
    if not planos_path:
        return {"error": "nextango_planos_path no configurado en site_config.json"}

    base = Path(planos_path) / "generico" / "patrones"
    updated, skipped, errors = [], [], []

    for patron_name, filename in _DXF_FILENAMES.items():
        try:
            if not frappe.db.exists("SI Patron", patron_name):
                skipped.append({"name": patron_name, "reason": "no existe en DB"})
                continue

            new_path = str(base / filename)

            if not Path(new_path).exists():
                skipped.append({"name": patron_name, "reason": f"archivo no encontrado en disco: {new_path}"})
                continue

            doc = frappe.get_doc("SI Patron", patron_name)
            if doc.archivo_dxf == new_path:
                skipped.append({"name": patron_name, "reason": "path ya es correcto"})
                continue

            doc.archivo_dxf = new_path
            doc.save(ignore_permissions=True)
            updated.append({"name": patron_name, "path": new_path, "version": int(doc.version or 1)})
        except Exception as exc:
            errors.append({"name": patron_name, "error": str(exc)})

    frappe.db.commit()
    return {"updated": updated, "skipped": skipped, "errors": errors}
