"""Baja de stock — lectura REAL de ventas de Tango por Live Query (read-only).

Conecta el Live Query de Tango (`tango_sync.http_client`, endpoint `/Api/Get?process=N`,
autenticado con `APP_INSTANCE_ID`) con la lógica pura de `baja.py`:

    registros crudos de Tango  →  map/agrupa por comprobante  →  baja.procesar_ventas
      →  {movimientos, claves_nuevas, hwm_nuevo, auditoria}

**CERO escritura a Tango** (solo lectura de ventas). El Stock Entry (Material Issue,
auto-submit) lo arma/submitea Atlas con `movimientos`.

Diseño desacoplado: el FETCH (que toca Tango) se inyecta; el mapeo/agrupación/filtro
es PURO y testeable sin red.

⚠️ A CONFIRMAR con Forge/Atlas (tienen acceso a Tango; probaron conectividad en T3):
  - **PROCESS_VENTAS_STOCK**: el process ID del Live Query de movimientos de stock por
    ventas (art. 87=artículos, 2117=clientes; el de stock/ventas NO está confirmado;
    la MVP standalone usaba 12567 con `GetApiLiveQueryData`).
  - **Nombres de columna** del registro (abajo, `_G(...)` tolera varias variantes).
    En especial que el registro traiga **CAE** (para el filtro de autorizado).
"""
from __future__ import annotations

import os
import re

from sistema_industrial.stock_sync import baja

# process ID del Live Query de ventas/stock — override por env hasta confirmarlo.
PROCESS_VENTAS_STOCK = int(os.environ.get("TANGO_PROCESS_VENTAS", "0")) or None


def _G(rec: dict, *claves, default=None):
    """Primer valor no vacío entre varias claves posibles (tolera nombres Tango)."""
    for k in claves:
        if k in rec and rec[k] not in (None, ""):
            return rec[k]
    return default


def _to_float(v):
    try:
        return float(str(v).replace(",", "."))
    except Exception:
        return 0.0


def _fecha_iso(v):
    """Normaliza fecha Tango a ISO yyyy-mm-dd (tolera 'yyyy-mm-ddThh:mm:ss' y 'dd/mm/yyyy')."""
    s = str(v or "").strip()
    if not s:
        return ""
    if "T" in s:
        return s.split("T")[0]
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", s)
    if m:
        d, mo, y = m.groups()
        return f"{y}-{int(mo):02d}-{int(d):02d}"
    return s[:10]


def _parse_nro(nro):
    """'0001-00012345' | '000100000012345' -> (punto_venta, numero)."""
    s = re.sub(r"\s", "", str(nro or ""))
    if "-" in s:
        pv, num = s.split("-", 1)
        return pv.zfill(4), num.zfill(8)
    digits = re.sub(r"\D", "", s)
    if len(digits) >= 5:
        return digits[:4].zfill(4), digits[4:].zfill(8)
    return "", digits


def _parse_tipo_letra(tipo_raw):
    """'FAC A' | 'FA' | 'NC B' -> (tipo, letra)."""
    t = str(tipo_raw or "").strip().upper()
    m = re.search(r"\b([ABCEM])\b\s*$", t)
    letra = m.group(1) if m else ""
    tipo = re.sub(r"\b[ABCEM]\b\s*$", "", t).strip() or t
    return tipo, letra


def _map_registro(rec: dict) -> dict:
    """Registro crudo de Tango (una línea de movimiento) -> línea + cabecera normalizada."""
    signed = _to_float(_G(rec, "CANTIDAD_CONTROL_STOCK", "CANTIDAD", "CANT", default=0))
    item_code = str(_G(rec, "COD_ARTICULO", "COD_STA11", "COD_ARTICU", default="") or "").strip()
    tipo_raw = _G(rec, "TIPO_COMPROBANTE", "TIPO", "COD_TIPO", default="")
    letra_sep = _G(rec, "LETRA", "LETRA_COMPROBANTE", default="")
    tipo, letra_emb = _parse_tipo_letra(tipo_raw)
    pv, numero = _parse_nro(_G(rec, "NRO_COMPROBANTE", "NUMERO", "NRO", default=""))
    cae = _G(rec, "CAE", "CAI", "CAE_NRO", default="")
    cae_flag = _G(rec, "CAE_AUTORIZADO", "AUTORIZADO", default=None)
    return {
        "tipo": tipo,
        "letra": (str(letra_sep).strip().upper() or letra_emb),
        "punto_venta": pv,
        "numero": numero,
        "cae": cae,
        "cae_autorizado": bool(cae) if cae_flag is None else bool(cae_flag),
        "fecha": _fecha_iso(_G(rec, "FECHA_DE_COMPROBANTE", "FECHA", "FECHA_COMPROBANTE", default="")),
        "doc_id": str(_G(rec, "ID_STA14", "ID_GVA12", "ID", default="") or ""),
        "_signed": signed,
        "_item_code": item_code,
    }


def agrupar_en_documentos(registros) -> list:
    """Agrupa líneas crudas por comprobante (tipo-letra-pv-numero) en documentos
    normalizados que consume `baja.procesar_ventas`."""
    docs = {}
    for rec in (registros or []):
        m = _map_registro(rec)
        clave = f"{m['tipo']}-{m['letra']}-{m['punto_venta']}-{m['numero']}"
        d = docs.get(clave)
        if d is None:
            d = {
                "tipo": m["tipo"], "letra": m["letra"], "punto_venta": m["punto_venta"],
                "numero": m["numero"], "cae": m["cae"], "cae_autorizado": m["cae_autorizado"],
                "fecha": m["fecha"], "doc_id": m["doc_id"], "lineas": [], "_signed_total": 0.0,
            }
            docs[clave] = d
        signed = m["_signed"]
        d["_signed_total"] += signed
        if m["_item_code"] and abs(signed) > 0:
            d["lineas"].append({
                "item_code": m["_item_code"],
                "cantidad": abs(signed),
                "es_mercaderia": True,   # fila de movimiento de stock => controla stock
            })
    # es_nota_credito por signo del total (Tango firma NC positivo, venta negativo)
    out = []
    for d in docs.values():
        d["es_nota_credito"] = d.pop("_signed_total", 0.0) > 0
        out.append(d)
    return out


def procesar_baja_desde_registros(registros, hwm=None, claves_procesadas=frozenset()) -> dict:
    """PURO: registros crudos de Tango -> resultado de baja (movimientos + dedup + auditoría)."""
    docs = agrupar_en_documentos(registros)
    return baja.procesar_ventas(docs, hwm=hwm, claves_procesadas=claves_procesadas)


def leer_registros_ventas(client, process=None) -> list:
    """Lee los registros de ventas/stock de Tango via Live Query (read-only).
    `client`: TangoHTTPClient (usa APP_INSTANCE_ID). Thin: no se testea sin Tango."""
    proc = process or PROCESS_VENTAS_STOCK
    if not proc:
        raise ValueError(
            "PROCESS_VENTAS_STOCK no configurado: falta el process ID del Live Query de "
            "ventas/stock de Tango (setear env TANGO_PROCESS_VENTAS o confirmar con Forge).")
    return list(client._iter_all(proc))


def ejecutar_baja(client, hwm=None, claves_procesadas=frozenset(), process=None) -> dict:
    """Entry point para la orquestación (Atlas): lee ventas de Tango y arma la baja.
    Devuelve {movimientos, claves_nuevas, hwm_nuevo, auditoria}. NO escribe."""
    registros = leer_registros_ventas(client, process=process)
    return procesar_baja_desde_registros(registros, hwm=hwm, claves_procesadas=claves_procesadas)
