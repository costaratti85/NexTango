"""Migración de patrones al DocType SI Patron.

Migra:
  - Patrones paramétricos builtin (Tresbolillo, Cuadriculado, Cuadriculado Square)
  - Patrones de archivo de pattern_library.json (Subte, Philo, Cosmos, Hexagonal, Aconcagua)

Uso:
    bench --site erp.local execute sistema_industrial.migrate.migrate_patrones.run
    bench --site erp.local execute sistema_industrial.migrate.migrate_patrones.run \
        --kwargs '{"overwrite": true}'
"""
import json


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
