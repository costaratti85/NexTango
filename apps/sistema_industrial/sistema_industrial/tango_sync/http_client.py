"""Real Tango Gestión HTTP client.

Hits GET /Api/Get?process=N&pageSize=N&pageIndex=N
Headers: ApiAuthorization, Company

This module uses `requests` which is available in the Frappe/ERPNext environment.
For standalone use outside Frappe, install requests separately.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Iterator

try:
    import requests
    from requests import Session
except ImportError:  # pragma: no cover
    requests = None  # type: ignore
    Session = object  # type: ignore

from sistema_industrial.tango_sync.schemas import (
    TangoArticle,
    TangoCustomer,
    TangoPrice,
)

logger = logging.getLogger(__name__)

# Known process IDs — update TANGO_PROCESS_CLIENTES once probe confirms it
PROCESS_ARTICULOS = 87
PROCESS_CLIENTES: int | None = None  # set after probe


@dataclass
class TangoHTTPClientConfig:
    base_url: str
    token: str
    company: str = "25"
    page_size: int = 100
    timeout: int = 15
    process_articulos: int = PROCESS_ARTICULOS
    process_clientes: int | None = None


@dataclass
class TangoHTTPClient:
    """HTTP adapter for the Tango Gestión REST API."""

    config: TangoHTTPClientConfig
    _session: Any = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if requests is None:
            raise RuntimeError("requests library not available — install it or run inside Frappe")
        self._session = requests.Session()
        self._session.headers.update({
            "ApiAuthorization": self.config.token,
            "Company": self.config.company,
        })

    # ------------------------------------------------------------------
    # Low-level pagination
    # ------------------------------------------------------------------

    def _fetch_page(self, process: int, page_index: int) -> list[dict]:
        url = f"{self.config.base_url.rstrip('/')}/Api/Get"
        params = {
            "process": process,
            "pageSize": self.config.page_size,
            "pageIndex": page_index,
        }
        resp = self._session.get(url, params=params, timeout=self.config.timeout)
        resp.raise_for_status()
        data = resp.json()
        return self._extract_records(data)

    @staticmethod
    def _extract_records(data: Any) -> list[dict]:
        if isinstance(data, list):
            return data
        for key in ("data", "Data", "items", "Items", "result", "Result"):
            if key in data and isinstance(data[key], list):
                return data[key]
        return []

    def _iter_all(self, process: int) -> Iterator[dict]:
        page = 0
        while True:
            records = self._fetch_page(process, page)
            if not records:
                break
            yield from records
            if len(records) < self.config.page_size:
                break
            page += 1

    # ------------------------------------------------------------------
    # Domain-level methods
    # ------------------------------------------------------------------

    def get_articles(self) -> list[TangoArticle]:
        articles = []
        for rec in self._iter_all(self.config.process_articulos):
            try:
                articles.append(TangoArticle(
                    code=rec["COD_STA11"],
                    description=rec.get("DESCRIPCIO", ""),
                    barcode=rec.get("COD_BARRA") or None,
                    uom=rec.get("UNIDAD_MEDIDA", "unidad"),
                    tango_id=rec.get("ID_STA11"),
                    family=rec.get("FAMILIA"),
                    group=rec.get("GRUPO"),
                    classification=rec.get("CLASIFICACION"),
                    synonym=rec.get("SINONIMO"),
                ))
            except KeyError as e:
                logger.warning("Skipping article record missing field %s: %r", e, rec)
        return articles

    def get_customers(self) -> list[TangoCustomer]:
        if not self.config.process_clientes:
            raise RuntimeError(
                "process_clientes not configured. "
                "Run tools/probe_tango_clientes.py to find the correct process ID."
            )
        customers = []
        for rec in self._iter_all(self.config.process_clientes):
            try:
                customers.append(TangoCustomer(
                    code=rec.get("COD_GVA14", rec.get("CODIGO", "")),
                    name=rec.get("RAZON_SOCIAL", rec.get("NOMBRE", "")),
                    cuit=rec.get("CUIT") or None,
                    address=rec.get("DOMICILIO") or None,
                    city=rec.get("LOCALIDAD") or None,
                    province=rec.get("PROVINCIA") or None,
                    postal_code=rec.get("COD_POST") or None,
                    vat_condition=rec.get("CONDICION_IVA") or None,
                    payment_condition=rec.get("COD_CPG") or rec.get("CONDICION_PAGO") or None,
                    email=rec.get("EMAIL") or None,
                    phone=rec.get("TELEFONO") or None,
                    tango_id=rec.get("ID_GVA14"),
                    credit_limit=rec.get("LIMITE_CRED"),
                    is_active=rec.get("INHABILITADO", "N") != "S",
                ))
            except KeyError as e:
                logger.warning("Skipping customer record missing field %s: %r", e, rec)
        return customers

    def get_price_list(self, list_name: str = "default") -> list[TangoPrice]:
        # Tango price lists are typically fetched via a dedicated process or endpoint.
        # Placeholder: adapt process ID once confirmed.
        raise NotImplementedError(
            "Price list process ID not confirmed yet. "
            "Run probe_tango_clientes.py pattern against price-list processes."
        )
