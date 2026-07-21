"""Endpoints para el catálogo de patrones del panel decorativo.

URL base: /api/method/sistema_industrial.api.patrones.

Endpoints:
    get_all(customer=None)       — patrones Públicos + Exclusivos del cliente (activos)
    get_patron(name, version)    — resolver versionado (contrato con SI Pieza / Lechu)
    upload_pattern(...)          — copia DXF desde File de Frappe a /planos/, crea SI Patron
    update_pattern(...)          — edita definición y/o reemplaza/reapunta el DXF de un patrón
    list_dxf_files()             — lista los .dxf bajo /planos/ (picker de reapunte)
    delete_pattern(name)         — baja lógica: activo=0 (archivo queda en disco)
    list_admin()                 — todos los patrones incl. inactivos (grilla de admin)
"""
import json
import os
import re
import shutil
from pathlib import Path

import frappe


def _safe_name(name):
    return re.sub(r"[^\w]", "_", name)


def _safe_filename(filename):
    """Basename seguro: sin path traversal, sin caracteres peligrosos."""
    name = os.path.basename(filename)
    safe = re.sub(r"[^\w\-.]", "_", name)
    return safe or "patron.dxf"


def _planos_root() -> Path:
    """Raíz configurable en site_config como nextango_planos_path."""
    configured = frappe.conf.get("nextango_planos_path")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[4] / "planos"


def _patron_dest_dir(visibilidad, customer=None) -> Path:
    root = _planos_root()
    if visibilidad == "Exclusivo" and customer:
        return root / customer / "patrones"
    return root / "generico" / "patrones"


def _resolve_frappe_file(file_url: str) -> Path:
    """Resuelve un file_url de Frappe (/private/files/...) al path absoluto en disco."""
    fname = frappe.db.get_value("File", {"file_url": file_url}, "name")
    if not fname:
        frappe.throw(f"Archivo de Frappe no encontrado para URL: {file_url}")
    return Path(frappe.get_doc("File", fname).get_full_path())


def _count_splines(dxf_path) -> int:
    """Cuenta entidades SPLINE en el modelspace del DXF. Retorna 0 si falla."""
    try:
        import ezdxf
        doc = ezdxf.readfile(str(dxf_path))
        return sum(1 for e in doc.modelspace() if e.dxftype() == "SPLINE")
    except Exception:
        return 0


_THUMBNAIL_BASE = "/assets/sistema_industrial/pattern_thumbnails"


def _thumb_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "public" / "pattern_thumbnails"


def _thumb_url(nombre: str):
    safe = _safe_name(nombre)
    p = _thumb_dir() / f"{safe}.png"
    return f"{_THUMBNAIL_BASE}/{safe}.png" if p.exists() else None


def _render_dxf_to_png(dxf_path, out_path, size_px=400) -> bool:
    """Renderiza un DXF a PNG con fondo blanco. Retorna True si hay contenido."""
    import math
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    import ezdxf

    doc = ezdxf.readfile(str(dxf_path))
    msp = doc.modelspace()

    fig, ax = plt.subplots(figsize=(size_px / 100, size_px / 100), dpi=100)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.set_aspect("equal")
    ax.axis("off")

    has_content = False
    for e in msp:
        etype = e.dxftype()
        try:
            if etype == "LINE":
                ax.plot(
                    [e.dxf.start.x, e.dxf.end.x],
                    [e.dxf.start.y, e.dxf.end.y],
                    color="black", linewidth=0.5,
                )
                has_content = True
            elif etype in ("ARC", "CIRCLE"):
                cx, cy = e.dxf.center.x, e.dxf.center.y
                r = e.dxf.radius
                if etype == "ARC":
                    a0 = math.radians(e.dxf.start_angle)
                    a1 = math.radians(e.dxf.end_angle)
                    if a1 <= a0:
                        a1 += 2 * math.pi
                else:
                    a0, a1 = 0.0, 2 * math.pi
                n = max(32, int(abs(a1 - a0) / math.pi * 64))
                angles = np.linspace(a0, a1, n)
                ax.plot(cx + r * np.cos(angles), cy + r * np.sin(angles),
                        color="black", linewidth=0.5)
                has_content = True
            elif etype == "LWPOLYLINE":
                pts = list(e.get_points())
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                if e.closed:
                    xs.append(xs[0])
                    ys.append(ys[0])
                ax.plot(xs, ys, color="black", linewidth=0.5)
                has_content = True
            elif etype == "SPLINE":
                flat = list(e.flattening(0.1))
                if flat:
                    ax.plot([p[0] for p in flat], [p[1] for p in flat],
                            color="black", linewidth=0.5)
                    has_content = True
        except Exception:
            pass

    if not has_content:
        plt.close(fig)
        return False

    ax.autoscale()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(out_path), dpi=100, bbox_inches="tight",
                facecolor="white", pad_inches=0.05)
    plt.close(fig)
    return True


