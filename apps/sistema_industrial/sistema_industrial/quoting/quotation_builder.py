"""Build ERPNext-friendly quotation payloads from neutral preset quotations."""

from sistema_industrial.core.models import PresetQuotation
from sistema_industrial.pricing_sync.price_cache import PriceCache


def build_erpnext_quotation_payload(quotation: PresetQuotation, price_cache: PriceCache) -> dict:
    items = []
    for line in quotation.lines:
        unit_price = line.unit_price or price_cache.get(line.item_code)
        items.append({
            "item_code": line.item_code,
            "description": line.description,
            "qty": line.quantity,
            "uom": line.uom,
            "rate": unit_price.amount if unit_price else 0,
            "currency": unit_price.currency if unit_price else "ARS",
            "si_metadata": line.metadata,
        })

    return {
        "doctype": "Quotation",
        "party_name": quotation.customer_code,
        "si_preset_name": quotation.preset_name,
        "si_resources": [r.__dict__ for r in quotation.resources],
        "items": items,
        "si_metadata": quotation.metadata,
    }
