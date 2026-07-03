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
    """Maps to Tango GVA14 (clientes). Process 2117 confirmed 2026-07-01.

    Field mapping (Tango → internal):
      COD_GVA14           → code
      RAZON_SOCI          → name  (NOM_COM as fallback)
      CUIT                → cuit
      DOMICILIO           → address
      LOCALIDAD           → city
      GVA18_DESCRIPCION   → province  (e.g. "Capital Federal")
      C_POSTAL            → postal_code
      COD_CATEGORIA_IVA   → vat_condition  (e.g. "CF", "RI", "MO")
      GVA01_DESC_COND     → payment_condition
      E_MAIL              → email
      TELEFONO_1          → phone
      ID_GVA14            → tango_id
      CUPO_CREDI          → credit_limit
      HABILITADO (bool)   → is_active
    """
    code: str               # COD_GVA14 → ERPNext customer_code
    name: str               # RAZON_SOCI → customer_name
    cuit: str | None = None              # CUIT → tax_id
    address: str | None = None           # DOMICILIO
    city: str | None = None              # LOCALIDAD
    province: str | None = None          # GVA18_DESCRIPCION
    postal_code: str | None = None       # C_POSTAL
    vat_condition: str | None = None     # COD_CATEGORIA_IVA (CF/RI/MO…)
    payment_condition: str | None = None # GVA01_DESC_COND
    email: str | None = None             # E_MAIL
    phone: str | None = None             # TELEFONO_1
    tango_id: int | None = None          # ID_GVA14 — internal Tango PK
    credit_limit: float | None = None    # CUPO_CREDI
    is_active: bool = True               # HABILITADO (bool)
    discount: float = 0.0               # PORC_DESC — descuento por defecto del cliente (%)


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