def _save_thumbnail(nombre: str, dxf_path, step_x, step_y):
    """Genera el thumbnail PNG. Intenta panel tileado; fallback a figura suelta."""
    import tempfile
    dxf_path = Path(str(dxf_path))
    if not dxf_path.exists():
        return None

    safe = _safe_name(nombre)
    out_path = _thumb_dir() / f"{safe}.png"

    tiled_ok = False
    if step_x and step_y:
        try:
            from sistema_industrial.presets.legacy_panel_adapter import (
                LegacyPanelAdapter, LegacyPanelRunRequest,
            )
            with tempfile.TemporaryDirectory() as tmp:
                tmp_dxf = Path(tmp) / f"{safe}_panel.dxf"
                req = LegacyPanelRunRequest(
                    preset_code=f"thumb_{safe}",
                    preset_name=f"thumb_{safe}",
                    material="generic",
                    thickness_mm=1.0,
                    width_mm=300.0,
                    height_mm=300.0,
                    quantity=1,
                    output_dxf_path=tmp_dxf,
                    pattern_type="dxf",
                    pattern_dxf_path=dxf_path,
                    step_x_mm=float(step_x),
                    step_y_mm=float(step_y),
                    margin_mm=20.0,
                    cut_partial_figures=True,
                )
                result = LegacyPanelAdapter().run(req)
                total_geom = sum(
                    r.get("geometry_item_count", 0)
                    for r in result.calculated_resources
                )
                if total_geom > 0:
                    tiled_ok = _render_dxf_to_png(tmp_dxf, out_path)
        except Exception as exc:
            frappe.log_error(f"thumbnail tileado {nombre}: {exc}", "thumbnail_motor_panel")

    if not tiled_ok:
        try:
            _render_dxf_to_png(dxf_path, out_path)
        except Exception as exc:
            frappe.log_error(f"thumbnail fallback {nombre}: {exc}", "thumbnail_dxf_directo")
            return None

    return f"{_THUMBNAIL_BASE}/{safe}.png" if out_path.exists() else None


def _find_pattern_library():
    try:
        from sistema_industrial.presets.legacy_panel_adapter import find_legacy_panel_dir
        p = find_legacy_panel_dir() / "pattern_library.json"
        return p if p.exists() else None
    except Exception:
        return None


def _patron_doc_to_row(doc):
    """Convierte un dict de SI Patron en el formato de fila para get_all()."""
    name = doc.get("name", "")
    tipo = doc.get("tipo", "")
    visibilidad = doc.get("visibilidad", "Público")
    version = int(doc.get("version") or 1)

    try:
        parametros = json.loads(doc.get("parametros") or "{}")
    except (json.JSONDecodeError, TypeError):
        parametros = {}

    step_x = parametros.get("step_x")
    step_y = parametros.get("step_y")

    if tipo in ("Archivo", "Vectorizado"):
        file_path = str(doc.get("archivo_dxf") or "")
        try:
            file_available = bool(file_path) and Path(file_path).exists()
        except Exception:
            file_available = False
    else:
        file_path = ""
        file_available = True

    spline_count = int(doc.get("spline_count") or 0)
    return {
        "name": name,
        "label": name,
        "file_path": file_path,
        "step_x": step_x,
        "step_y": step_y,
        "file_available": file_available,
        "restricted": False,
        "restricted_reason": "",
        "tipo": tipo,
        "visibilidad": visibilidad,
        "version": version,
        "parametros": parametros,
        "has_splines": spline_count > 0,
        "spline_count": spline_count,
        "thumbnail_url": _thumb_url(name),
    }


_TIPO_ORDER = {"Paramétrico": 0, "Archivo": 1, "Vectorizado": 1}


def _sort_patron_rows(rows):
    """Ordena: Paramétrico primero, luego Archivo/Vectorizado; nombre ascendente dentro de cada grupo."""
    rows.sort(key=lambda r: (_TIPO_ORDER.get(r.get("tipo", "Archivo"), 1), r["name"]))
    return rows


