import json

try:
    import frappe
    from frappe.model.document import Document
except Exception:  # pragma: no cover - entorno local sin Frappe
    frappe = None
    Document = object


class SIPieza(Document):
    def validate(self):
        self._validate_prompt_json()
        self._validate_estado_plegado_consistencia()

    def _validate_prompt_json(self):
        if not self.prompt:
            return
        try:
            data = json.loads(self.prompt)
        except (json.JSONDecodeError, TypeError):
            frappe.throw("El campo 'Prompt (JSON)' debe contener JSON válido.")
            return
        tipo = data.get("tipo")
        if tipo not in ("patron", "parametrico", "archivo", None):
            frappe.throw(
                f"Tipo de prompt desconocido: {tipo!r}. "
                "Valores aceptados: 'patron', 'parametrico', 'archivo'."
            )
        if tipo == "patron":
            # Contrato de Punto (MSG_002): campos patron_name + patron_version
            if not data.get("patron_name"):
                frappe.throw("Prompt tipo 'patron': se requiere el campo 'patron_name' (nombre del SI Patron).")
            if "patron_version" not in data:
                frappe.throw("Prompt tipo 'patron': se requiere el campo 'patron_version' para garantizar reproducibilidad.")

    def _validate_estado_plegado_consistencia(self):
        if not self.matriceria and self.estado_plegado not in ("N/A", None, ""):
            frappe.throw(
                "Sin matríz de plegado, el estado de plegado debe ser 'N/A'. "
                "Completá el campo 'Matríz de plegado' antes de asignar un estado de plegado."
            )
        if self.matriceria and self.estado_plegado == "N/A":
            frappe.throw(
                "La pieza tiene matríz de plegado pero su estado de plegado es 'N/A'. "
                "Cambiá el estado a 'Pendiente' si va a plegarse."
            )
