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


def _company_puede_postear_stock(company: str, warehouse: str = None) -> bool:
    """Con perpetual inventory ON, submitear stock postea GL → hace falta cuenta de
    inventario. True si el depósito tiene `account`, o la company tiene
    `default_inventory_account`. (Nextango sí; HSRS no, a hoy.)"""
    if warehouse and frappe.db.get_value("Warehouse", warehouse, "account"):
        return True
    if not frappe.db.get_value("Company", company, "enable_perpetual_inventory"):
        return True  # sin perpetual inventory no se exige cuenta
    return bool(frappe.db.get_value("Company", company, "default_inventory_account"))


# ---------------------------------------------------------------- baja / reversión

def _construir_baja(ref, items, company, warehouse, entry_type):
    """Constructor compartido (validado en smoke duro): arma el Stock Entry de la
    baja, lo submitea si el gate está ON, loguea y devuelve el resultado.

    ref: identidad del comprobante (tango_comprobante_ref, índice único).
    items: [{item_code, qty}] con qty > 0 (ya en valor absoluto).
    entry_type: 'Material Issue' (salida/venta → descuenta) o 'Material Receipt'
        (entrada/nota de crédito → suma). El warehouse va como s_warehouse o
        t_warehouse según corresponda.

    Dedup capa 2: si el índice único ya tiene ese ref, ERPNext rechaza el insert
    (UniqueValidationError) → se captura y se reporta 'ya procesado' (nunca dos veces).
    """
    es_salida = entry_type == "Material Issue"
    wh_key = "s_warehouse" if es_salida else "t_warehouse"
    try:
        payload = {
            "doctype": "Stock Entry",
            "stock_entry_type": entry_type,
            "company": company,
            "items": [{"item_code": it["item_code"], "qty": float(it["qty"]),
                       wh_key: warehouse} for it in items],
        }
        if frappe.get_meta("Stock Entry").get_field("tango_comprobante_ref"):
            payload["tango_comprobante_ref"] = ref
        doc = frappe.get_doc(payload)
        doc.insert(ignore_permissions=True)   # BORRADOR (docstatus=0)

        submitted = False
        if auto_submit_habilitado():
            doc.submit()                      # docstatus=1: MUEVE stock
            submitted = True
        frappe.db.commit()

        frappe.logger(_LOG).info({
            "evento": "baja_stock", "ref": ref, "stock_entry": doc.name,
            "entry_type": entry_type, "docstatus": doc.docstatus, "submitted": submitted,
            "items": [{"item_code": it["item_code"], "qty": float(it["qty"])} for it in items],
        })
        return {"ok": True, "stock_entry": doc.name, "docstatus": doc.docstatus,
                "submitted": submitted, "skipped": False, "motivo": None, "ref": ref,
                "warning": (None if submitted else
                            "baja en BORRADOR: el gate de auto-submit "
                            "(ocr_baja_auto_submit) está apagado; no movió stock.")}
    except frappe.UniqueValidationError:
        frappe.db.rollback()
        existente = ya_procesado(ref)
        return {"ok": True, "stock_entry": existente, "skipped": True,
                "motivo": "comprobante ya procesado (índice único)", "ref": ref}
    except Exception as exc:
        frappe.log_error(f"ocr_baja _construir_baja {ref}: {exc}", _LOG)
        return {"ok": False, "stock_entry": None, "skipped": False,
                "motivo": f"error al armar la baja: {exc}", "ref": ref}


def _cae_autorizado(comprobante: dict) -> bool:
    """El comprobante trae un CAE (o CAEA) autorizado. Blindaje MSG_035: solo se
    descuenta stock de comprobantes AUTORIZADOS. El filtro fino (autorizado + con
    mercadería) lo hace OCR en la Live Query; acá NO confiamos a ciegas y exigimos
    que la señal de autorización venga en el comprobante (defensa en profundidad)."""
    cae = comprobante.get("cae") or comprobante.get("caea") or comprobante.get("cae_numero")
    if str(cae or "").strip():
        return True
    # flag explícito alternativo (por si OCR marca autorizado sin adjuntar el nº)
    return bool(comprobante.get("cae_autorizado") or comprobante.get("autorizado"))