def _get_all_from_frappe(customer=None):
    """Retorna lista de filas desde SI Patron, o None si el doctype está vacío."""
    try:
        total = frappe.db.count("SI Patron", {"activo": 1})
        if not total:
            return None

        fields = [
            "name", "tipo", "visibilidad", "cliente",
            "archivo_dxf", "parametros", "version", "descripcion",
            "activo", "spline_count",
        ]

        public_rows = frappe.get_all(
            "SI Patron",
            filters={"visibilidad": "Público", "activo": 1},
            fields=fields,
        )

        exclusive_rows = []
        if customer:
            exclusive_rows = frappe.get_all(
                "SI Patron",
                filters={"visibilidad": "Exclusivo", "cliente": customer, "activo": 1},
                fields=fields,
            )

        rows = [_patron_doc_to_row(d) for d in public_rows + exclusive_rows]
        return _sort_patron_rows(rows)
    except Exception as exc:
        frappe.log_error(f"patrones.get_all: error leyendo SI Patron: {exc}")
        return None


def _get_all_from_legacy():
    """Fallback: lee pattern_library.json (igual que antes de la migración)."""
    rows = []
    lib_file = _find_pattern_library()
    if lib_file is None:
        frappe.log_error("patrones.get_all: no se encontró pattern_library.json")
        return rows

    try:
        library = json.loads(lib_file.read_text(encoding="utf-8"))
    except Exception as exc:
        frappe.log_error(f"patrones.get_all: error leyendo pattern_library.json: {exc}")
        return rows

    for name, entry in library.items():
        if entry.get("type") != "dxf":
            continue
        file_path = str(entry.get("file_path", ""))
        try:
            file_available = bool(file_path) and Path(file_path).exists()
        except Exception:
            file_available = False

        rows.append({
            "name": name,
            "label": name,
            "file_path": file_path,
            "step_x": entry.get("step_x"),
            "step_y": entry.get("step_y"),
            "file_available": file_available,
            "restricted": bool(entry.get("restricted", False)),
            "restricted_reason": str(entry.get("restricted_reason", "")),
            "tipo": "Archivo",
            "visibilidad": "Público",
            "version": 1,
            "parametros": {
                "step_x": entry.get("step_x"),
                "step_y": entry.get("step_y"),
            },
            "thumbnail_url": _thumb_url(name),
        })
    return _sort_patron_rows(rows)


@frappe.whitelist(allow_guest=False)
def get_all(customer=None):
    """Lista de patrones disponibles para la galería del panel decorativo.

    customer (opcional): nombre de Customer ERPNext. Si se pasa, incluye también
        los patrones Exclusivos de ese cliente.

    r.message:
    {
        "rows": [
            {
                "name": "Subte",
                "label": "Subte",
                "file_path": "//190.190.190.9/.../subte.dxf",
                "step_x": 84.0, "step_y": 84.0,
                "file_available": false,
                "restricted": false, "restricted_reason": "",
                "tipo": "Archivo",          // "Paramétrico" para builtin
                "visibilidad": "Público",   // o "Exclusivo"
                "version": 1,
                "parametros": {"step_x": 84.0, "step_y": 84.0}
            },
            ...
        ],
        "source": "frappe"  // o "legacy_json"
    }

    Notas:
    - Patrones Paramétricos tienen file_available=true siempre (el motor los genera directo).
    - Patrones Archivo: file_available=true solo si el DXF existe en el servidor.
    - Fallback a legacy_json si SI Patron está vacío (pre-migración).
    """
    frappe_rows = _get_all_from_frappe(customer)
    if frappe_rows is not None:
        return {"rows": frappe_rows, "source": "frappe"}

    return {"rows": _get_all_from_legacy(), "source": "legacy_json"}


