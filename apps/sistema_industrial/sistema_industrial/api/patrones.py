"""Endpoints para el catálogo de patrones del panel decorativo.

URL base: /api/method/sistema_industrial.api.patrones.

Endpoints:
    get_all(customer=None)       — patrones Públicos + Exclusivos del cliente (activos)
    get_patron(name, version)    — resolver versionado (contrato con SI Pieza / Lechu)
    upload_pattern(...)          — copia DXF desde File de Frappe a /planos/, crea SI Patron
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
    }
