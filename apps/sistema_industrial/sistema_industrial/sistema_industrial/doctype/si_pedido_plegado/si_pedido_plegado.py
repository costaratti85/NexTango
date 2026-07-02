import sys
from pathlib import Path

try:
    import frappe
    from frappe.model.document import Document
except Exception:  # pragma: no cover
    frappe = None
    Document = object

_PLEGADOS_DIR = Path(__file__).resolve().parents[6] / "Programas_hechos" / "Plegados"


def _load_bandeja():
    plegados_path = str(_PLEGADOS_DIR)
    inserted = plegados_path not in sys.path
    if inserted:
        sys.path.insert(0, plegados_path)
    try:
        from bandeja import calcular_bandeja, calcular_recursos_bandeja  # type: ignore
        return calcular_bandeja, calcular_recursos_bandeja
    finally:
        if inserted and plegados_path in sys.path:
            sys.path.remove(plegados_path)


class SIPedidoPlegado(Document):
    def before_save(self):
        self._recalcular_recursos()
        self._recalcular_costo()

    def _recalcular_recursos(self):
        if not (frappe and self.material_corte and self.ancho_int
                and self.largo_int and self.alto and self.espesor):
            return
        try:
            mat = frappe.get_doc("SI Material Corte", self.material_corte)
            material_row = {
                "densidad_kg_m2": float(mat.densidad_kg_m2 or 0),
                "velocidad_corte_mm_s": float(mat.velocidad_corte_mm_s or 0),
            }
            calcular_bandeja, calcular_recursos_bandeja = _load_bandeja()
            geom = calcular_bandeja(
                float(self.ancho_int), float(self.largo_int),
                float(self.alto), float(self.espesor)
            )
            rec = calcular_recursos_bandeja(
                float(self.ancho_int), float(self.largo_int),
                float(self.alto), float(self.espesor), material_row
            )
            self.blank_ancho = geom["blank_ancho"]
            self.blank_largo = geom["blank_largo"]
            self.despunte = geom["despunte"]
            self.peso_kg = rec["kg_chapa"]
            self.tiempo_laser_s = rec["tiempo_laser_s"]
            self.cantidad_pliegues = rec["plegados"]
        except Exception as exc:
            if frappe:
                frappe.log_error(f"SI Pedido Plegado._recalcular_recursos: {exc}")

    def _recalcular_costo(self):
        if not frappe:
            return
        try:
            precios = frappe.get_single("SI Precios Globales")
            p_laser = float(precios.precio_segundo_laser or 0)
            p_pliegue = float(precios.precio_por_plegado or 0)

            mat = frappe.get_doc("SI Material Corte", self.material_corte) if self.material_corte else None
            p_kg = float(mat.precio_por_kg or 0) if mat else 0.0
            p_plegar_kg = float(mat.precio_plegar_por_kg or 0) if mat else 0.0

            self.costo_total = round(
                float(self.peso_kg or 0) * p_kg * float(self.factor_kg or 1)
                + float(self.tiempo_laser_s or 0) * p_laser * float(self.factor_laser or 1)
                + float(self.peso_kg or 0) * p_plegar_kg * float(self.factor_plegar_kg or 1)
                + int(self.cantidad_pliegues or 0) * p_pliegue * float(self.factor_pliegue or 1),
                2
            )
        except Exception as exc:
            if frappe:
                frappe.log_error(f"SI Pedido Plegado._recalcular_costo: {exc}")