@frappe.whitelist(allow_guest=False)
def upload_pattern(nombre, step_x, step_y, visibilidad, file_url, customer=None, descripcion=None):
    """Crea o actualiza un SI Patron copiando el DXF desde un File de Frappe a /planos/.

    El File ya fue subido por el browser vía frappe.ui.FileUploader.

    Args:
        nombre:      Nombre del patrón (= SI Patron.name)
        step_x:      Paso horizontal en mm (float o None)
        step_y:      Paso vertical en mm (float o None)
        visibilidad: "Público" o "Exclusivo"
        file_url:    URL del File de Frappe ej. /private/files/subte.dxf
        customer:    Nombre del Customer ERPNext (requerido si visibilidad="Exclusivo")
        descripcion: Descripción libre

    r.message: {ok: true, name, version}
    """
    if visibilidad == "Exclusivo" and not customer:
        frappe.throw("customer es requerido para visibilidad Exclusivo")

    src_path = _resolve_frappe_file(file_url)

    dest_dir = _patron_dest_dir(visibilidad, customer)
    dest_dir.mkdir(parents=True, exist_ok=True)

    safe = _safe_filename(src_path.name)

    if frappe.db.exists("SI Patron", nombre):
        existing = frappe.get_doc("SI Patron", nombre)
        next_v = int(existing.version or 1) + 1
        stem, ext = os.path.splitext(safe)
        safe = f"{stem}_v{next_v}{ext}"

    dest_path = dest_dir / safe
    shutil.copy2(str(src_path), str(dest_path))

    sc = _count_splines(dest_path)

    parametros = json.dumps({
        "step_x": float(step_x) if step_x not in (None, "") else None,
        "step_y": float(step_y) if step_y not in (None, "") else None,
    }, ensure_ascii=False)

    if frappe.db.exists("SI Patron", nombre):
        doc = frappe.get_doc("SI Patron", nombre)
        doc.archivo_dxf = str(dest_path)
        doc.visibilidad = visibilidad
        doc.cliente = customer if visibilidad == "Exclusivo" else ""
        if descripcion:
            doc.descripcion = descripcion
        doc.parametros = parametros
        doc.activo = 1
        doc.spline_count = sc
        doc.save(ignore_permissions=True)
    else:
        payload = {
            "doctype": "SI Patron",
            "name": nombre,
            "tipo": "Archivo",
            "visibilidad": visibilidad,
            "descripcion": descripcion or "",
            "archivo_dxf": str(dest_path),
            "parametros": parametros,
            "activo": 1,
            "spline_count": sc,
        }
        if visibilidad == "Exclusivo" and customer:
            payload["cliente"] = customer
        doc = frappe.get_doc(payload)
        doc.insert(ignore_permissions=True)

    frappe.db.commit()

    return {
        "ok": True,
        "name": nombre,
        "version": int(doc.version or 1),
        "has_splines": sc > 0,
        "spline_count": sc,
    }


def _validate_existing_dxf(dxf_path) -> Path:
    """Valida un path de reapunte: .dxf existente dentro de la raíz de planos.

    Acepta path absoluto o relativo a la raíz. Rechaza traversal fuera de la raíz.
    """
    root = _planos_root().resolve()
    p = Path(str(dxf_path))
    if not p.is_absolute():
        p = root / p
    try:
        resolved = p.resolve()
    except Exception:
        frappe.throw(f"Ruta inválida: {dxf_path}")
    if not str(resolved).startswith(str(root) + os.sep):
        frappe.throw("dxf_path debe estar dentro de la carpeta de planos del servidor")
    if resolved.suffix.lower() != ".dxf":
        frappe.throw("dxf_path debe apuntar a un archivo .dxf")
    if not resolved.is_file():
        frappe.throw(f"Archivo no encontrado en el servidor: {dxf_path}")
    return resolved


