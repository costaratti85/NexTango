"""Endpoints para el catálogo de patrones DXF del panel decorativo.

URL base: /api/method/sistema_industrial.api.patrones.

Endpoints:
    get_all() — lista de patrones DXF de la biblioteca (r.message.rows)
"""
import json
import re
from pathlib import Path

import frappe


_THUMBNAIL_BASE = "/assets/sistema_industrial/pattern_thumbnails"


def _safe_name(name: str) -> str:
    return re.sub(r"[^\w]", "_", name)


def _thumbnail_url(thumb_filename: str):
    """Retorna la URL Frappe si el PNG existe en public/pattern_thumbnails/, o None."""
    thumb_dir = Path(__file__).resolve().parents[1] / "public" / "pattern_thumbnails"
    p = thumb_dir / thumb_filename
    if p.exists():
        return f"{_THUMBNAIL_BASE}/{thumb_filename}"
    return None


def _find_pattern_library():
    """Ubica pattern_library.json via el dir legacy del motor."""
    try:
        from sistema_industrial.presets.legacy_panel_adapter import find_legacy_panel_dir
        p = find_legacy_panel_dir() / "pattern_library.json"
        return p if p.exists() else None
    except Exception:
        return None


@frappe.whitelist(allow_guest=False)
def get_all():
    """Lista de patrones DXF de la biblioteca para la galería del panel decorativo.

    Solo incluye patrones de tipo "dxf" de pattern_library.json. Los modos builtin
    (tresbolillo, cuadriculado, none) están hardcodeados en la page JS de Vega.

    r.message:
    {
        "rows": [
            {
                "name": "Subte",
                "label": "Subte",
                "file_path": "//190.190.190.9/.../subte.dxf",
                "step_x": 84.0,
                "step_y": 84.0,
                "thumbnail_url": "/assets/sistema_industrial/pattern_thumbnails/Subte.png",
                "file_available": false,
                "restricted": false,
                "restricted_reason": ""
            },
            ...
        ]
    }

    Notas para Vega / Forge:
    - file_available=false indica que la ruta no es accesible desde el worker de Frappe
      en el servidor (rutas UNC de Windows, paths locales Windows). El frontend debe
      mostrar estos patrones como "no disponible" (grayed-out) en la galería.
    - thumbnail_url es null si no existe la imagen en public/pattern_thumbnails/.
    - Para activar un patrón: copiar el DXF al servidor y actualizar file_path en
      pattern_library.json a una ruta Linux válida (e.g. /home/costa/patrones/Subte.dxf).
    """
    rows = []

    lib_file = _find_pattern_library()
    if lib_file is None:
        frappe.log_error("patrones.get_all: no se encontró pattern_library.json")
        return {"rows": [], "error": "pattern_library.json no encontrado"}

    try:
        library = json.loads(lib_file.read_text(encoding="utf-8"))
    except Exception as exc:
        frappe.log_error(f"patrones.get_all: error leyendo pattern_library.json: {exc}")
        return {"rows": [], "error": str(exc)}

    for name, entry in library.items():
        if entry.get("type") != "dxf":
            continue

        safe = _safe_name(name)
        file_path = str(entry.get("file_path", ""))
        file_available = bool(file_path) and Path(file_path).exists()

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
        })

    return {"rows": rows}
