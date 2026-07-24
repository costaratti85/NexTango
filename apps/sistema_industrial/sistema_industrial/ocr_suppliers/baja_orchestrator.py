"""Orquestador de la baja de stock por ventas de Tango (Fase T5, parte de Atlas).

Ata la lectura de ventas de OCR con la escritura de stock de ERPNext. OCR
(`stock_sync.tango_ventas.ejecutar_baja`) lee ventas por Live Query (read-only),
**filtra CAE autorizado + mercadería** y dedupea por HWM `(fecha,doc_id)` + clave
`tipo-letra-pv-numero`. Acá (Atlas) hacemos la parte de escritura/estado:

  1. Persistimos el HWM + el set de claves procesadas (estado durable) y se los
     pasamos a OCR en la próxima corrida.
  2. Armamos y (con el gate ON) submiteamos el Stock Entry por comprobante:
     salida (venta) → Material Issue; entrada (nota de crédito) → Material Receipt.
     Cada Stock Entry lleva `tango_comprobante_ref` = clave (índice único) → dedup
     férreo capa 2 (nunca descontar dos veces), además del HWM de OCR (capa 1).
  3. Persistimos la auditoría (log).
  4. Corremos periódico por `scheduler_events` (hook), idempotente por el dedup.

CERO escritura a Tango (todo lectura de Tango + escritura ERPNext). El gate de
auto-submit (`ocr_baja_auto_submit`) y la company con cuenta de inventario
(`ocr_default_company`) son requisitos para que MUEVA stock; si no, degrada.

SEAM: si el lector de OCR o el cliente de Tango no están deployados, no rompe:
devuelve un estado 'pendiente' claro.
"""
from __future__ import annotations

import json

import frappe

from sistema_industrial.ocr_suppliers.baja_stock import (
    _construir_baja, _source_warehouse, _company_puede_postear_stock,
    auto_submit_habilitado,
)

_STATE_KEY = "ocr_baja_state"      # estado durable (tabDefaultValue global)
_CLAVES_MAX = 5000                 # cota del set persistido (el HWM acota el barrido)
_LOG = "ocr_baja"


# --------------------------------------------------------------- estado durable

def cargar_estado() -> dict:
    """{hwm: {fecha, doc_id}|None, claves: [...]}. Durable, sobrevive restart."""
    raw = frappe.db.get_default(_STATE_KEY)
    if raw:
        try:
            st = json.loads(raw)
            return {"hwm": st.get("hwm"), "claves": st.get("claves") or []}
        except (ValueError, TypeError):
            pass
    return {"hwm": None, "claves": []}


def guardar_estado(hwm, claves) -> None:
    claves = list(dict.fromkeys(claves or []))[-_CLAVES_MAX:]  # dedup + cota
    frappe.db.set_default(_STATE_KEY, json.dumps({"hwm": hwm, "claves": claves},
                                                 ensure_ascii=False))
    frappe.db.commit()


# --------------------------------------------------------------- seams OCR/Tango

def _mov_attr(m, name, default=None):
    """StockMovement puede venir como dict o como objeto/dataclass."""
    if isinstance(m, dict):
        return m.get(name, default)
    return getattr(m, name, default)


def _leer_ventas(process, hwm, claves):
    """SEAM con OCR (stock_sync.tango_ventas.ejecutar_baja) + cliente Tango.
    Devuelve el dict de OCR o None si el lector/cliente no está deployado."""
    try:
        from sistema_industrial.stock_sync.tango_ventas import ejecutar_baja
    except (ImportError, NotImplementedError):
        return None
    try:
        from sistema_industrial.tango_sync.client import get_client  # cliente read-only
        client = get_client()
    except Exception:
        client = None
    if client is None:
        return None
    return ejecutar_baja(client, hwm=hwm, claves_procesadas=set(claves), process=process)


# --------------------------------------------------------------- orquestación

