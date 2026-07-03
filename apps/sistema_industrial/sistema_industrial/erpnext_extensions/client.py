"""Cliente REST para ERPNext v16 — autenticación via API key/secret token."""

import logging
import os

import requests

logger = logging.getLogger(__name__)


class ERPNextClient:
    def __init__(self):
        self.base_url = os.environ.get("ERPNEXT_URL", "http://190.190.190.20").rstrip("/")
        api_key = os.environ.get("ERPNEXT_API_KEY", "")
        api_secret = os.environ.get("ERPNEXT_API_SECRET", "")
        if not api_key:
            logger.warning("ERPNEXT_API_KEY no configurado — las requests no van a autenticarse")
        self.headers = {
            "Authorization": f"token {api_key}:{api_secret}",
            "Content-Type": "application/json",
        }

    def post_quotation(self, payload: dict) -> dict:
        """POST /api/resource/Quotation → devuelve el doc creado."""
        url = f"{self.base_url}/api/resource/Quotation"
        response = requests.post(url, json=payload, headers=self.headers, timeout=30)
        if not response.ok:
            raise RuntimeError(
                f"ERPNext POST /api/resource/Quotation respondió {response.status_code}: {response.text[:300]}"
            )
        return response.json()

    def get_item(self, item_code: str) -> dict | None:
        """GET /api/resource/Item/<code> → None si no existe."""
        url = f"{self.base_url}/api/resource/Item/{item_code}"
        response = requests.get(url, headers=self.headers, timeout=10)
        if response.status_code == 404:
            return None
        if not response.ok:
            raise RuntimeError(
                f"ERPNext GET /api/resource/Item/{item_code} respondió {response.status_code}: {response.text[:300]}"
            )
        return response.json()

    def get_doc(self, doctype: str, name: str) -> dict | None:
        """GET /api/resource/<doctype>/<name> → None si no existe (404)."""
        import urllib.parse
        url = f"{self.base_url}/api/resource/{urllib.parse.quote(doctype)}/{urllib.parse.quote(name)}"
        response = requests.get(url, headers=self.headers, timeout=10)
        if response.status_code == 404:
            return None
        if not response.ok:
            raise RuntimeError(
                f"ERPNext GET {doctype}/{name} respondió {response.status_code}: {response.text[:300]}"
            )
        return response.json().get("data", response.json())

    def create_doc(self, doctype: str, doc: dict) -> dict:
        """POST /api/resource/<doctype> → devuelve el doc creado. Lanza RuntimeError en 4xx/5xx."""
        import urllib.parse
        url = f"{self.base_url}/api/resource/{urllib.parse.quote(doctype)}"
        payload = {"doctype": doctype, **doc}
        response = requests.post(url, json=payload, headers=self.headers, timeout=30)
        if not response.ok:
            raise RuntimeError(
                f"ERPNext POST {doctype} respondió {response.status_code}: {response.text[:400]}"
            )
        return response.json().get("data", response.json())

    def get_customer(self, customer_code: str) -> dict | None:
        """GET /api/resource/Customer/<code> → None si no existe."""
        return self.get_doc("Customer", customer_code)

    def update_quotation(self, name: str, payload: dict) -> dict:
        """PUT /api/resource/Quotation/<name> → actualiza un Quotation existente."""
        import urllib.parse
        url = f"{self.base_url}/api/resource/Quotation/{urllib.parse.quote(name)}"
        response = requests.put(url, json=payload, headers=self.headers, timeout=30)
        if not response.ok:
            raise RuntimeError(
                f"ERPNext PUT Quotation/{name} respondió {response.status_code}: {response.text[:300]}"
            )
        return response.json().get("data", response.json())

    def list_quotations(self, customer_code: str) -> list[dict]:
        """GET /api/resource/Quotation con filtro por party_name → lista de Quotations."""
        return self.list_docs(
            "Quotation",
            filters=[["party_name", "=", customer_code]],
            fields=["name", "status", "grand_total", "transaction_date"],
        )

    def patch_doc(self, doctype: str, name: str, data: dict) -> dict:
        """PUT /api/resource/<doctype>/<name> → actualiza campos del doc."""
        import urllib.parse
        url = f"{self.base_url}/api/resource/{urllib.parse.quote(doctype)}/{urllib.parse.quote(name)}"
        response = requests.put(url, json=data, headers=self.headers, timeout=30)
        if not response.ok:
            raise RuntimeError(
                f"ERPNext PUT {doctype}/{name} respondió {response.status_code}: {response.text[:300]}"
            )
        return response.json().get("data", response.json())

    def list_docs(
        self,
        doctype: str,
        filters: list,
        fields: list[str] | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """GET /api/resource/<doctype> con filtros → lista de docs."""
        import json as _json, urllib.parse
        params = {
            "filters": _json.dumps(filters),
            "fields": _json.dumps(fields or ["name"]),
            "limit": str(limit),
        }
        url = f"{self.base_url}/api/resource/{urllib.parse.quote(doctype)}"
        response = requests.get(url, params=params, headers=self.headers, timeout=15)
        if not response.ok:
            raise RuntimeError(
                f"ERPNext list {doctype} respondió {response.status_code}: {response.text[:300]}"
            )
        return response.json().get("data", [])

    def find_customer_by_tango_code(self, tango_code: str) -> dict | None:
        """Busca un Customer por si_tango_code. Retorna el primer resultado o None."""
        results = self.list_docs(
            "Customer",
            filters=[["si_tango_code", "=", tango_code]],
            fields=["name", "customer_name", "si_tango_code", "disabled"],
            limit=1,
        )
        return results[0] if results else None
