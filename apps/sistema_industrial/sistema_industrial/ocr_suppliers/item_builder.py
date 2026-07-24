"""Constructor PURO del payload de un Item nuevo (sin frappe → testeable).

La orquestación (api/ocr_proveedores.confirmar) resuelve item_group/uom/supplier
contra ERPNext y delega la forma del doc acá.
"""


def item_payload_nuevo(item_code, item_name, supplier, codigo_proveedor, barcode,
                       item_group, uom, is_stock_item=1, si_iva_pct=None) -> dict:
    """Payload de un Item nuevo con supplier_items + barcodes nativos.

    barcode/codigo_proveedor/supplier son opcionales (tablas vacías si faltan).
    item_name cae al item_code si viene vacío; se trunca a 140 (límite ERPNext).

    is_stock_item: 1 (default) = artículo con control de stock (lo mueve la
        Recepción de Compra). Lo explicita el checkbox de la grilla (Vega); sin
        él la Purchase Receipt no movería stock (Nova/MSG_033, Forge/MSG_038).
    si_iva_pct: % de IVA del renglón (21 / 10.5 / 0 / 27 / None). Se guarda en el
        custom field Item.si_iva_pct (Forge/MSG_041) — solo si viene un valor.
        DEFENSIVO: si el campo aún no existe en el sitio, frappe lo ignora.
    """
    payload = {
        "doctype": "Item",
        "item_code": item_code,
        "item_name": (item_name or item_code)[:140],
        "item_group": item_group,
        "stock_uom": uom,
        "is_stock_item": 1 if is_stock_item else 0,
        "supplier_items": ([{"supplier": supplier, "supplier_part_no": codigo_proveedor or ""}]
                           if supplier else []),
        "barcodes": ([{"barcode": barcode}] if barcode else []),
    }
    if si_iva_pct is not None:
        payload["si_iva_pct"] = si_iva_pct
    return payload
