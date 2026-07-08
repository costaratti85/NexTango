"""Endpoints del vectorizador de imágenes.

vectorize_image(file_url)
    → {run_id, presets: [{name, slug, transform_scale, viewbox, entity_count,
                          svg_full, entities: [{id, bbox_approx, nodes}]}]}

compose_pattern(run_id, preset, selected_entity_ids, escala_display,
                step_x_mm, step_y_mm, nombre, visibilidad,
                customer=None, descripcion=None)
    → {ok, name, version, has_splines, spline_count}

Runs almacenados en <site>/private/vectorize_runs/{run_id}/ (efímeros, sin doctype).
"""
import json
import re
import shutil
import time
from pathlib import Path

import frappe


def _runs_root() -> Path:
    return Path(frappe.get_site_path("private", "vectorize_runs"))


def _images_root() -> Path:
    return Path(frappe.get_site_path("private", "vectorize_images"))


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
    """Vectoriza imagen con potrace (5 presets). Devuelve SVG interactivo por preset."""
    from sistema_industrial.vectorize.runner import vectorize, PRESETS

    image_path = _resolve_frappe_file(file_url)

    if presets and isinstance(presets, str):
        presets = json.loads(presets)
    if not presets:
        presets = PRESETS

    run_id = _new_run_id()
    runs_root = _runs_root()
    run_dir = runs_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # Limpiar runs anteriores (un solo run activo a la vez)
    for old_run in runs_root.iterdir():
        if old_run.is_dir() and old_run.name != run_id:
            shutil.rmtree(old_run, ignore_errors=True)

    # Purgar imágenes fuente con más de 90 días
    images_root = _images_root()
    if images_root.exists():
        cutoff = time.time() - 90 * 86400
        for img_file in images_root.iterdir():
            if img_file.is_file() and img_file.stat().st_mtime < cutoff:
                img_file.unlink(missing_ok=True)

    # Persistir ruta de imagen original para que compose_pattern pueda copiarla
    (run_dir / "source_image.txt").write_text(str(image_path), encoding="utf-8")

    return vectorize(image_path, run_dir, presets)


