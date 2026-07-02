"""Endpoints MES para piezas de producción (SI Pieza).

URL base: /api/method/sistema_industrial.api.piezas.

Endpoints:
    por_pedido(order)                       — piezas de un pedido
    por_cliente(customer)                   — piezas de un cliente
    por_material(material, espesor_mm)      — agrupar cortes por chapa
    por_matriceria(matriceria)              — pendientes de corte + pendientes de plegado con esa matríz
    marcar_cortada(name)                    — estado_corte=Cortada + fecha_corte=now (idempotente)
    marcar_plegada(name)                    — estado_plegado=Plegada + fecha_plegado=now (requiere Cortada)

Formato de respuesta:
    Consultas: {"rows": [...]}
    Acciones:  {"ok": true/false, "name": ..., ...} | {"ok": false, "error": "..."}
"""
import frappe
from frappe.utils import now_datetime


_PIEZA_LIST_FIELDS = [
    "name", "order_doctype", "order", "cliente",
    "material", "espesor_mm", "cantidad",
    "prompt", "version_patron", "matriceria",
    "estado_corte", "estado_plegado", "fecha_corte", "fecha_plegado",
]

_ROLES_CORTE = {"SI Operador Laser", "SI Admin Produccion"}
_ROLES_PLEGADO = {"SI Operador Plegado", "SI Admin Produccion"}


@frappe.whitelist(allow_guest=False)
def por_pedido(order):
    """Piezas de un pedido (SI Presupuesto Panel o SI Pedido Plegado).

    r.message: {"rows": [...]}
    """
    rows = frappe.get_all(
        "SI Pieza",
        fields=_PIEZA_LIST_FIELDS,
        filters={"order": order},
        order_by="creation asc",
    )
    return {"rows": rows}


@frappe.whitelist(allow_guest=False)
def por_cliente(customer):
    """Piezas de un cliente (todas las órdenes).

    r.message: {"rows": [...]}
    """
    rows = frappe.get_all(
        "SI Pieza",
        fields=_PIEZA_LIST_FIELDS,
        filters={"cliente": customer},
        order_by="creation desc",
        limit=500,
    )
    return {"rows": rows}


@frappe.whitelist(allow_guest=False)
def por_material(material, espesor_mm):
    """Piezas de un material y espesor dados — útil para agrupar cortes por chapa.

    r.message: {"rows": [...]}
    """
    try:
        espesor_mm = float(espesor_mm)
    except (TypeError, ValueError) as exc:
        return {"ok": False, "error": f"espesor_mm inválido: {exc}"}

    rows = frappe.get_all(
        "SI Pieza",
        fields=_PIEZA_LIST_FIELDS,
        filters={"material": material, "espesor_mm": espesor_mm},
        order_by="creation asc",
    )
    return {"rows": rows}


@frappe.whitelist(allow_guest=False)
def por_matriceria(matriceria):
    """Piezas con esa matríz que están pendientes de corte O pendientes de plegado.

    Caso de uso clave: el operador de plegado quiere todo lo que hay que procesar
    con la matríz actual antes de cambiarla. Incluye:
      - pendientes de corte (hay que cortarlas antes de plegar)
      - ya cortadas pero todavía no plegadas

    r.message:
    {
        "rows": [...],
        "pendientes_corte": N,
        "pendientes_plegado": M
    }
    """
    pending_cut = frappe.get_all(
        "SI Pieza",
        fields=_PIEZA_LIST_FIELDS,
        filters={"matriceria": matriceria, "estado_corte": "Pendiente"},
        order_by="creation asc",
    )
    pending_fold = frappe.get_all(
        "SI Pieza",
        fields=_PIEZA_LIST_FIELDS,
        filters={
            "matriceria": matriceria,
            "estado_corte": "Cortada",
            "estado_plegado": "Pendiente",
        },
        order_by="creation asc",
    )
    return {
        "rows": pending_cut + pending_fold,
        "pendientes_corte": len(pending_cut),
        "pendientes_plegado": len(pending_fold),
    }


@frappe.whitelist(allow_guest=False)
def marcar_cortada(name):
    """Marca la pieza como Cortada y registra fecha_corte.

    Roles permitidos: SI Operador Laser, SI Admin Produccion.

    Idempotente: si la pieza ya estaba Cortada devuelve ok=True con
    already_cut=True sin tocar la fecha original.

    r.message (éxito):
    {
        "ok": true,
        "name": "PZA-2026-00001",
        "fecha_corte": "2026-07-02 14:30:00.000000",
        "already_cut": false
    }

    r.message (ya estaba cortada):
    {
        "ok": true,
        "name": "PZA-2026-00001",
        "fecha_corte": "2026-07-02 12:00:00.000000",
        "already_cut": true
    }

    r.message (error):
    {
        "ok": false,
        "error": "descripción del error"
    }
    """
    if not (_ROLES_CORTE & set(frappe.get_roles())):
        return {"ok": False, "error": "Sin permisos para marcar pieza como cortada (roles requeridos: SI Operador Laser o SI Admin Produccion)"}

    if not frappe.db.exists("SI Pieza", name):
        return {"ok": False, "error": f"Pieza no encontrada: {name!r}"}

    doc = frappe.get_doc("SI Pieza", name)

    if doc.estado_corte == "Cortada":
        return {"ok": True, "name": name, "fecha_corte": str(doc.fecha_corte), "already_cut": True}

    doc.estado_corte = "Cortada"
    doc.fecha_corte = now_datetime()
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {"ok": True, "name": name, "fecha_corte": str(doc.fecha_corte), "already_cut": False}


@frappe.whitelist(allow_guest=False)
def marcar_plegada(name):
    """Marca la pieza como Plegada y registra fecha_plegado.

    Roles permitidos: SI Operador Plegado, SI Admin Produccion.

    Requiere estado_corte == 'Cortada'.
    Rechaza si estado_plegado == 'N/A' (la pieza no va a la plegadora).
    Idempotente: si ya estaba Plegada devuelve ok=True con already_folded=True
    sin tocar la fecha original.

    r.message (éxito):
    {
        "ok": true,
        "name": "PZA-2026-00001",
        "fecha_plegado": "2026-07-02 15:00:00.000000",
        "already_folded": false
    }

    r.message (ya estaba plegada):
    {
        "ok": true,
        "name": "PZA-2026-00001",
        "fecha_plegado": "2026-07-02 13:00:00.000000",
        "already_folded": true
    }

    r.message (error):
    {
        "ok": false,
        "error": "descripción del error"
    }
    """
    if not (_ROLES_PLEGADO & set(frappe.get_roles())):
        return {"ok": False, "error": "Sin permisos para marcar pieza como plegada (roles requeridos: SI Operador Plegado o SI Admin Produccion)"}

    if not frappe.db.exists("SI Pieza", name):
        return {"ok": False, "error": f"Pieza no encontrada: {name!r}"}

    doc = frappe.get_doc("SI Pieza", name)

    if doc.estado_corte != "Cortada":
        return {"ok": False, "error": f"La pieza {name!r} no está cortada (estado_corte={doc.estado_corte!r}). Cortarla antes de plegar."}

    if doc.estado_plegado == "N/A":
        return {"ok": False, "error": f"La pieza {name!r} no requiere plegado (estado_plegado=N/A)."}

    if doc.estado_plegado == "Plegada":
        return {"ok": True, "name": name, "fecha_plegado": str(doc.fecha_plegado), "already_folded": True}

    doc.estado_plegado = "Plegada"
    doc.fecha_plegado = now_datetime()
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {"ok": True, "name": name, "fecha_plegado": str(doc.fecha_plegado), "already_folded": False}
