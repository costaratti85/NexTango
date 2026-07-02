"""Endpoints para el catálogo de patrones del panel decorativo.

URL base: /api/method/sistema_industrial.api.patrones.

Endpoints:
    get_all(customer=None)       — lista patrones Públicos + Exclusivos del cliente
    get_patron(name, version)    — resolver versionado (contrato con SI Pieza / Lechu)
    upload_pattern(...)          — sube DXF y crea/actualiza SI Patron
    delete_pattern(name)         — baja lógica del doc (archivo queda en disco)
"""
import base64
import json
import os
import re
from pathlib import Path

import frappe


_THUMBNAIL_BASE = "/assets/sistema_industrial/pattern_thumbnails"


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


def _thumbnail_url(filename):
    """Retorna la URL Frappe si el PNG existe en public/pattern_thumbnails/, o None."""
    thumb_dir = Path(__file__).resolve().parents[1] / "public" / "pattern_thumbnails"
    p = thumb_dir / filename
    return f"{_THUMBNAIL_BASE}/{filename}" if p.exists() else None


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

    if tipo == "Archivo":
        file_path = str(doc.get("archivo_dxf") or "")
        # Frappe Attach stores URLs like /files/... or full paths; check existence via Path
        try:
            file_available = bool(file_path) and Path(file_path).exists()
        except Exception:
            file_available = False
    else:
        # Paramétrico — siempre disponible (el motor lo genera sin DXF externo)
        file_path = ""
        file_available = True

    # Thumbnail: campo Attach del doc tiene precedencia; fallback a public/pattern_thumbnails/
    thumb = doc.get("thumbnail") or _thumbnail_url(f"{_safe_name(name)}.png")

    return {
        "name": name,
        "label": name,
        "file_path": file_path,
        "step_x": step_x,
        "step_y": step_y,
        "thumbnail_url": thumb,
        "file_available": file_available,
        "restricted": False,
        "restricted_reason": "",
        "tipo": tipo,
        "visibilidad": visibilidad,
        "version": version,
        "parametros": parametros,
    }


def _get_all_from_frappe(customer=None):
    """Retorna lista de filas desde SI Patron, o None si el doctype está vacío."""
    try:
        total = frappe.db.count("SI Patron")
        if not total:
            return None  # trigger fallback a legacy_json

        fields = [
            "name", "tipo", "visibilidad", "cliente",
            "archivo_dxf", "parametros", "version", "thumbnail", "descripcion",
        ]

        public_rows = frappe.get_all(
            "SI Patron",
            filters={"visibilidad": "Público"},
            fields=fields,
        )

        exclusive_rows = []
        if customer:
            exclusive_rows = frappe.get_all(
                "SI Patron",
                filters={"visibilidad": "Exclusivo", "cliente": customer},
                fields=fields,
            )

        rows = [_patron_doc_to_row(d) for d in public_rows + exclusive_rows]
        rows.sort(key=lambda r: r["name"])
        return rows
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
        safe = _safe_name(name)
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
            "thumbnail_url": _thumbnail_url(f"{safe}.png"),
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
        })
    return rows


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
                "thumbnail_url": "/assets/sistema_industrial/pattern_thumbnails/Subte.png",
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
    - Compatibilidad con MSG_047 de Vega: los campos name/file_path/step_x/step_y/
      thumbnail_url/file_available/restricted/restricted_reason se mantienen intactos.
    """
    frappe_rows = _get_all_from_frappe(customer)
    if frappe_rows is not None:
        return {"rows": frappe_rows, "source": "frappe"}

    return {"rows": _get_all_from_legacy(), "source": "legacy_json"}


@frappe.whitelist(allow_guest=False)
def upload_pattern(name, file_b64, filename, visibilidad, step_x=None, step_y=None, customer=None, descripcion=""):
    """Sube un DXF y crea o actualiza el SI Patron correspondiente.

    El archivo se guarda en:
        Público   → <planos_root>/generico/patrones/<filename>
        Exclusivo → <planos_root>/<customer>/patrones/<filename>

    Si el patrón ya existe, el archivo nuevo recibe sufijo de versión (_v2, _v3…)
    para no pisar el historial.

    r.message: {ok, name, version, path, file_available}
    """
    if visibilidad == "Exclusivo" and not customer:
        frappe.throw("customer es requerido para visibilidad Exclusivo")

    dest_dir = _patron_dest_dir(visibilidad, customer)
    dest_dir.mkdir(parents=True, exist_ok=True)

    safe = _safe_filename(filename)

    if frappe.db.exists("SI Patron", name):
        existing = frappe.get_doc("SI Patron", name)
        next_v = int(existing.version or 1) + 1
        stem, ext = os.path.splitext(safe)
        safe = f"{stem}_v{next_v}{ext}"

    dest_path = dest_dir / safe
    dest_path.write_bytes(base64.b64decode(file_b64))

    parametros = json.dumps({
        "step_x": float(step_x) if step_x not in (None, "") else None,
        "step_y": float(step_y) if step_y not in (None, "") else None,
    }, ensure_ascii=False)

    if frappe.db.exists("SI Patron", name):
        doc = frappe.get_doc("SI Patron", name)
        doc.archivo_dxf = str(dest_path)
        doc.visibilidad = visibilidad
        doc.cliente = customer if visibilidad == "Exclusivo" else ""
        if descripcion:
            doc.descripcion = descripcion
        doc.parametros = parametros
        doc.save(ignore_permissions=True)
    else:
        payload = {
            "doctype": "SI Patron",
            "name": name,
            "tipo": "Archivo",
            "visibilidad": visibilidad,
            "descripcion": descripcion or "",
            "archivo_dxf": str(dest_path),
            "parametros": parametros,
        }
        if visibilidad == "Exclusivo" and customer:
            payload["cliente"] = customer
        doc = frappe.get_doc(payload)
        doc.insert(ignore_permissions=True)

    frappe.db.commit()
    return {
        "ok": True,
        "name": name,
        "version": int(doc.version or 1),
        "path": str(dest_path),
        "file_available": dest_path.exists(),
    }


@frappe.whitelist(allow_guest=False)
def delete_pattern(name):
    """Baja lógica de un SI Patron. El archivo DXF NO se borra del disco.

    r.message: {ok: true, name: "Subte"}
    Error: frappe.DoesNotExistError si el patrón no existe.
    """
    if not frappe.db.exists("SI Patron", name):
        frappe.throw(f"Patrón '{name}' no encontrado", frappe.DoesNotExistError)
    frappe.delete_doc("SI Patron", name, ignore_permissions=True)
    frappe.db.commit()
    return {"ok": True, "name": name}


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
        "thumbnail_url": "/assets/sistema_industrial/pattern_thumbnails/Subte.png",
        "descripcion": ""
    }

    Error: frappe.DoesNotExistError si el patron o la versión no existen.
    """
    if not frappe.db.exists("SI Patron", name):
        frappe.throw(f"Patrón no encontrado: {name}", frappe.DoesNotExistError)

    doc = frappe.get_doc("SI Patron", name)

    if version is None:
        # Versión vigente — datos del master
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

    thumb = doc.thumbnail or _thumbnail_url(f"{_safe_name(name)}.png")

    return {
        "name": name,
        "version": version_num,
        "tipo": doc.tipo or "",
        "visibilidad": doc.visibilidad or "Público",
        "parametros": parametros,
        "archivo_dxf_url": archivo_dxf,
        "file_available": file_available,
        "thumbnail_url": thumb,
        "descripcion": doc.descripcion or "",
    }