@frappe.whitelist(allow_guest=False)
def compose_pattern(run_id, escala_display, step_x_mm, step_y_mm,
                    nombre, visibilidad,
                    selected_items=None,
                    preset=None, selected_entity_ids=None,
                    customer=None, descripcion=None):
    """Compone DXF con las entidades seleccionadas y registra SI Patron.

    Acepta dos formatos:
    - Nuevo (preferred): selected_items=[{entity_id, preset}, ...] — cada entidad
      puede venir de un preset distinto.
    - Legado (compat): preset + selected_entity_ids — un preset para todas.
    """
    from sistema_industrial.vectorize.composer import compose_dxf, compose_dxf_legacy

    escala_display = float(escala_display)
    step_x_mm = float(step_x_mm)
    step_y_mm = float(step_y_mm)

    # Normalizar al formato unificado selected_items
    if selected_items is not None:
        if isinstance(selected_items, str):
            selected_items = json.loads(selected_items)
    elif preset is not None and selected_entity_ids is not None:
        if isinstance(selected_entity_ids, str):
            selected_entity_ids = json.loads(selected_entity_ids)
        selected_items = [
            {"entity_id": eid, "preset": preset}
            for eid in selected_entity_ids
        ]
    else:
        return {"ok": False, "error": "Se requiere selected_items o (preset + selected_entity_ids)"}

    run_dir = _runs_root() / run_id
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        return {"ok": False, "error": "run expirado o no encontrado"}

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    # Recuperar imagen original del sidecar (ausente en runs anteriores al campo)
    source_image_txt = run_dir / "source_image.txt"
    source_image_path = (
        Path(source_image_txt.read_text(encoding="utf-8").strip())
        if source_image_txt.exists() else None
    )

    safe_stem = re.sub(r"[^\w\-]", "_", nombre)
    tmp_dxf = run_dir / f"{safe_stem}_composed.dxf"
    compose_dxf(manifest, selected_items, escala_display, tmp_dxf)

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

    # Copiar imagen fuente a directorio persistente (retención 90 días)
    imagen_fuente = None
    if source_image_path and source_image_path.exists():
        images_root = _images_root()
        images_root.mkdir(parents=True, exist_ok=True)
        dest_img = images_root / f"{safe_stem}{source_image_path.suffix}"
        shutil.copy2(str(source_image_path), str(dest_img))
        imagen_fuente = str(dest_img)

    # Registrar el preset "principal" en parámetros (el más frecuente entre los items)
    preset_counts: dict = {}
    for item in selected_items:
        p = item.get("preset", "")
        preset_counts[p] = preset_counts.get(p, 0) + 1
    preset_dominante = max(preset_counts, key=preset_counts.get) if preset_counts else (preset or "")

    parametros = json.dumps({
        "step_x": step_x_mm,
        "step_y": step_y_mm,
        "origen": "vectorizado",
        "preset": preset_dominante,
        "escala_display": escala_display,
        "selected_items": selected_items,
    })

    from sistema_industrial.api.patrones import _count_splines, _generate_and_save_thumbnail
    sc = _count_splines(dest_path)

    if frappe.db.exists("SI Patron", nombre):
        doc = frappe.get_doc("SI Patron", nombre)
        doc.archivo_dxf = str(dest_path)
        doc.activo = 1
        doc.parametros = parametros
        doc.spline_count = sc
        if imagen_fuente:
            doc.imagen_fuente = imagen_fuente
    else:
        doc = frappe.new_doc("SI Patron")
        doc.name = nombre
        doc.tipo = "Vectorizado"
        doc.visibilidad = visibilidad
        doc.cliente = customer or ""
        doc.descripcion = descripcion or ""
        doc.archivo_dxf = str(dest_path)
        doc.parametros = parametros
        doc.spline_count = sc
        doc.activo = 1
        doc.imagen_fuente = imagen_fuente or ""

    doc.save(ignore_permissions=True)
    frappe.db.commit()

    _generate_and_save_thumbnail(nombre, dest_path)

    return {
        "ok": True,
        "name": doc.name,
        "version": doc.version,
        "has_splines": sc > 0,
        "spline_count": sc,
    }


@frappe.whitelist(allow_guest=False)
def get_entity_variants(run_id, entity_id, source_preset):
    """Devuelve las variantes de una entidad puntual en los otros presets.

    Dado entity_id en source_preset, busca la entidad equivalente en cada
    uno de los demás presets por proximidad de bbox-center (matching lazy,
    client-side no necesita conocer la lógica).

    Returns:
    {
      "variants": [
        {"preset": "Esquinas",   "entity_id": "e2", "available": true,
         "bbox_approx": {...}},
        {"preset": "Ultra-Fino", "entity_id": "e0", "available": false},
        ...
      ]
    }
    """
    run_dir = _runs_root() / run_id
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        return {"ok": False, "error": "run expirado o no encontrado"}

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    # Encontrar la entidad de referencia en el preset fuente
    src_preset = next(
        (p for p in manifest.get("presets", []) if p["name"] == source_preset), None
    )
    if src_preset is None:
        return {"ok": False, "error": f"Preset '{source_preset}' no encontrado"}

    src_entity = next(
        (e for e in src_preset.get("entities", []) if e["id"] == entity_id), None
    )
    if src_entity is None:
        return {"ok": False, "error": f"Entidad '{entity_id}' no encontrada en {source_preset}"}

    # Centro de bbox de la entidad de referencia
    bb = src_entity.get("bbox_approx", {})
    ref_cx = bb.get("x", 0) + bb.get("w", 0) / 2.0
    ref_cy = bb.get("y", 0) + bb.get("h", 0) / 2.0
    ref_w = bb.get("w", 0)
    ref_h = bb.get("h", 0)

    # Tolerancia: 10% de la dimensión mayor, mínimo 5 unidades display
    img_dim = max(ref_w, ref_h, 1.0)
    tol = max(img_dim * 0.10, 5.0)

    variants = []
    for p in manifest.get("presets", []):
        if p["name"] == source_preset:
            # La propia entidad en su preset origen
            variants.append({
                "preset": p["name"],
                "entity_id": entity_id,
                "available": True,
                "bbox_approx": src_entity.get("bbox_approx"),
                "is_source": True,
            })
            continue

        # Buscar la entidad más cercana por centro de bbox
        best = None
        best_dist = float("inf")
        for e in p.get("entities", []):
            ebb = e.get("bbox_approx", {})
            cx = ebb.get("x", 0) + ebb.get("w", 0) / 2.0
            cy = ebb.get("y", 0) + ebb.get("h", 0) / 2.0
            dist = ((cx - ref_cx) ** 2 + (cy - ref_cy) ** 2) ** 0.5
            if dist < best_dist:
                best_dist = dist
                best = e

        if best is not None and best_dist <= tol:
            variants.append({
                "preset": p["name"],
                "entity_id": best["id"],
                "available": True,
                "bbox_approx": best.get("bbox_approx"),
                "is_source": False,
            })
        else:
            variants.append({
                "preset": p["name"],
                "entity_id": None,
                "available": False,
                "is_source": False,
            })

    return {"ok": True, "variants": variants}


