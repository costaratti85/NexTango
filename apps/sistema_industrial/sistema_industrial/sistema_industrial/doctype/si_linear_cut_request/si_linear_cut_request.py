try:
    from frappe.model.document import Document
except Exception:  # pragma: no cover - local non-Frappe test environment
    Document = object


class SILinearCutRequest(Document):
    pass
