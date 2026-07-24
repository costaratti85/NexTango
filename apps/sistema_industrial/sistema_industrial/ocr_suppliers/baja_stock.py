"""Baja de stock por ventas de Tango (Fase T5) — parte de Atlas.

Contrato: `coordination/research/PLAN_BAJA_STOCK_Y_CHECK_CATALOGO.md` sección
"GREEN-LIGHT REAL — DECISIONES AJUSTADAS" (Nova/MSG_035). La LECTURA de ventas de
Tango (Live Query, filtro CAE+mercadería) es de OCR; acá está lo de Atlas:

  - Stock Entry **Material Issue** (baja) con AUTO-SUBMIT **GATEADO** (default OFF).
  - Dedup FÉRREO: custom field `tango_comprobante_ref` (índice único) +
    high-water mark (HWM). Nunca descontar dos veces.
  - Log de auditoría de cada baja.
  - Reversibilidad: el Stock Entry nativo es cancelable (docstatus=2).

⚠️ **AUTO-SUBMIT APAGADO hasta el smoke.** El resguardo de Constantino es "baja
auto solo si dedup+CAE pasan smoke". Por eso `auto_submit_habilitado()` devuelve
False salvo que se prenda EXPLÍCITAMENTE el flag `ocr_baja_auto_submit` en
site_config, y eso recién cuando (a) el dedup (T4) esté deployado y pase smoke en
vivo y (b) Nova confirme el gate. Mientras, la baja se crea en BORRADOR.

CERO escritura a Tango: todo es lectura de Tango (la hace OCR) + escritura ERPNext.
"""
from __future__ import annotations

import re

import frappe

_LOG = "ocr_baja"
_HWM_PREFIX = "ocr_baja_hwm:"      # + "{tipo}-{letra}-{ptovta}"  -> último numero


# ---------------------------------------------------------------- identidad / dedup

def comprobante_ref(comp: dict) -> str:
    """Identidad única del comprobante de venta: "tipo-letra-ptovta-numero".

    Ej. {"tipo":"FA","letra":"A","punto_venta":"0003","numero":"00012345"}
        -> "FA-A-0003-00012345". Normaliza (mayúsculas, solo alnum por parte).
    Devuelve "" si falta tipo o numero (no se puede deduplicar → no procesar)."""
    def _p(v):
        return re.sub(r"[^0-9A-Za-z]", "", str(v or "")).upper()
    tipo = _p(comp.get("tipo"))
    letra = _p(comp.get("letra"))
    ptovta = _p(comp.get("punto_venta", comp.get("ptovta")))
    numero = _p(comp.get("numero"))
    if not tipo or not numero:
        return ""
    return f"{tipo}-{letra}-{ptovta}-{numero}"


def ya_procesado(ref: str) -> str | None:
    """name del Stock Entry que ya descontó ese comprobante, o None. Chequeo por
    el índice único `tango_comprobante_ref` (segunda capa del dedup)."""
    if not ref:
        return None
    if not frappe.get_meta("Stock Entry").get_field("tango_comprobante_ref"):
        return None  # campo aún no migrado
    return frappe.db.get_value("Stock Entry", {"tango_comprobante_ref": ref}, "name")


# ---------------------------------------------------------------- high-water mark

def _hwm_key(comp: dict) -> str:
    def _p(v):
        return re.sub(r"[^0-9A-Za-z]", "", str(v or "")).upper()
    return f"{_HWM_PREFIX}{_p(comp.get('tipo'))}-{_p(comp.get('letra'))}-" \
           f"{_p(comp.get('punto_venta', comp.get('ptovta')))}"


def get_hwm(comp: dict) -> int:
    """Último número de comprobante rastrillado para esa serie (tipo-letra-ptovta)."""
    try:
        return int(frappe.db.get_default(_hwm_key(comp)) or 0)
    except (TypeError, ValueError):
        return 0


def avanzar_hwm(comp: dict) -> int:
    """Avanza el HWM SOLO hacia adelante (max). Devuelve el HWM resultante."""
    try:
        numero = int(re.sub(r"\D", "", str(comp.get("numero") or "")) or 0)
    except ValueError:
        return get_hwm(comp)
    actual = get_hwm(comp)
    if numero > actual:
        frappe.db.set_default(_hwm_key(comp), str(numero))
        return numero
    return actual


# ---------------------------------------------------------------- gate auto-submit

def auto_submit_habilitado() -> bool:
    """GATE del auto-submit de la baja. Default **OFF**.

    Solo True si el flag `ocr_baja_auto_submit` está explícitamente prendido en
    site_config — cosa que se hace RECIÉN cuando el dedup pasa smoke en vivo y Nova
    confirma. Mientras, la baja se crea en BORRADOR (no descuenta hasta el submit)."""
    return bool(frappe.conf.get("ocr_baja_auto_submit"))


# ---------------------------------------------------------------- warehouse origen

def _source_warehouse(company: str = None) -> tuple:
    """(company, s_warehouse) de la baja. SEAM con Forge (stock_config.delivery_
    defaults) — warehouse COMPARTIDO con la recepción (MSG_035: no duplicar). Con
    fallback local seguro (nunca 'en tránsito' salvo config explícita)."""
    try:
        from sistema_industrial.ocr_suppliers.stock_config import delivery_defaults
        d = delivery_defaults(company)
        return d.get("company"), d.get("set_warehouse")
    except (ImportError, NotImplementedError):
        comp = (company or frappe.conf.get("ocr_default_company")
                or frappe.defaults.get_user_default("Company")
                or frappe.defaults.get_global_default("company")
                or frappe.db.get_value("Company", {}, "name"))
        wh = frappe.conf.get("ocr_default_warehouse")
        if wh and frappe.db.exists("Warehouse", wh):
            return comp, wh
        for hint in ("Ferretería", "Ferreteria", "Almacén Principal", "Almacen Principal"):
            wh = frappe.db.get_value(
                "Warehouse",
                {"company": comp, "is_group": 0, "disabled": 0,
                 "warehouse_name": ["like", f"%{hint}%"]}, "name")
            if wh:
                return comp, wh
        return comp, None  # sin depósito seguro -> el caller degrada


