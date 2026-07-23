"""Constructor PURO del payload de un Item nuevo (sin frappe → testeable).

La orquestación (api/ocr_proveedores.confirmar) resuelve item_group/uom/supplier
contra ERPNext y delega la forma del doc acá.
"""


def item_payload_nuevo(item_code, item_name, supplier, codigo_proveedor, barcode,
                       item_group, uom) -> dict:
    """Payload de un Item nuevo con supplier_items + barcodes nativos.

    barcode/codigo_proveedor/supplier son opcionales (tablas vacías si faltan).
    item_name cae al item_code si viene vacío; se trunca a 140 (límite ERPNext).
    """
    return {
        "doctype": "Item",
        "item_code": item_code,
        "item_name": (item_name or item_code)[:140],
        "item_group": item_group,
        "stock_uom": uom,
        "supplier_items": ([{"supplier": supplier, "supplier_part_no": codigo_proveedor or ""}]
                           if supplier else []),
        "barcodes": ([{"barcode": barcode}] if barcode else []),
    }