@frappe.whitelist(allow_guest=False)
def update_pattern(name, descripcion=None, visibilidad=None, customer=None,
                   step_x=None, step_y=None, offset_x=None, offset_y=None,
                   parametros=None, file_url=None, dxf_path=None, activo=None):
    """Edita la definición de un SI Patron existente y/o reemplaza/reapunta su DXF.

    Todos los argumentos salvo `name` son opcionales: lo que no se manda, no se toca.

    Args:
        name:        SI Patron existente (requerido).
        descripcion: reemplaza la descripción.
        visibilidad: "Público" | "Exclusivo" (Exclusivo requiere customer).
        customer:    Customer ERPNext (se limpia si visibilidad queda Público).
        step_x/step_y: float; "" limpia el valor.
        offset_x/offset_y: ALIAS de step_x/step_y (vocabulario del taller: el
                     offset X/Y del patrón es el paso de tileado — ver
                     legacy_panel_adapter: offset_x_mm <- step_x_mm). Se guarda
                     canónico como step_x/step_y en parametros. No mandar el
                     alias y el canónico a la vez.
        parametros:  JSON string — merge de claves sobre el JSON existente.
                     step_x/step_y (u offset_x/offset_y) explícitos pisan lo
                     que venga acá.
        file_url:    File de Frappe ya subido → se copia a /planos/ con sufijo _vN
                     (reemplazo con archivo nuevo).
        dxf_path:    path de un .dxf existente bajo la raíz de planos → reapunte
                     sin copia. Mutuamente excluyente con file_url.
        activo:      0|1 baja/alta lógica.

    Versionado (contrato con Lechu/MES): si cambia `parametros` o `archivo_dxf`,
    el before_save de SI Patron congela automáticamente una nueva fila append-only
    en SI Patron Version y bumpea `version`. Las versiones viejas nunca se tocan.

    r.message: {ok, name, version, previous_version, version_created, tipo,
                visibilidad, cliente, descripcion, activo, parametros,
                archivo_dxf, file_available, spline_count, has_splines,
                thumbnail_url}
    """
    if not frappe.db.exists("SI Patron", name):
        frappe.throw(f"Patrón '{name}' no encontrado", frappe.DoesNotExistError)
    if file_url and dxf_path:
        frappe.throw("file_url y dxf_path son mutuamente excluyentes: "
                     "subí un archivo nuevo O reapuntá a uno existente")

    # offset_x/offset_y son alias de step_x/step_y (misma propiedad del patrón)
    if offset_x is not None:
        if step_x is not None:
            frappe.throw("step_x y offset_x son la misma propiedad: mandá uno solo")
        step_x = offset_x
    if offset_y is not None:
        if step_y is not None:
            frappe.throw("step_y y offset_y son la misma propiedad: mandá uno solo")
        step_y = offset_y

    doc = frappe.get_doc("SI Patron", name)
    previous_version = int(doc.version or 1)

    if (file_url or dxf_path) and (doc.tipo or "") == "Paramétrico":
        frappe.throw("Un patrón Paramétrico no usa archivo DXF")

    # --- visibilidad / cliente (antes del DXF: definen carpeta destino del upload) ---
    if visibilidad not in (None, ""):
        if visibilidad not in ("Público", "Exclusivo"):
            frappe.throw(f"visibilidad inválida: {visibilidad}")
        doc.visibilidad = visibilidad
    if customer not in (None, ""):
        doc.cliente = customer
    if (doc.visibilidad or "") == "Exclusivo" and not doc.cliente:
        frappe.throw("customer es requerido para visibilidad Exclusivo")
    if (doc.visibilidad or "") == "Público":
        doc.cliente = ""

    # --- archivo DXF: reemplazo (file_url) o reapunte (dxf_path) ---
    dxf_changed = False
    if file_url:
        src_path = _resolve_frappe_file(file_url)
        dest_dir = _patron_dest_dir(doc.visibilidad, doc.cliente or None)
        dest_dir.mkdir(parents=True, exist_ok=True)
        safe = _safe_filename(src_path.name)
        stem, ext = os.path.splitext(safe)
        dest_path = dest_dir / f"{stem}_v{previous_version + 1}{ext}"
        shutil.copy2(str(src_path), str(dest_path))
        doc.archivo_dxf = str(dest_path)
        dxf_changed = True
    elif dxf_path:
        doc.archivo_dxf = str(_validate_existing_dxf(dxf_path))
        dxf_changed = True

    # --- parámetros: merge JSON + step_x/step_y explícitos ---
    try:
        current_params = json.loads(doc.parametros or "{}")
    except (json.JSONDecodeError, TypeError):
        current_params = {}
    params_changed = False
    if parametros not in (None, ""):
        extra = parametros
        if isinstance(extra, str):
            try:
                extra = json.loads(extra)
            except json.JSONDecodeError:
                frappe.throw("parametros no es JSON válido")
        if not isinstance(extra, dict):
            frappe.throw("parametros debe ser un objeto JSON")
        current_params.update(extra)
        params_changed = True
    for key, val in (("step_x", step_x), ("step_y", step_y)):
        if val is None:
            continue
        current_params[key] = float(val) if val != "" else None
        params_changed = True
    if params_changed:
        doc.parametros = json.dumps(current_params, ensure_ascii=False)

    # --- campos sueltos (no versionados) ---
    if descripcion is not None:
        doc.descripcion = descripcion
    if activo not in (None, ""):
        doc.activo = 1 if str(activo).lower() in ("1", "true") else 0

    if dxf_changed:
        doc.spline_count = _count_splines(doc.archivo_dxf)

    doc.save(ignore_permissions=True)
    frappe.db.commit()

    new_version = int(doc.version or 1)

    # Autogeneración del thumbnail (motor de Punto: generate_thumbnail -> {ok, url}).
    # MODO DE FALLA FIRME (MSG_020): si el render falla o el motor no sabe
    # renderizar este DXF, el patrón queda DISPONIBLE igual (con la miniatura
    # previa si había, o sin miniatura) y el update NUNCA rompe. Se loguea el
    # fallo — por excepción o por ok=False — para poder backfillear después.
    thumb_url = _thumb_url(name)
    if dxf_changed or params_changed:
        try:
            result = generate_thumbnail(name)
            if result.get("ok"):
                thumb_url = result.get("url") or thumb_url
            else:
                frappe.log_error(
                    f"update_pattern: thumbnail NO generado para '{name}' "
                    f"(motor ok=False: {result.get('reason', 's/d')}). "
                    f"Patrón disponible sin miniatura; backfilleable.",
                    "update_pattern_thumbnail")
        except Exception as exc:
            frappe.log_error(f"update_pattern thumbnail '{name}': {exc}. "
                             f"Patrón disponible sin miniatura; backfilleable.",
                             "update_pattern_thumbnail")

    file_path = str(doc.archivo_dxf or "")
    try:
        file_available = bool(file_path) and Path(file_path).exists()
    except Exception:
        file_available = False
    sc = int(doc.spline_count or 0)

    return {
        "ok": True,
        "name": name,
        "version": new_version,
        "previous_version": previous_version,
        "version_created": new_version != previous_version,
        "tipo": doc.tipo or "",
        "visibilidad": doc.visibilidad or "Público",
        "cliente": doc.cliente or "",
        "descripcion": doc.descripcion or "",
        "activo": int(doc.activo or 0),
        "parametros": current_params,
        "offset_x": current_params.get("step_x"),   # espejo de parametros.step_x
        "offset_y": current_params.get("step_y"),   # espejo de parametros.step_y
        "archivo_dxf": file_path,
        "file_available": file_available,
        "spline_count": sc,
        "has_splines": sc > 0,
        "thumbnail_url": thumb_url,
    }


