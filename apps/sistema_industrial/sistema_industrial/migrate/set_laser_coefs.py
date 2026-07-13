"""Carga los coeficientes calibrados del modelo físico de tiempo de láser
en un registro «SI Material Corte».

Modelo:  T = α·cut_mm + β·travel_mm + γ·pierce + δ   (segundos)

Los valores de abajo salieron de la calibración por mínimos cuadrados de la
batería CypCut P01–P14 (chapa N°14 / 2.0 mm), datos reales de Constantino
(ver tools/calibracion_laser_N14_2.0mm.json y MSG_094/029 del canal Nova).
Ajuste: R²=0.9999, LOO-CV error medio 1.20 %. NO editar a mano — regenerar con
tools/calibrar_laser.py si llegan nuevos datos.

Uso:
    bench --site erp.local execute \
        sistema_industrial.migrate.set_laser_coefs.run
"""

# Coeficientes calibrados — chapa N°14 (2.0 mm). Modelo conjunto 4 parámetros.
COEFS_N14_2MM = {
    "laser_a_s_per_mm": 0.006169,   # α  s/mm cortando
    "laser_b_s_per_hole": 0.010412,  # β  s/mm desplazándose (fieldname legacy; es travel)
    "laser_c_s_per_m2": 1.0516,      # γ  s/perforación   (fieldname legacy; es pierce)
    "laser_d_base_s": 9.72,          # δ  overhead fijo (s)
}

# doc_name = "{material} {espesor_mm}mm" (misma convención que migrate_materiales).
DOC_NAME = "Chapa doble decapada 2.0mm"


def run(doc_name: str = DOC_NAME, coefs: dict | None = None) -> dict:
    """Setea laser_a/b/c/d en el registro indicado. Idempotente.

    Retorna {"ok": bool, "doc": name, "aplicado": {...}, "error": str?}.
    """
    import frappe

    coefs = coefs or COEFS_N14_2MM

    if not frappe.db.exists("SI Material Corte", doc_name):
        return {
            "ok": False,
            "doc": doc_name,
            "error": (
                f"No existe 'SI Material Corte' {doc_name!r}. "
                f"Verificar el nombre exacto (formato '<material> <espesor>mm')."
            ),
        }

    doc = frappe.get_doc("SI Material Corte", doc_name)
    doc.update(coefs)
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return {"ok": True, "doc": doc_name, "aplicado": coefs}
