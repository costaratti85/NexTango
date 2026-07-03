try:
    import frappe
    from frappe.model.document import Document
except Exception:  # pragma: no cover
    frappe = None
    Document = object


class SIPresupuestoPanel(Document):
    def before_save(self):
        self._recalcular_total()

    def _recalcular_total(self):
        if not frappe:
            return
        precios = frappe.get_single("SI Precios Globales")
        p_laser = float(precios.precio_segundo_laser or 0)
        p_pliegue = float(precios.precio_por_plegado or 0)

        total = 0.0
        for linea in self.lineas or []:
            mat = frappe.get_doc("SI Material Corte", linea.material_corte) if linea.material_corte else None
            p_kg = float(mat.precio_por_kg or 0) if mat else 0.0
            p_plegar_kg = float(mat.precio_plegar_por_kg or 0) if mat else 0.0

            costo = (
                float(linea.peso_kg or 0) * p_kg * float(linea.factor_kg or 1)
                + float(linea.tiempo_laser_s or 0) * p_laser * float(linea.factor_laser or 1)
                + float(linea.peso_kg or 0) * p_plegar_kg * float(linea.factor_plegar_kg or 1)
                + int(linea.cantidad_plegados or 0) * p_pliegue * float(linea.factor_pliegue or 1)
            )
            linea.costo_total = round(costo, 2)
            total += costo

        descuento = float(self.descuento_pct or 0)
        if descuento:
            total = total * (1 - descuento / 100)
        self.total_ars = round(total, 2)
