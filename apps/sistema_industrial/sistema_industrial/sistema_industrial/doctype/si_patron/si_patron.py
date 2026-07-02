try:
    import frappe
    from frappe.model.document import Document
except Exception:  # pragma: no cover
    frappe = None
    Document = object


class SIPatron(Document):
    def before_save(self):
        self._handle_versioning()

    def _handle_versioning(self):
        """Congela el estado actual en una fila del child si parametros o archivo_dxf cambiaron.

        La primera vez (sin versiones): crea la fila version_num=1.
        Las siguientes: compara con la última fila — si algo cambió, agrega version_num+1.
        El campo `version` del master siempre refleja la versión vigente.
        """
        if not frappe:
            return

        now = frappe.utils.now()
        current_params = (self.parametros or "").strip()
        current_dxf = (self.archivo_dxf or "").strip()

        if not self.versiones:
            # Primer save — crear versión 1
            self.version = 1
            self.append("versiones", {
                "version_num": 1,
                "fecha_congela": now,
                "parametros_frozen": current_params,
                "archivo_dxf_frozen": current_dxf,
            })
            return

        # Buscar la fila con el mayor version_num
        last_row = max(self.versiones, key=lambda r: int(r.version_num or 0))
        prev_params = (last_row.parametros_frozen or "").strip()
        prev_dxf = (last_row.archivo_dxf_frozen or "").strip()

        if current_params != prev_params or current_dxf != prev_dxf:
            new_version = int(last_row.version_num or 0) + 1
            self.version = new_version
            self.append("versiones", {
                "version_num": new_version,
                "fecha_congela": now,
                "parametros_frozen": current_params,
                "archivo_dxf_frozen": current_dxf,
            })
