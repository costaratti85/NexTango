try:
    from frappe import _
except Exception:  # pragma: no cover - local non-Frappe test environment
    _ = lambda text: text


def get_data():
    return [
        {
            "module_name": "Sistema Industrial",
            "type": "module",
            "label": _("Sistema Industrial"),
        }
    ]
