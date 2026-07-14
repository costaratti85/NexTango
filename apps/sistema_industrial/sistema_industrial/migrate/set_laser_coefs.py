"""Carga los coeficientes calibrados del modelo físico de tiempo de láser
en un registro «SI Material Corte».

Modelo:  T = α·cut_mm + β·travel_mm + γ·pierce + δ   (segundos)

Los valores de abajo salieron de la calibración por mínimos cuadrados de la
BATERÍA 2 (ratios travel/cut desacoplados) medida real en CypCut, chapa N°14 /
2.0 mm, corte 75 mm/s (ver tools/calibracion_bateria2_REAL.json y MSG_110 del
canal Nova). Ajuste: R²=1.0000, error máx 0.7 %.

Validación física: α=0.01337 s/mm ≈ 1/75 = 0.01333 → coincide con la velocidad
de corte nominal (74.8 vs 75 mm/s) → modelo validado. β=0.00495 s/mm es la
velocidad EFECTIVA de desplazamiento (~202 mm/s), menor que el rápido nominal
(1650 mm/s) porque los saltos entre agujeros son cortos y nunca alcanzan la
velocidad crucero — esperado y correcto. δ≈0 (sin overhead fijo).

NO editar a mano — regenerar con tools/calibrar_laser.py si llegan nuevos datos.

Uso:
    bench --site erp.local execute \
        sistema_industrial.migrate.set_laser_coefs.run
"""

# Coeficientes calibrados — chapa N°14 (2.0 mm). Batería 2 real, modelo δ=0.
COEFS_N14_2MM = {
    "laser_a_s_per_mm": 0.013372,   # α  s/mm cortando (≈1/75mm/s, validado)
    "laser_b_s_per_hole": 0.004946,  # β  s/mm desplazándose efectivo (fieldname legacy; es travel)
    "laser_c_s_per_m2": 1.1852,      # γ  s/perforación   (fieldname legacy; es pierce)
    "laser_d_base_s": 0.0,           # δ  overhead fijo (s) — despreciable
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
