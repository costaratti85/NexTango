"""Migración de patrones al DocType SI Patron.

Migra:
  - Patrones paramétricos builtin (solo Tresbolillo — Cuadriculado y Cuadriculado Square eliminados)
  - Patrones de archivo de pattern_library.json (Subte, Philo, Cosmos, Hexagonal, Aconcagua)

Uso:
    bench --site erp.local execute sistema_industrial.migrate.migrate_patrones.run
    bench --site erp.local execute sistema_industrial.migrate.migrate_patrones.run \
        --kwargs '{"overwrite": true}'

    # Borrar docs específicos por nombre (hard-delete con DXF + File huérfano):
    bench --site erp.local execute sistema_industrial.migrate.migrate_patrones.delete_named_patrones \
        --kwargs '{"names": ["Cuadriculado", "Cuadriculado Square"]}'

    # Borrado total de patrones DXF (decisión Constantino — los va a recargar):
    bench --site erp.local execute sistema_industrial.migrate.migrate_patrones.wipe_file_patterns

    # OBSOLETO (reemplazado por wipe_file_patterns):
    # bench --site erp.local execute sistema_industrial.migrate.migrate_patrones.fix_dxf_paths
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
    # "Cuadriculado" y "Cuadriculado Square" eliminados por decisión de Constantino (2026-07-03).
    # No recrear. Usar delete_named_patrones() para hard-delete si reaparecen.
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


def migrate_parametricos():
    """Inserta o repara los patrones paramétricos builtin (actualmente solo Tresbolillo).

    Cubre dos casos:
    - Doc faltante (migration nunca corrió): lo inserta con activo=1.
    - Doc existente con activo=NULL/0 (field añadido después de la inserción):
      fuerza activo=1 sin tocar el resto.

    Retorna: {"inserted": [...], "fixed_activo": [...], "ok": [...], "errors": [...]}
    """
    import frappe

    inserted, fixed_activo, ok_list, errors = [], [], [], []

    for p in _PARAMETRICOS:
        name = p["name"]
        try:
            if not frappe.db.exists("SI Patron", name):
                payload = {
                    "doctype": "SI Patron",
                    "name": name,
                    "tipo": p["tipo"],
                    "visibilidad": p["visibilidad"],
                    "descripcion": p.get("descripcion", ""),
                    "parametros": json.dumps(p["parametros"], ensure_ascii=False),
                    "activo": 1,
                }
                doc = frappe.get_doc(payload)
                doc.insert(ignore_permissions=True)
                inserted.append(name)
            else:
                doc = frappe.get_doc("SI Patron", name)
                if not doc.activo:
                    doc.activo = 1
                    doc.save(ignore_permissions=True)
                    fixed_activo.append(name)
                else:
                    ok_list.append(name)
        except Exception as exc:
            errors.append({"name": name, "error": str(exc)})

    frappe.db.commit()
    return {"inserted": inserted, "fixed_activo": fixed_activo, "ok": ok_list, "errors": errors}


def delete_named_patrones(names):
    """Hard-delete de SI Patron por nombre, sin importar su tipo.

    Borra: doc + versiones (cascada), .dxf físico, Frappe File huérfano privado.

    Uso:
        bench --site erp.local execute sistema_industrial.migrate.migrate_patrones.delete_named_patrones \
            --kwargs '{"names": ["Cuadriculado", "Cuadriculado Square"]}'

    Retorna: {"borrados": [...], "no_encontrados": [...], "errors": [...]}
    """
    import frappe

    borrados, no_encontrados, errors = [], [], []

    for name in names:
        if not frappe.db.exists("SI Patron", name):
            no_encontrados.append(name)
            continue

        try:
            doc = frappe.get_doc("SI Patron", name)
            dxf_path = (doc.archivo_dxf or "").strip()

            # Borrar .dxf físico si existe
            if dxf_path:
                try:
                    p = Path(dxf_path)
                    if p.exists():
                        p.unlink()
                except Exception as exc:
                    errors.append({"step": "unlink_dxf", "name": name, "error": str(exc)})

            # Hard-delete del doc (cascada a SI Patron Version)
            frappe.delete_doc(
                "SI Patron", name,
                force=True, delete_permanently=True, ignore_permissions=True,
            )
            borrados.append(name)
        except Exception as exc:
            errors.append({"step": "delete_doc", "name": name, "error": str(exc)})

    frappe.db.commit()

    # Borrar Frappe File huérfanos privados .dxf que quedaran referenciados
    huerfanos = frappe.db.get_all(
        "File",
        filters={"file_url": ["like", "/private/files/%.dxf"]},
        fields=["name", "file_url"],
    )
    for f in huerfanos:
        try:
            frappe.delete_doc(
                "File", f["name"],
                force=True, delete_permanently=True, ignore_permissions=True,
            )
        except Exception as exc:
            errors.append({"step": "delete_file", "name": f["name"], "error": str(exc)})

    frappe.db.commit()
    return {"borrados": borrados, "no_encontrados": no_encontrados, "errors": errors}


def wipe_file_patterns():
    """Hard-delete de todos los SI Patron tipo Archivo + Vectorizado.

    Decisión de Constantino (autorizada en vivo, 2026-07-02): borrar los
    patrones DXF para recargarlos desde cero. No hay pedidos que los referencien.

    Alcance:
      1. Borrar SI Patron con tipo IN ("Archivo", "Vectorizado") y sus versiones
         congeladas (SI Patron Version — cascada de delete_doc).
      2. Borrar los .dxf físicos referenciados en archivo_dxf.
      3. Borrar Frappe File huérfanos (archivos privados .dxf subidos por el
         FileUploader de admin-patrones antes de copiarse a /planos/).
      4. Neutralizar el fallback a pattern_library.json → escribirlo como {}.
         Sin esto, si SI Patron queda vacío de activos, get_all() caería al JSON
         y los patrones borrados reaparecerían.

    NO modifica los patrones Paramétricos (Tresbolillo, Cuadriculado, etc.).

    Retorna:
      {docs_borrados, versiones_borradas, archivos_borrados,
       files_huerfanos_borrados, errors}
    """
    import frappe

    docs_borrados = []
    archivos_borrados = []
    errors = []

    # 1. Localizar todos los SI Patron no-paramétricos
    targets = frappe.db.get_all(
        "SI Patron",
        filters={"tipo": ["in", ["Archivo", "Vectorizado"]]},
        fields=["name", "archivo_dxf"],
    )

    for t in targets:
        name = t["name"]
        dxf_path = (t.get("archivo_dxf") or "").strip()

        # Contar versiones antes de borrar (para el reporte)
        versiones_count = frappe.db.count("SI Patron Version", {"parent": name})

        # Borrar .dxf físico
        if dxf_path:
            try:
                p = Path(dxf_path)
                if p.exists():
                    p.unlink()
                    archivos_borrados.append(dxf_path)
            except Exception as exc:
                errors.append({
                    "step": "unlink_dxf", "name": name,
                    "path": dxf_path, "error": str(exc),
                })

        # Hard-delete del doc (cascada a SI Patron Version por ser tabla hija)
        try:
            frappe.delete_doc(
                "SI Patron", name,
                force=True, delete_permanently=True, ignore_permissions=True,
            )
            docs_borrados.append({"name": name, "versiones": versiones_count})
        except Exception as exc:
            errors.append({"step": "delete_doc", "name": name, "error": str(exc)})

    frappe.db.commit()

    # 3. Borrar Frappe File huérfanos (privados .dxf subidos por el FileUploader)
    huerfanos = frappe.db.get_all(
        "File",
        filters={"file_url": ["like", "/private/files/%.dxf"]},
        fields=["name", "file_url"],
    )
    files_borrados = []
    for f in huerfanos:
        try:
            frappe.delete_doc(
                "File", f["name"],
                force=True, delete_permanently=True, ignore_permissions=True,
            )
            files_borrados.append(f["file_url"])
        except Exception as exc:
            errors.append({"step": "delete_file", "name": f["name"], "error": str(exc)})

    frappe.db.commit()

    # 4. Neutralizar fallback: vaciar pattern_library.json
    lib_file = _find_pattern_library()
    if lib_file:
        try:
            lib_file.write_text("{}", encoding="utf-8")
        except Exception as exc:
            errors.append({"step": "neutralize_library", "error": str(exc)})

    total_versiones = sum(d["versiones"] for d in docs_borrados)

    return {
        "docs_borrados": len(docs_borrados),
        "docs_borrados_nombres": [d["name"] for d in docs_borrados],
        "versiones_borradas": total_versiones,
        "archivos_borrados": len(archivos_borrados),
        "files_huerfanos_borrados": len(files_borrados),
        "errors": errors,
    }


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
