"""Baja de stock: ventas de Tango (read-only) → movimientos de stock deduplicados.

Pieza PURA (sin frappe → testeable). **NO escribe**: lee ventas de Tango (Live Query,
via tango_sync) y produce movimientos normalizados + un log de auditoría, para que
la orquestación de **Atlas** arme y **submitee** el Stock Entry (auto-submit es suyo).

Dedup en dos niveles (robusto ante reprocesos):
  - **HWM** (High-Water Mark): (fecha, doc_id) del último comprobante procesado →
    solo se miran comprobantes por encima del HWM.
  - **clave** = tipo·letra·punto_venta·numero → set de claves ya procesadas
    (respaldo por si el HWM se solapa o llegan comprobantes fuera de orden).

Filtros (solo baja de mercadería fiscalmente válida):
  - **CAE autorizado**: se ignoran comprobantes sin CAE aprobado.
  - **mercadería**: solo líneas que controlan stock (`es_mercaderia`), se ignoran
    servicios/ítems no-stock.

Contrato del "documento de venta" que consume (lo provee `tango_sync` — coordinar
con Forge que el adapter Live Query mapee estos campos):
    {
      "tipo": "FAC", "letra": "A", "punto_venta": "0001", "numero": "00012345",
      "cae": "71...", "cae_autorizado": True,
      "fecha": "2026-07-23",          # ISO (yyyy-mm-dd) para el HWM
      "doc_id": "STA...",             # id interno Tango (desempate del HWM)
      "es_nota_credito": False,
      "lineas": [ {"item_code": "06-..", "cantidad": 10.0, "es_mercaderia": True}, ... ]
    }
"""
from __future__ import annotations

from sistema_industrial.stock_sync.events import StockMovement


def clave_comprobante(doc: dict) -> str:
    """Clave de dedup: tipo·letra·punto_venta·numero (normalizada)."""
    def g(k):
        return str(doc.get(k, "") or "").strip().upper()
    return f"{g('tipo')}-{g('letra')}-{g('punto_venta')}-{g('numero')}"


def _hwm_key(doc: dict) -> tuple:
    """Clave ordenable para el HWM: (fecha_iso, doc_id)."""
    return (str(doc.get("fecha", "") or ""), str(doc.get("doc_id", "") or ""))


def es_computable(doc: dict):
    """(bool, motivo) — ¿este comprobante genera baja de stock?"""
    if not doc.get("cae_autorizado"):
        return False, "sin_cae"
    lineas_merc = [ln for ln in (doc.get("lineas") or []) if ln.get("es_mercaderia")]
    if not lineas_merc:
        return False, "sin_mercaderia"
    return True, "ok"


def movimientos_de_documento(doc: dict) -> list:
    """Movimientos de stock de un comprobante (solo líneas de mercadería).
    Venta → salida (delta negativo); Nota de crédito → entrada (delta positivo)."""
    signo = 1 if doc.get("es_nota_credito") else -1
    reason = "tango_credit_note" if doc.get("es_nota_credito") else "tango_invoice"
    clave = clave_comprobante(doc)
    movs = []
    for ln in (doc.get("lineas") or []):
        if not ln.get("es_mercaderia"):
            continue
        code = str(ln.get("item_code", "") or "").strip()
        qty = float(ln.get("cantidad", 0) or 0)
        if not code or qty == 0:
            continue
        movs.append(StockMovement(
            item_code=code,
            quantity_delta=signo * abs(qty),
            reason=reason,
            source_document_id=clave,
        ))
    return movs


def procesar_ventas(docs, hwm: dict | None = None, claves_procesadas=frozenset()) -> dict:
    """Filtra + deduplica ventas y arma los movimientos de baja.

    Args:
        docs: lista de documentos de venta (ver contrato arriba).
        hwm:  {"fecha","doc_id"} del último procesado, o None (primera corrida).
        claves_procesadas: set de claves ya procesadas (respaldo del HWM).

    Returns dict:
        {
          "movimientos": [StockMovement...],       # para el Stock Entry (Atlas)
          "claves_nuevas": [clave...],             # a agregar al set persistido
          "hwm_nuevo": {"fecha","doc_id"}|None,    # nuevo HWM a persistir
          "auditoria": [ {clave, accion, motivo, fecha, doc_id, n_mov} ],
        }
    """
    hwm_key = (hwm.get("fecha", ""), hwm.get("doc_id", "")) if hwm else None
    procesadas = set(claves_procesadas)
    ordenados = sorted(docs or [], key=_hwm_key)

    movimientos, claves_nuevas, auditoria = [], [], []
    hwm_nuevo_key = hwm_key

    for doc in ordenados:
        clave = clave_comprobante(doc)
        k = _hwm_key(doc)
        entry = {"clave": clave, "fecha": doc.get("fecha"), "doc_id": doc.get("doc_id")}

        if hwm_key is not None and k <= hwm_key:
            auditoria.append({**entry, "accion": "omitido", "motivo": "bajo_hwm", "n_mov": 0})
            continue
        if clave in procesadas:
            auditoria.append({**entry, "accion": "omitido", "motivo": "duplicado", "n_mov": 0})
            continue

        ok, motivo = es_computable(doc)
        if not ok:
            auditoria.append({**entry, "accion": "omitido", "motivo": motivo, "n_mov": 0})
            # igual avanza el HWM: comprobante visto y resuelto
            if hwm_nuevo_key is None or k > hwm_nuevo_key:
                hwm_nuevo_key = k
            continue

        movs = movimientos_de_documento(doc)
        movimientos.extend(movs)
        claves_nuevas.append(clave)
        procesadas.add(clave)
        auditoria.append({**entry, "accion": "procesado",
                          "motivo": "nota_credito" if doc.get("es_nota_credito") else "venta",
                          "n_mov": len(movs)})
        if hwm_nuevo_key is None or k > hwm_nuevo_key:
            hwm_nuevo_key = k

    hwm_nuevo = ({"fecha": hwm_nuevo_key[0], "doc_id": hwm_nuevo_key[1]}
                 if hwm_nuevo_key else None)
    return {
        "movimientos": movimientos,
        "claves_nuevas": claves_nuevas,
        "hwm_nuevo": hwm_nuevo,
        "auditoria": auditoria,
    }


def stock_entry_items(movimientos) -> list:
    """Agrega los movimientos por item_code → líneas para el Stock Entry.
    Devuelve [{item_code, qty_delta}] (qty_delta neto; Atlas decide s_warehouse/
    t_warehouse según el signo y el tipo de Stock Entry)."""
    por_item = {}
    for m in movimientos:
        por_item[m.item_code] = por_item.get(m.item_code, 0.0) + m.quantity_delta
    return [{"item_code": code, "qty_delta": round(delta, 4)}
            for code, delta in por_item.items() if round(delta, 4) != 0]