def crear_baja(comprobante: dict, lineas: list, company: str = None) -> dict:
    """Crea la baja de stock (Stock Entry Material Issue) de un comprobante de venta.

    comprobante: {tipo, letra, punto_venta, numero, cae, ...} (lo arma OCR desde
        Tango; DEBE traer el CAE autorizado — ver `_cae_autorizado`).
    lineas: [{item_code, qty}] de MERCADERÍA a descontar (OCR ya filtra servicios/
        percepciones; acá se exige al menos un renglón con item_code y qty>0).
    company: opcional (default configurable).

    Blindaje (MSG_035): (1) solo comprobantes con CAE autorizado + mercadería;
    (2) dedup DOS capas: HWM (acota) + índice único `tango_comprobante_ref`.
    AUTO-SUBMIT GATEADO: submitea (descuenta) solo si `auto_submit_habilitado()`
    (flag `ocr_baja_auto_submit`); si no, deja el Stock Entry en BORRADOR.

    Devuelve {ok, stock_entry, docstatus, submitted, ref, skipped, motivo, warning}.
    """
    ref = comprobante_ref(comprobante)
    if not ref:
        return {"ok": False, "stock_entry": None, "skipped": True,
                "motivo": "comprobante sin tipo/numero — no se puede deduplicar",
                "ref": ""}

    # Blindaje 1a: CAE autorizado (si no, NO se descuenta — smoke test 2).
    if not _cae_autorizado(comprobante):
        return {"ok": False, "stock_entry": None, "skipped": True,
                "motivo": "comprobante sin CAE autorizado — no se descuenta stock",
                "ref": ref}

    # Dedup capa 2 (índice único): ¿ya se descontó este comprobante?
    existente = ya_procesado(ref)
    if existente:
        return {"ok": True, "stock_entry": existente, "docstatus": None,
                "submitted": None, "skipped": True, "motivo": "comprobante ya procesado",
                "ref": ref}

    # Blindaje 1b: mercadería (al menos un renglón con item_code y qty>0).
    lineas = [l for l in (lineas or [])
              if l.get("item_code") and float(l.get("qty") or 0) > 0]
    if not lineas:
        return {"ok": False, "stock_entry": None, "skipped": True,
                "motivo": "sin mercadería (renglones con item_code y qty > 0)", "ref": ref}

    comp, s_wh = _source_warehouse(company)
    if not s_wh:
        return {"ok": False, "stock_entry": None, "skipped": True,
                "motivo": "sin depósito origen configurado (ocr_default_warehouse)",
                "ref": ref, "warning": "configurá el depósito origen de la baja"}

    # Blindaje contable: con perpetual inventory, submitear un movimiento de stock
    # postea GL y necesita cuenta de inventario. Si la company NO la tiene (p. ej.
    # HSRS no la tiene, Nextango sí), NO intentamos la baja auto: mensaje claro que
    # apunta al fix (ocr_default_company) en vez de un error críptico de ERPNext.
    if auto_submit_habilitado() and not _company_puede_postear_stock(comp, s_wh):
        return {"ok": False, "stock_entry": None, "skipped": True,
                "motivo": f"la company '{comp}' no tiene cuenta de inventario configurada "
                          f"(perpetual inventory): no se puede postear la baja",
                "ref": ref,
                "warning": "configurá 'ocr_default_company' a una company con cuenta de "
                           "inventario (default_inventory_account) o cargá la cuenta en el depósito"}

    res = _construir_baja(ref, lineas, comp, s_wh, "Material Issue")
    if res.get("ok") and not res.get("skipped"):
        avanzar_hwm(comprobante)   # HWM propio del caller directo (el orquestador usa el de OCR)
    return res


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
