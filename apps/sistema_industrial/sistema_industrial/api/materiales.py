"""API de materiales de corte — desbloquea los dropdowns de Vega.

Endpoints:
    get_all()           → lista completa de materiales activos
    add(data)           → crea un SI Material Corte
    update(name, data)  → actualiza campos de un material
    delete(name)        → desactiva (no borra) un material
    load_defaults()     → reimporta material_table.json al doctype
    get_precios()       → devuelve SI Precios Globales
    save_precios(data)  → actualiza SI Precios Globales
"""
import json

try:
    import frappe
except ImportError:  # pragma: no cover
    frappe = None


_MATERIAL_FIELDS = [
    "name", "material", "familia", "calibre", "espesor_mm",
    "densidad_kg_m2", "velocidad_corte_mm_s",
    "tiempo_perforacion_s", "consumible_por_perforacion",
    "precio_por_kg", "precio_plegar_por_kg", "activo",
]


@frappe.whitelist(allow_guest=False)
def get_all():
    """Devuelve la lista de materiales activos.

    Fuente primaria: doctype SI Material Corte.
    Fallback: material_table.json legacy si el doctype está vacío.

    Formato de r.message para el frontend:
    {
        "rows": [
            {
                "name": "Chapa doble decapada 0.56mm",
                "material": "Chapa doble decapada",
                "familia": "hierro",
                "calibre": "24",
                "espesor_mm": 0.56,
                "densidad_kg_m2": 4.48,
                "velocidad_corte_mm_s": 180.0,
                "tiempo_perforacion_s": 0.1,
                "consumible_por_perforacion": 0.0,
                "precio_por_kg": 8804.0,
                "precio_plegar_por_kg": 0.0,
                "activo": 1
            }, ...
        ],
        "source": "frappe"  # o "legacy_json"
    }
    """
    rows = frappe.get_all(
        "SI Material Corte",
        fields=_MATERIAL_FIELDS,
        filters={"activo": 1},
        order_by="material asc, espesor_mm asc",
    )
    if rows:
        return {"rows": [dict(r) for r in rows], "source": "frappe"}

    # Fallback al JSON legacy si el doctype aún no fue migrado
    return _fallback_legacy()


def _fallback_legacy():
    try:
        from sistema_industrial.presets.legacy_panel_adapter import find_legacy_panel_dir
        mat_file = find_legacy_panel_dir() / "material_table.json"
        if mat_file.exists():
            rows = json.loads(mat_file.read_text(encoding="utf-8"))
            return {"rows": rows, "source": "legacy_json"}
    except Exception:
        pass
    return {"rows": [], "source": "empty"}


@frappe.whitelist(allow_guest=False)
def add(data):
    """Crea un nuevo SI Material Corte.

    data: dict JSON con campos del doctype.
    """
    if isinstance(data, str):
        data = json.loads(data)
    doc = frappe.get_doc({"doctype": "SI Material Corte", **data})
    doc.insert()
    frappe.db.commit()
    return {"name": doc.name}


@frappe.whitelist(allow_guest=False)
def update(name, data):
    """Actualiza campos de un SI Material Corte existente."""
    if isinstance(data, str):
        data = json.loads(data)
    doc = frappe.get_doc("SI Material Corte", name)
    doc.update(data)
    doc.save()
    frappe.db.commit()
    return {"name": doc.name}


@frappe.whitelist(allow_guest=False)
def delete(name):
    """Desactiva (no borra) un material. La baja lógica preserva historiales."""
    doc = frappe.get_doc("SI Material Corte", name)
    doc.activo = 0
    doc.save()
    frappe.db.commit()
    return {"deleted": name}


@frappe.whitelist(allow_guest=False)
def load_defaults():
    """Reimporta material_table.json al doctype (idempotente, actualiza si ya existe)."""
    from sistema_industrial.migrate.migrate_materiales import run as _run
    result = _run(overwrite=True)
    return result


@frappe.whitelist(allow_guest=False)
def get_precios():
    """Devuelve los precios globales escalares (SI Precios Globales).

    r.message:
    {
        "precio_segundo_laser": 60.0,
        "precio_por_plegado": 0.0
    }
    """
    try:
        doc = frappe.get_single("SI Precios Globales")
        return {
            "precio_segundo_laser": float(doc.precio_segundo_laser or 0),
            "precio_por_plegado": float(doc.precio_por_plegado or 0),
        }
    except Exception:
        return {"precio_segundo_laser": 0.0, "precio_por_plegado": 0.0}


@frappe.whitelist(allow_guest=False)
def save_precios(data):
    """Actualiza SI Precios Globales.

    data: {"precio_segundo_laser": X, "precio_por_plegado": Y}
    """
    if isinstance(data, str):
        data = json.loads(data)
    doc = frappe.get_single("SI Precios Globales")
    if "precio_segundo_laser" in data:
        doc.precio_segundo_laser = float(data["precio_segundo_laser"])
    if "precio_por_plegado" in data:
        doc.precio_por_plegado = float(data["precio_por_plegado"])
    doc.save()
    frappe.db.commit()
    return {"ok": True}