def procesar_baja_ventas(process: str = None) -> dict:
    """Corre una pasada de la baja: lee ventas (OCR), arma/submitea los Stock Entry
    por comprobante, persiste HWM+claves y la auditoría. Idempotente por el dedup.

    Devuelve {status, procesados, submitted, skipped, errores, hwm, detalle:[...]}.
    """
    estado = cargar_estado()
    resultado = _leer_ventas(process, estado.get("hwm"), estado.get("claves"))
    if resultado is None:
        return {"status": "pendiente_ocr_o_tango",
                "motivo": "el lector de ventas de OCR (stock_sync.tango_ventas) o el "
                          "cliente de Tango todavía no están disponibles/deployados.",
                "hwm": estado.get("hwm")}

    movimientos = resultado.get("movimientos") or []
    claves_nuevas = resultado.get("claves_nuevas") or []
    hwm_nuevo = resultado.get("hwm_nuevo") or estado.get("hwm")
    auditoria = resultado.get("auditoria") or []

    # doc_id -> clave (para poner el tango_comprobante_ref por comprobante).
    doc2clave = {}
    for a in auditoria:
        did, clave = a.get("doc_id"), a.get("clave")
        if did is not None and clave:
            doc2clave[str(did)] = clave

    # Agrupar movimientos por comprobante (source_document_id) y netear por ítem.
    grupos: dict = {}
    for m in movimientos:
        did = str(_mov_attr(m, "source_document_id", ""))
        it = _mov_attr(m, "item_code")
        delta = float(_mov_attr(m, "quantity_delta", 0) or 0)
        if not it or delta == 0:
            continue
        g = grupos.setdefault(did, {})
        g[it] = g.get(it, 0.0) + delta

    comp_c, wh = _source_warehouse()  # company + depósito (misma resolución que el stock-in)
    detalle, n_sub, n_skip, n_err = [], 0, 0, 0

    for did, items_delta in grupos.items():
        clave = doc2clave.get(did) or did
        # Homogéneo por comprobante: venta = deltas negativos (salida); NC = positivos.
        salida = [{"item_code": k, "qty": -v} for k, v in items_delta.items() if v < 0]
        entrada = [{"item_code": k, "qty": v} for k, v in items_delta.items() if v > 0]
        if salida and entrada:
            frappe.logger(_LOG).warning(
                {"evento": "baja_comprobante_mixto", "clave": clave,
                 "nota": "comprobante con signos mixtos; se arma un Stock Entry por signo "
                         "pero comparten clave (índice único) → revisar con OCR"})
        for items, etype in ((salida, "Material Issue"), (entrada, "Material Receipt")):
            if not items:
                continue
            if not wh:
                r = {"ok": False, "skipped": True, "ref": clave,
                     "motivo": "sin depósito (ocr_default_warehouse)"}
            elif auto_submit_habilitado() and not _company_puede_postear_stock(comp_c, wh):
                r = {"ok": False, "skipped": True, "ref": clave,
                     "motivo": f"company '{comp_c}' sin cuenta de inventario (ocr_default_company)"}
            else:
                r = _construir_baja(clave, items, comp_c, wh, etype)
            detalle.append({"clave": clave, "entry_type": etype, **r})
            if r.get("submitted"):
                n_sub += 1
            elif r.get("skipped"):
                n_skip += 1
            elif not r.get("ok"):
                n_err += 1

    # Persistir estado (HWM + claves acumuladas) SOLO tras procesar.
    guardar_estado(hwm_nuevo, list(estado.get("claves", [])) + list(claves_nuevas))

    # Auditoría estructurada (la de OCR + el resultado de escritura).
    frappe.logger(_LOG).info({"evento": "baja_corrida", "process": process,
                              "comprobantes": len(grupos), "submitted": n_sub,
                              "skipped": n_skip, "errores": n_err, "hwm": hwm_nuevo})

    return {"status": "ok", "procesados": len(grupos), "submitted": n_sub,
            "skipped": n_skip, "errores": n_err, "hwm": hwm_nuevo, "detalle": detalle}


@frappe.whitelist()
def procesar_baja_ventas_api(process: str = None) -> dict:
    """Wrapper whitelisted (UI/diagnóstico). Respeta el gate: si `ocr_baja_auto_submit`
    está OFF, arma en borrador y no descuenta."""
    return procesar_baja_ventas(process=process)


def scheduled_baja_ventas() -> None:
    """Entry point del scheduler (hook `scheduler_events`). Read-only sobre Tango,
    idempotente por el dedup.

    DORMIDO mientras el gate `ocr_baja_auto_submit` esté OFF: no procesa nada (evita
    generar borradores en masa antes de que la baja esté habilitada). Se despierta
    solo cuando Constantino/Nova prenden el gate tras el smoke duro."""
    if not auto_submit_habilitado():
        return
    try:
        res = procesar_baja_ventas()
        if res.get("status") == "ok" and (res.get("submitted") or res.get("errores")):
            frappe.logger(_LOG).info({"evento": "baja_scheduled", **{
                k: res[k] for k in ("procesados", "submitted", "skipped", "errores")}})
    except Exception as exc:
        frappe.log_error(f"scheduled_baja_ventas: {exc}", _LOG)
