"""Tango boundary schemas.

These are not final Tango API payloads. They define the canonical internal shape
that Tango adapters must provide/consume.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TangoArticle:
    code: str           # COD_STA11 → ERPNext item_code
    description: str    # DESCRIPCIO → item_name / description
    barcode: str | None = None       # COD_BARRA
    uom: str = "unidad"              # UNIDAD_MEDIDA (fallback: "unidad")
    tango_id: int | None = None      # ID_STA11 — internal Tango PK (store as custom field)
    family: str | None = None        # FAMILIA → Item Group (level 1)
    group: str | None = None         # GRUPO → Item Group (level 2)
    classification: str | None = None  # CLASIFICACION → Item Group (level 3, if present)
    synonym: str | None = None       # SINONIMO → additional description / search keyword


@dataclass(frozen=True)
class TangoCustomer:
    """Maps to Tango GVA14 (clientes).

    Process ID not yet confirmed — run tools/probe_tango_clientes.py.
    Field names are best-guess from Tango Gestión conventions; verify after probe.
    """
    code: str               # COD_GVA14 → ERPNext customer_code
    name: str               # RAZON_SOCIAL / NOMBRE → customer_name
    cuit: str | None = None              # CUIT → tax_id (custom field)
    address: str | None = None           # DOMICILIO
    city: str | None = None              # LOCALIDAD
    province: str | None = None          # PROVINCIA
    postal_code: str | None = None       # COD_POST
    vat_condition: str | None = None     # CONDICION_IVA (RI, Monotributo, Exento…)
    payment_condition: str | None = None # COD_CPG / CONDICION_PAGO → Payment Terms
    email: str | None = None             # EMAIL
    phone: str | None = None             # TELEFONO
    tango_id: int | None = None          # ID_GVA14 — internal Tango PK
    credit_limit: float | None = None    # LIMITE_CRED
    is_active: bool = True               # derived from INHABILITADO != "S"


@dataclass(frozen=True)
class TangoPrice:
    item_code: str
    price: float
    currency: str = "ARS"
    list_name: str = "default"


@dataclass(frozen=True)
class TangoInvoiceLine:
    item_code: str
    quantity: float
    description: str | None = None


@dataclass(frozen=True)
class TangoFiscalDocument:
    document_id: str
    document_type: str
    customer_code: str | None
    lines: list[TangoInvoiceLine]
    is_credit_note: bool = False
