try:
    from frappe.model.document import Document
except Exception:  # pragma: no cover
    Document = object


class SILineaPresupuesto(Document):
    pass
