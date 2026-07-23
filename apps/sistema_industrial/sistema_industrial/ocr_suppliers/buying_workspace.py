"""Sumar OCR Proveedores al workspace estándar "Buying" (Compras) de ERPNext.

Se corre en `after_migrate` (ver hooks.py): agrega — de forma ADITIVA e
IDEMPOTENTE — un link a la página `ocr-proveedores` dentro del card "Buying"
(junto a Solicitud de Materiales / Orden de compra / Factura de Compra).

Por qué after_migrate y no forkear el buying.json estándar: cada `bench migrate`
re-sincroniza el workspace estándar de ERPNext (perdería un cambio hecho a mano
en la DB). Este hook se re-aplica DESPUÉS de esa sync, así el link sobrevive a
updates de ERPNext sin overridear destructivamente el workspace. Es código en la
app → se versiona y se deploya con el código.

No reordena lo existente: inserta el link al final del card "Buying". Idempotente.
"""
import frappe

_OCR_LINK = {
    "type": "Link",
    "label": "OCR Proveedores",
    "link_type": "Page",
    "link_to": "ocr-proveedores",
    "onboard": 0,
    "is_query_report": 0,
}


def add_ocr_link_to_buying():
    """Idempotente: agrega el link a ocr-proveedores en el card 'Buying' de Compras."""
    if not frappe.db.exists("Workspace", "Buying"):
        return
    ws = frappe.get_doc("Workspace", "Buying")
    if any((l.type == "Link" and l.link_to == "ocr-proveedores") for l in ws.links):
        return  # ya presente

    new = ws.append("links", dict(_OCR_LINK))
    rest = [r for r in ws.links if r is not new]

    # posición: al final del card "Buying" (justo antes del próximo Card Break).
    pos, seen_buying = len(rest), False
    for i, r in enumerate(rest):
        if r.type == "Card Break":
            if r.label == "Buying":
                seen_buying = True
            elif seen_buying:
                pos = i
                break

    desired = rest[:pos] + [new] + rest[pos:]
    # El save del Workspace respeta el orden solo si la LISTA se reordena Y el
    # idx queda explícito (probado en el server): hay que hacer ambas cosas.
    for i, r in enumerate(desired, start=1):
        r.idx = i
    ws.set("links", desired)
    ws.flags.ignore_links = True
    ws.save(ignore_permissions=True)
    frappe.db.commit()
