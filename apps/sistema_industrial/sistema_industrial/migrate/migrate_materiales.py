"""Script de migración: material_table.json + daily_prices.json → Frappe doctypes.

Uso:
    bench --site erp.local execute \
        sistema_industrial.migrate.migrate_materiales.run

También es llamado por api/materiales.load_defaults().
"""
import json
from pathlib import Path


_FAMILIA_MAP = {
    "hierro": "precio_kg_doble_decapada",
    "galvanizada": "precio_kg_galvanizado",
    "inox430": "precio_kg_inoxidable_430",
    "inox304": "precio_kg_inoxidable_304",
}


def run(overwrite: bool = False) -> dict:
    """Migra material_table.json y daily_prices.json al doctype Frappe.

    overwrite=True: actualiza registros existentes (idempotente).
    overwrite=False: solo inserta los que no existen.

    Retorna: {"inserted": N, "updated": M, "skipped": K, "errors": [...]}
    """
    import frappe

    mat_file, daily_file = _find_source_files()
    if mat_file is None:
        return {"error": "No se encontró material_table.json. Verificar nextango_engine_path."}

    mat_rows = json.loads(mat_file.read_text(encoding="utf-8"))
    daily = json.loads(daily_file.read_text(encoding="utf-8")) if daily_file and daily_file.exists() else {}

    # Precios por familia desde daily_prices.json
    precio_kg_por_familia = {
        familia: float(daily.get(key, 0))
        for familia, key in _FAMILIA_MAP.items()
    }

    inserted = updated = skipped = 0
    errors = []

    for row in mat_rows:
        try:
            doc_name = f"{row['material']} {row['espesor_mm']}mm"
            familia = str(row.get("familia", "")).strip()
            precio_kg = precio_kg_por_familia.get(familia, 0.0)

            fields = {
                "material": str(row["material"]).strip(),
                "familia": familia,
                "calibre": str(row.get("calibre", "-")).strip() or "-",
                "espesor_mm": float(row["espesor_mm"]),
                "densidad_kg_m2": float(row["densidad_kg_m2"]),
                "velocidad_corte_mm_s": float(row["velocidad_corte_mm_s"]),
                "tiempo_perforacion_s": float(row.get("tiempo_perforacion_s", 0)),
                "consumible_por_perforacion": float(row.get("consumible_por_perforacion", 0)),
                "precio_por_kg": precio_kg,
                "precio_plegar_por_kg": 0.0,
                "activo": 1,
            }

            if frappe.db.exists("SI Material Corte", doc_name):
                if overwrite:
                    doc = frappe.get_doc("SI Material Corte", doc_name)
                    doc.update(fields)
                    doc.save(ignore_permissions=True)
                    updated += 1
                else:
                    skipped += 1
            else:
                doc = frappe.get_doc({"doctype": "SI Material Corte", **fields})
                doc.insert(ignore_permissions=True)
                inserted += 1

        except Exception as exc:
            errors.append({"row": row.get("material", "?"), "error": str(exc)})

    # Migrar precios escalares a SI Precios Globales
    if daily:
        try:
            pg = frappe.get_single("SI Precios Globales")
            pg.precio_segundo_laser = float(daily.get("precio_segundo_maquina", 0))
            pg.precio_por_plegado = 0.0
            pg.save(ignore_permissions=True)
        except Exception as exc:
            errors.append({"row": "SI Precios Globales", "error": str(exc)})

    frappe.db.commit()

    return {
        "inserted": inserted,
        "updated": updated,
        "skipped": skipped,
        "errors": errors,
    }


def _find_source_files():
    """Busca material_table.json usando la misma lógica que legacy_panel_adapter."""
    try:
        from sistema_industrial.presets.legacy_panel_adapter import find_legacy_panel_dir
        legacy_dir = find_legacy_panel_dir()
        mat_file = legacy_dir / "material_table.json"
        daily_file = legacy_dir / "daily_prices.json"
        return mat_file if mat_file.exists() else None, daily_file
    except Exception:
        return None, None