@frappe.whitelist(allow_guest=False)
def list_dxf_files():
    """Lista los archivos .dxf bajo la raíz de planos (picker de reapunte).

    r.message:
    {
        "root": "/.../planos",
        "files": [
            {"path": "...", "relpath": "generico/patrones/x.dxf",
             "size_kb": 34.2, "modified": "2026-07-01 10:22:33",
             "used_by": ["Aconcagua"]}   // [] = huérfano
        ]
    }
    """
    from datetime import datetime

    root = _planos_root()

    used_map = {}
    try:
        for d in frappe.get_all("SI Patron", fields=["name", "archivo_dxf"]):
            p = (d.get("archivo_dxf") or "").strip()
            if p:
                used_map.setdefault(os.path.normpath(p), []).append(d["name"])
    except Exception as exc:
        frappe.log_error(f"list_dxf_files: error leyendo SI Patron: {exc}")

    files = []
    if root.exists():
        for f in sorted(root.rglob("*")):
            if not f.is_file() or f.suffix.lower() != ".dxf":
                continue
            try:
                st = f.stat()
            except OSError:
                continue
            used = (used_map.get(os.path.normpath(str(f)))
                    or used_map.get(os.path.normpath(str(f.resolve())))
                    or [])
            files.append({
                "path": str(f),
                "relpath": str(f.relative_to(root)),
                "size_kb": round(st.st_size / 1024, 1),
                "modified": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "used_by": used,
            })

    return {"root": str(root), "files": files}


@frappe.whitelist(allow_guest=False)
def delete_pattern(name):
    """Baja lógica: pone activo=0 en el SI Patron. El archivo DXF queda en disco.

    r.message: {ok: true, name: "Subte"}
    Error: frappe.DoesNotExistError si el patrón no existe.
    """
    if not frappe.db.exists("SI Patron", name):
        frappe.throw(f"Patrón '{name}' no encontrado", frappe.DoesNotExistError)
    doc = frappe.get_doc("SI Patron", name)
    doc.activo = 0
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {"ok": True, "name": name}