# ---------------------------------------------------------------- baja / reversión

def crear_baja(comprobante: dict, lineas: list, company: str = None) -> dict:
    """Crea la baja de stock (Stock Entry Material Issue) de un comprobante de venta.

    comprobante: {tipo, letra, punto_venta, numero, ...} (lo arma OCR desde Tango).
    lineas: [{item_code, qty}] a descontar.
    company: opcional (default configurable).

    Dedup en DOS capas antes de tocar stock: HWM (acota) + índice único (garantiza).
    AUTO-SUBMIT GATEADO: solo submitea si `auto_submit_habilitado()` (default OFF);
    si no, deja el Stock Entry en BORRADOR (no descuenta hasta el submit humano).

    Devuelve {ok, stock_entry, docstatus, submitted, ref, skipped, motivo, warning}.
    """
    ref = comprobante_ref(comprobante)
    if not ref:
        return {"ok": False, "stock_entry": None, "skipped": True,
                "motivo": "comprobante sin tipo/numero — no se puede deduplicar",
                "ref": ""}

    # Dedup capa 2 (índice único): ¿ya se descontó este comprobante?
    existente = ya_procesado(ref)
    if existente:
        return {"ok": True, "stock_entry": existente, "docstatus": None,
                "submitted": None, "skipped": True, "motivo": "comprobante ya procesado",
                "ref": ref}

    lineas = [l for l in (lineas or [])
              if l.get("item_code") and float(l.get("qty") or 0) > 0]
    if not lineas:
        return {"ok": False, "stock_entry": None, "skipped": True,
                "motivo": "sin renglones con item_code y qty > 0", "ref": ref}

    comp, s_wh = _source_warehouse(company)
    if not s_wh:
        return {"ok": False, "stock_entry": None, "skipped": True,
                "motivo": "sin depósito origen configurado (ocr_default_warehouse)",
                "ref": ref, "warning": "configurá el depósito origen de la baja"}

    try:
        payload = {
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Issue",
            "company": comp,
            "items": [{
                "item_code": l["item_code"],
                "qty": float(l["qty"]),
                "s_warehouse": s_wh,
            } for l in lineas],
        }
        if frappe.get_meta("Stock Entry").get_field("tango_comprobante_ref"):
            payload["tango_comprobante_ref"] = ref
        doc = frappe.get_doc(payload)
        doc.insert(ignore_permissions=True)  # BORRADOR (docstatus=0)

        submitted = False
        if auto_submit_habilitado():
            doc.submit()                      # docstatus=1: DESCUENTA stock
            submitted = True

        avanzar_hwm(comprobante)              # el HWM avanza hacia adelante
        frappe.db.commit()

        frappe.logger(_LOG).info({
            "evento": "baja_stock",
            "ref": ref,
            "stock_entry": doc.name,
            "docstatus": doc.docstatus,
            "submitted": submitted,
            "items": [{"item_code": l["item_code"], "qty": float(l["qty"])} for l in lineas],
        })
        return {"ok": True, "stock_entry": doc.name, "docstatus": doc.docstatus,
                "submitted": submitted, "skipped": False, "motivo": None, "ref": ref,
                "warning": (None if submitted else
                            "baja en BORRADOR: el auto-submit está apagado hasta el "
                            "smoke del dedup (resguardo de Constantino).")}
    except Exception as exc:
        frappe.log_error(f"ocr_baja crear_baja {ref}: {exc}", _LOG)
        return {"ok": False, "stock_entry": None, "skipped": False,
                "motivo": f"error al crear la baja: {exc}", "ref": ref}


@frappe.whitelist()
def revertir_baja(stock_entry: str) -> dict:
    """Reversibilidad (Nova/MSG_035): cancela la baja (Stock Entry docstatus 1→2),
    devolviendo el stock. Si está en BORRADOR (nunca descontó), informa que no hay
    nada que revertir. Acción humana explícita."""
    if not frappe.db.exists("Stock Entry", stock_entry):
        frappe.throw(f"Stock Entry inexistente: {stock_entry}")
    doc = frappe.get_doc("Stock Entry", stock_entry)
    if doc.docstatus == 0:
        return {"ok": True, "revertido": False,
                "motivo": "la baja está en borrador (no descontó stock); no hay qué revertir"}
    if doc.docstatus == 2:
        return {"ok": True, "revertido": False, "motivo": "ya estaba cancelada"}
    doc.cancel()  # docstatus=2 → revierte los Stock Ledger Entries
    frappe.db.commit()
    frappe.logger(_LOG).info({"evento": "baja_revertida", "stock_entry": stock_entry})
    return {"ok": True, "revertido": True, "stock_entry": stock_entry}


@frappe.whitelist()
def baja_gate_estado() -> dict:
    """Read-only: estado del gate de auto-submit de la baja (para la UI / diagnóstico)."""
    return {
        "auto_submit_habilitado": auto_submit_habilitado(),
        "flag": "ocr_baja_auto_submit (site_config)",
        "nota": ("Apagado por defecto. Se prende solo cuando el dedup pasa smoke en "
                 "vivo y Nova confirma el gate. Con el gate apagado la baja queda en "
                 "BORRADOR."),
    }
