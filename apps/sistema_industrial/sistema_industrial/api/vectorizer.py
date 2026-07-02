"""Endpoints del vectorizador de imágenes.

vectorize_image(file_url, presets=None)
    → {run_id, preset_names, figura_count, figuras: [...]}

compose_pattern(run_id, selecciones, nombre, step_x, step_y, visibilidad,
                customer=None, descripcion=None)
    → {ok, name, version, has_splines, spline_count}

Runs se almacenan en <site>/private/vectorize_runs/{run_id}/ (efímeros, sin doctype).
"""
import json
import re
import shutil
import time
from pathlib import Path

import frappe


def _runs_root() -> Path:
    return Path(frappe.get_site_path("private", "vectorize_runs"))


def _new_run_id() -> str:
    return f"vr_{int(time.time())}_{frappe.generate_hash(length=4)}"


def _resolve_frappe_file(file_url: str) -> Path:
    fname = frappe.db.get_value("File", {"file_url": file_url}, "name")
    if not fname:
        frappe.throw(f"Archivo no encontrado en Frappe: {file_url}")
    return Path(frappe.get_doc("File", fname).get_full_path())


def _patron_dest_dir(visibilidad, customer=None) -> Path:
    from sistema_industrial.api.patrones import _planos_root
    root = _planos_root()
    if visibilidad == "Exclusivo" and customer:
        return root / customer / "patrones"
    return root / "generico" / "patrones"


@frappe.whitelist(allow_guest=False)
def vectorize_image(file_url, presets=None):
    """Corre potrace con 5 presets y devuelve figuras con previews SVG por variante."""
    from sistema_industrial.vectorize.runner import vectorize, PRESETS

    image_path = _resolve_frappe_file(file_url)

    if presets and isinstance(presets, str):
        presets = json.loads(presets)
    if not presets:
        presets = PRESETS

    run_id = _new_run_id()
    run_dir = _runs_root() / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    return vectorize(image_path, run_dir, presets)


@frappe.whitelist(allow_guest=False)
def compose_pattern(run_id, selecciones, nombre, step_x, step_y, visibilidad,
                    customer=None, descripcion=None):
    """Compone DXF con las figuras/variantes elegidas y registra SI Patron."""
    from sistema_industrial.vectorize.composer import compose_dxf

    if isinstance(selecciones, str):
        selecciones = json.loads(selecciones)
    step_x = float(step_x)
    step_y = float(step_y)

    run_dir = _runs_root() / run_id
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        return {"ok": False, "error": "run expirado o no encontrado"}

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    # Compose DXF in run_dir (temp)
    safe_stem = re.sub(r"[^\w\-]", "_", nombre)
    tmp_dxf = run_dir / f"{safe_stem}_composed.dxf"
    compose_dxf(manifest, selecciones, tmp_dxf)

    # Determine destination and version suffix
    dest_dir = _patron_dest_dir(visibilidad, customer)
    dest_dir.mkdir(parents=True, exist_ok=True)

    if frappe.db.exists("SI Patron", nombre):
        doc = frappe.get_doc("SI Patron", nombre)
        next_v = len(doc.versiones) + 1
        dxf_filename = f"{safe_stem}_v{next_v}.dxf"
    else:
        dxf_filename = f"{safe_stem}.dxf"

    dest_path = dest_dir / dxf_filename
    shutil.copy2(str(tmp_dxf), str(dest_path))

    parametros = json.dumps({"step_x": step_x, "step_y": step_y, "origen": "vectorizado"})

    if frappe.db.exists("SI Patron", nombre):
        doc = frappe.get_doc("SI Patron", nombre)
        doc.archivo_dxf = str(dest_path)
        doc.activo = 1
    else:
        doc = frappe.new_doc("SI Patron")
        doc.name = nombre
        doc.tipo = "Vectorizado"
        doc.visibilidad = visibilidad
        doc.cliente = customer or ""
        doc.descripcion = descripcion or ""
        doc.archivo_dxf = str(dest_path)
        doc.parametros = parametros
        doc.spline_count = 0
        doc.activo = 1

    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return {
        "ok": True,
        "name": doc.name,
        "version": doc.version,
        "has_splines": False,
        "spline_count": 0,
    }