@frappe.whitelist(allow_guest=False)
def convert_splines(name):
    """Convierte splines a arcos en el DXF del patrón y guarda como nueva versión.

    Usa el conversor curado tools/dxf_spline_to_arcs.py (TASK_022 + fix puntas).
    El archivo original queda congelado en el historial (constraint de versionado).

    r.message:
    {
        "ok": true, "name": "Subte", "version": 2,
        "splines_convertidas": 12, "arcos_generados": 47, "lineas_generadas": 15
    }
    """
    if not frappe.db.exists("SI Patron", name):
        frappe.throw(f"Patrón '{name}' no encontrado", frappe.DoesNotExistError)

    doc = frappe.get_doc("SI Patron", name)
    src_path = Path(doc.archivo_dxf or "")
    if not src_path.exists():
        frappe.throw(f"Archivo DXF no disponible en disco: {doc.archivo_dxf}")

    next_v = int(doc.version or 1) + 1
    dest_path = src_path.parent / f"{src_path.stem}_v{next_v}{src_path.suffix}"

    from sistema_industrial.presets.panel_sales_local_app import convert_dxf_splines_clean
    stats = convert_dxf_splines_clean(str(src_path), str(dest_path), tolerance=0.1)

    doc.archivo_dxf = str(dest_path)
    doc.spline_count = 0
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return {
        "ok": True,
        "name": name,
        "version": int(doc.version or 1),
        "splines_convertidas": stats.get("converted_count", 0),
        "arcos_generados": stats.get("arc_count", 0),
        "lineas_generadas": stats.get("line_count", 0),
    }


@frappe.whitelist(allow_guest=False)
def list_admin():
    """Lista TODOS los SI Patron (activos e inactivos) para la página de administración.

    A diferencia de get_all(), no filtra por activo ni por customer.

    r.message:
    {
        "rows": [
            {
                "name", "tipo", "visibilidad", "cliente",
                "file_available", "version", "activo",
                "has_splines", "spline_count"
            },
            ...
        ]
    }
    """
    fields = [
        "name", "tipo", "visibilidad", "cliente",
        "archivo_dxf", "parametros", "version", "descripcion",
        "activo", "spline_count",
    ]
    docs = frappe.get_all("SI Patron", fields=fields, order_by="name asc")
    rows = []
    for d in docs:
        row = _patron_doc_to_row(d)
        row["cliente"] = d.get("cliente") or ""
        row["activo"] = int(d.get("activo") or 0)
        rows.append(row)
    return {"rows": _sort_patron_rows(rows)}


@frappe.whitelist(allow_guest=False)
def get_patron(name, version=None):
    """Resolver versionado — contrato con SI Pieza / Lechu.

    Dados (name, version), devuelve los parámetros exactos del patrón en ese momento,
    incluso si el patrón fue editado después. Garantía de reproducibilidad permanente.

    Args:
        name:    nombre del SI Patron (e.g. "Subte", "Tresbolillo")
        version: int o None. None → versión vigente. N → versión congelada N.

    r.message:
    {
        "name": "Subte",
        "version": 1,
        "tipo": "Archivo",
        "visibilidad": "Público",
        "parametros": {"step_x": 84.0, "step_y": 84.0},
        "archivo_dxf_url": "",          // URL/path del DXF; vacío para Paramétrico
        "file_available": false,
        "descripcion": ""
    }

    Error: frappe.DoesNotExistError si el patron o la versión no existen.
    """
    if not frappe.db.exists("SI Patron", name):
        frappe.throw(f"Patrón no encontrado: {name}", frappe.DoesNotExistError)

    doc = frappe.get_doc("SI Patron", name)

    if version is None:
        parametros_str = doc.parametros or "{}"
        archivo_dxf = doc.archivo_dxf or ""
        version_num = int(doc.version or 1)
    else:
        version_num = int(version)
        row = next(
            (r for r in doc.versiones if int(r.version_num or 0) == version_num),
            None,
        )
        if row is None:
            frappe.throw(
                f"Versión {version_num} no encontrada para patrón '{name}'",
                frappe.DoesNotExistError,
            )
        parametros_str = row.parametros_frozen or "{}"
        archivo_dxf = row.archivo_dxf_frozen or ""

    try:
        parametros = json.loads(parametros_str)
    except (json.JSONDecodeError, TypeError):
        parametros = {}

    try:
        file_available = bool(archivo_dxf) and Path(archivo_dxf).exists()
    except Exception:
        file_available = False

    return {
        "name": name,
        "version": version_num,
        "tipo": doc.tipo or "",
        "visibilidad": doc.visibilidad or "Público",
        "parametros": parametros,
        "archivo_dxf_url": archivo_dxf,
        "file_available": file_available,
        "descripcion": doc.descripcion or "",
        "thumbnail_url": _thumb_url(name),
    }