@frappe.whitelist(allow_guest=False)
def diagnose_svg_run(run_id=None):
    """Diagnóstico del pipeline vectorizador: analiza SVGs crudos de potrace.

    Sin run_id: usa el run más reciente en vectorize_runs/.
    Con run_id: usa ese directorio específico.

    Por cada preset reporta:
      raw_path_count      — cuántos <path> tiene el SVG crudo
      raw_d_summary       — largo del d de cada path + count de subpaths M…Z
      parsed_entity_count — entidades que produce _parse_potrace_svg + _split_subpaths
      svg_file_size_bytes — tamaño del .svg para detectar SVGs truncados/vacíos

    Permite comparar lo que potrace generó vs. lo que el parser captura.

    Uso:
        bench --site erp.local execute sistema_industrial.api.vectorizer.diagnose_svg_run
        bench --site erp.local execute sistema_industrial.api.vectorizer.diagnose_svg_run \\
            --kwargs '{"run_id": "vr_1234567890_abcd"}'
    """
    from sistema_industrial.vectorize.runner import _parse_potrace_svg, _split_subpaths

    runs_root = _runs_root()

    if run_id:
        run_dir = runs_root / run_id
    else:
        dirs = [d for d in runs_root.iterdir() if d.is_dir()] if runs_root.exists() else []
        if not dirs:
            return {"error": "No hay runs en vectorize_runs/"}
        run_dir = max(dirs, key=lambda d: d.stat().st_mtime)
        run_id = run_dir.name

    if not run_dir.exists():
        return {"error": f"Run no encontrado: {run_id}"}

    svg_files = sorted(run_dir.glob("*.svg"))
    if not svg_files:
        return {"error": f"No hay archivos .svg en {run_dir}", "run_id": run_id}

    preset_reports = []

    for svg_file in svg_files:
        svg_text = svg_file.read_text(encoding="utf-8", errors="replace")
        svg_size = len(svg_text)

        # Analyze raw <path> elements from potrace output
        raw_paths = list(re.finditer(r'<path\b[^>]*/>', svg_text))
        raw_path_count = len(raw_paths)

        d_summary = []
        for pm in raw_paths:
            elem = pm.group(0)
            dm = re.search(r'\bd="([^"]*)"', elem)
            d_val = dm.group(1).strip() if dm else ""
            m_count = len(re.findall(r'[Mm]', d_val))
            d_summary.append({
                "d_len": len(d_val),
                "M_count": m_count,         # number of subpaths (each M starts one)
                "is_compound": m_count > 1,
            })

        # What the parser actually extracts after splitting
        _, _, path_ds = _parse_potrace_svg(svg_text)
        parsed_entity_count = len(path_ds)

        preset_reports.append({
            "slug": svg_file.stem,
            "svg_file_size_bytes": svg_size,
            "raw_path_count": raw_path_count,
            "raw_d_summary": d_summary,
            "parsed_entity_count": parsed_entity_count,
            "expected_after_split": sum(s["M_count"] for s in d_summary),
        })

    return {
        "run_id": run_id,
        "run_dir": str(run_dir),
        "presets": preset_reports,
    }
