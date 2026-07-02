try:
    from frappe.model.document import Document
except Exception:  # pragma: no cover
    Document = object


class SIMaterialCorte(Document):
    def autoname(self):
        # El autoname "format:" de Frappe omite campos Float (solo concatena
        # strings), por lo que {espesor_mm} quedaba vacío y los nombres
        # colisionaban. Se nombra desde el controller, que tiene precedencia.
        self.name = f"{self.material} {self.espesor_mm}mm"