@frappe.whitelist(allow_guest=False)
def _save_thumbnail_cuadriculado_nativo(nombre: str, params: dict):
    """Thumbnail de un cuadriculado paramétrico con el MOTOR NATIVO.

    Genera el DXF con LegacyPanelAdapter (cuadrados o círculos tileados según
    hole_shape) usando los parámetros del patrón y lo renderiza a PNG. No usa
    archivo_dxf ni el fallback de render directo.
    """
    import tempfile
    safe = _safe_name(nombre)
    out_path = _thumb_dir() / f"{safe}.png"
    try:
        from sistema_industrial.presets.legacy_panel_adapter import (
            LegacyPanelAdapter, LegacyPanelRunRequest,
        )
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dxf = Path(tmp) / f"{safe}.dxf"
            req = LegacyPanelRunRequest(
                preset_code=f"thumb_{safe}",
                preset_name=f"thumb_{safe}",
                material="generic",
                thickness_mm=1.0,
                width_mm=300.0,
                height_mm=300.0,
                quantity=1,
                output_dxf_path=tmp_dxf,
                pattern_type="cuadriculado",
                hole_shape=params.get("hole_shape", "square"),
                hole_size_mm=float(params.get("hole_size", 10.0)),
                step_x_mm=float(params.get("step_x", 18.0)),
                step_y_mm=float(params.get("step_y", 18.0)),
                margin_mm=20.0,
                cut_partial_figures=True,
            )
            LegacyPanelAdapter().run(req)
            if not _render_dxf_to_png(tmp_dxf, out_path):
                return None
    except Exception as exc:
        frappe.log_error(f"thumbnail cuadriculado nativo {nombre}: {exc}", "thumbnail_nativo")
        return None
    return f"{_THUMBNAIL_BASE}/{safe}.png" if out_path.exists() else None


def generate_thumbnail(name):
    """Genera (o regenera) el thumbnail de un patrón. r.message: {ok, url}"""
    if not frappe.db.exists("SI Patron", name):
        frappe.throw(f"Patrón no encontrado: {name}", frappe.DoesNotExistError)
    doc = frappe.get_doc("SI Patron", name)
    try:
        params = json.loads(doc.parametros or "{}")
    except Exception:
        params = {}
    # Paramétrico cuadriculado → motor nativo (sin archivo DXF)
    if params.get("forma") == "cuadriculado":
        url = _save_thumbnail_cuadriculado_nativo(name, params)
        return {"ok": bool(url), "url": url}
    dxf_path = doc.archivo_dxf or ""
    if not dxf_path:
        return {"ok": False, "url": None, "reason": "sin archivo DXF"}
    url = _save_thumbnail(name, dxf_path, params.get("step_x"), params.get("step_y"))
    return {"ok": bool(url), "url": url}


@frappe.whitelist(allow_guest=False)
def get_thumbnail(name):
    """Devuelve la URL del thumbnail; lo genera si no existe. r.message: {url}"""
    existing = _thumb_url(name)
    if existing:
        return {"url": existing}
    result = generate_thumbnail(name)
    return {"url": result.get("url")}


@frappe.whitelist(allow_guest=False)
def backfill_thumbnails(force=False, names=None):
    """Genera thumbnails para todos (o una lista de) patrones Archivo/Vectorizado activos.

    Args:
        force: True = regenera incluso los que ya existen en disco.
        names: lista JSON de nombres, o None para todos.

    r.message: {generated: [...], skipped: [...], failed: [...]}
    """
    if names:
        if isinstance(names, str):
            names = json.loads(names)
    else:
        docs = frappe.get_all(
            "SI Patron",
            filters=[["tipo", "in", ["Archivo", "Vectorizado", "Paramétrico"]], ["activo", "=", 1]],
            fields=["name"],
        )
        names = [d["name"] for d in docs]

    generated, skipped, failed = [], [], []
    for n in names:
        if not force and _thumb_url(n):
            skipped.append(n)
            continue
        try:
            if not frappe.db.exists("SI Patron", n):
                failed.append({"name": n, "error": "no existe"})
                continue
            # generate_thumbnail enruta: paramétrico cuadriculado → motor nativo;
            # resto → tileado del archivo DXF. Paramétricos sin thumbnail (ej.
            # tresbolillo sin archivo) devuelven ok=False → se saltan sin error.
            result = generate_thumbnail(n)
            if result.get("ok"):
                generated.append(n)
            else:
                skipped.append(n)
        except Exception as exc:
            failed.append({"name": n, "error": str(exc)})

    return {"generated": generated, "skipped": skipped, "failed": failed}
