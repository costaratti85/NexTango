"""API de OCR de facturas de proveedor — orquestación (backend Frappe).

Conecta las piezas del flujo, sin implementar el OCR (eso es del módulo
`ocr_suppliers` del agente OCR) ni tocar Tango:

    subir_factura(file_url)            -> encola el job OCR, devuelve {job_id}
    estado(job_id)                     -> {status}
    resultado(job_id)                  -> {proveedor, lineas, matches, meta}
    confirmar_recepcion_borrador(...)  -> [STRETCH] Purchase Receipt en BORRADOR

Flujo (async, server modesto → frappe.enqueue):
    upload (Vega/FileUploader) -> subir_factura -> enqueue _procesar_job
      _procesar_job: resolver archivo -> extract_invoice (SEAM OCR)
                     -> resolver Supplier por CUIT (tax_id, clave nativa)
                     -> match contra catálogo de Items -> guardar en cache
    Vega hace polling de estado(job_id) y al terminar lee resultado(job_id).

Contrato de datos publicado en coordination/research/OCR_PAGINA_CONTRATO.md.
NADA de auto-submit ni escrituras a Tango.
"""
import json
import re

import frappe

from sistema_industrial.ocr_suppliers.extraction import extract_invoice
from sistema_industrial.ocr_suppliers.catalog import load_catalog
from sistema_industrial.ocr_suppliers.item_matcher import match_lines
from sistema_industrial.ocr_suppliers.item_builder import item_payload_nuevo
from sistema_industrial.ocr_suppliers.code_suggester import suggest_next_item_code, aplicar_sugerencias


_JOB_PREFIX = "ocr_suppliers:job:"
_JOB_TTL = 3600  # 1 h: ventana para revisar y confirmar


# ----------------------------------------------------------------- helpers job

def _job_key(job_id: str) -> str:
    return f"{_JOB_PREFIX}{job_id}"


def _save_job(job_id: str, data: dict) -> None:
    frappe.cache().set_value(_job_key(job_id), data, expires_in_sec=_JOB_TTL)


def _load_job(job_id: str) -> dict | None:
    return frappe.cache().get_value(_job_key(job_id))


def _normalizar_cuit(cuit: str) -> str:
    return re.sub(r"\D", "", str(cuit or ""))


def _resolver_supplier(cuit: str) -> dict:
    """Busca el Supplier de ERPNext por tax_id == CUIT (clave nativa, design §2)."""
    cuit_n = _normalizar_cuit(cuit)
    if not cuit_n:
        return {"cuit": "", "nombre": "", "supplier": None, "encontrado": False}
    name = frappe.db.get_value("Supplier", {"tax_id": cuit_n}, "name")
    if not name:
        # fallback: algunos tax_id vienen con guiones
        for tid in frappe.get_all("Supplier", fields=["name", "tax_id"], limit_page_length=0):
            if _normalizar_cuit(tid.get("tax_id")) == cuit_n:
                name = tid["name"]
                break
    if not name:
        return {"cuit": cuit_n, "nombre": "", "supplier": None, "encontrado": False}
    sname = frappe.db.get_value("Supplier", name, "supplier_name")
    return {"cuit": cuit_n, "nombre": sname or name, "supplier": name, "encontrado": True}


# --------------------------------------------------------------- endpoints

@frappe.whitelist()
def subir_factura(file_url: str):
    """Recibe una factura ya subida (frappe.ui.FileUploader) y encola el OCR.

    file_url: /private/files/xxx.pdf (o imagen). r.message: {job_id, status}.
    """
    if not file_url:
        frappe.throw("file_url requerido")
    # resolver a path en disco (validación temprana)
    fname = frappe.db.get_value("File", {"file_url": file_url}, "name")
    if not fname:
        frappe.throw(f"Archivo no encontrado: {file_url}")

    job_id = frappe.generate_hash(length=12)
    _save_job(job_id, {"status": "queued", "file_url": file_url})
    frappe.enqueue(
        "sistema_industrial.api.ocr_proveedores._procesar_job",
        queue="long",
        timeout=600,
        # OJO: `job_id` es un kwarg RESERVADO de frappe.enqueue (id del job RQ) y NO
        # se reenvía a la función. Pasamos nuestro id bajo `ocr_job_id` para que llegue.
        ocr_job_id=job_id,
        file_url=file_url,
    )
    return {"job_id": job_id, "status": "queued"}


@frappe.whitelist()
def estado(job_id: str):
    """Estado del job. r.message: {status: queued|processing|done|error|ocr_pendiente}."""
    job = _load_job(job_id)
    if job is None:
        return {"status": "unknown"}
    return {"status": job.get("status", "unknown"),
            "error": job.get("error"),
            "n_lineas": len(job.get("lineas", []))}


@frappe.whitelist()
def resultado(job_id: str):
    """Resultado completo para la UI (Vega).

    r.message:
    {
      "status": "done",
      "proveedor": {"cuit", "nombre", "supplier", "encontrado"},
      "lineas": [
        {"idx", "codigo_proveedor", "codigo_barras", "descripcion", "cantidad",
         "precio_unitario", "match": {item_code,item_name,score,reason}|null,
         "confianza": 0..100, "candidatos": [{item_code,item_name,score,reason}...],
         "codigo_sugerido": "FF-SS-SS-NNN" | null}   // solo líneas SIN match (Forge)
      ],
      "meta": {...}
    }
    """
    job = _load_job(job_id)
    if job is None:
        frappe.throw("job_id desconocido o expirado")
    return {
        "status": job.get("status"),
        "error": job.get("error"),
        "proveedor": job.get("proveedor", {}),
        "lineas": job.get("lineas", []),
        "meta": job.get("meta", {}),
    }


# --------------------------------------------------------------- worker

def _procesar_job(ocr_job_id: str = None, file_url: str = None):
    """Worker encolado: OCR (seam) -> resolver Supplier -> match Items -> guardar."""
    job_id = ocr_job_id  # ver subir_factura: `job_id` colisiona con el reservado de enqueue
    _save_job(job_id, {"status": "processing", "file_url": file_url})
    try:
        path = frappe.get_doc("File", {"file_url": file_url}).get_full_path()
    except Exception as exc:
        _save_job(job_id, {"status": "error", "error": f"archivo: {exc}"})
        return

    # --- SEAM OCR: si el motor aún no está implementado, estado explícito ---
    try:
        extracted = extract_invoice(path)
    except NotImplementedError:
        _save_job(job_id, {
            "status": "ocr_pendiente",
            "error": "El motor OCR (ocr_suppliers.extraction.extract_invoice) "
                     "todavía no está implementado. Plumbing OK.",
            "file_url": file_url,
        })
        return
    except Exception as exc:
        frappe.log_error(f"ocr_proveedores extract {job_id}: {exc}", "ocr_proveedores")
        _save_job(job_id, {"status": "error", "error": f"extracción: {exc}"})
        return

    proveedor = _resolver_supplier((extracted.get("proveedor") or {}).get("cuit", ""))
    # completar nombre con lo detectado si el Supplier no aportó
    if not proveedor.get("nombre"):
        proveedor["nombre"] = (extracted.get("proveedor") or {}).get("nombre", "")

    try:
        catalog = load_catalog()
        lineas = match_lines(extracted.get("lineas", []), catalog)
    except Exception as exc:
        frappe.log_error(f"ocr_proveedores match {job_id}: {exc}", "ocr_proveedores")
        _save_job(job_id, {"status": "error", "error": f"matching: {exc}"})
        return

    # Sugerencia de código para las líneas SIN match (Forge). El humano lo
    # confirma/edita; es una pre-carga del campo editable (Regla 8).
    aplicar_sugerencias(lineas, suggest_next_item_code)

    _save_job(job_id, {
        "status": "done",
        "file_url": file_url,
        "proveedor": proveedor,
        "lineas": lineas,
        "meta": extracted.get("meta", {}),
    })


# --------------------------------------------------------------- STRETCH

@frappe.whitelist()
def confirmar_recepcion_borrador(supplier: str, lineas_json, company: str = None):
    """[STRETCH] Crea un Purchase Receipt en BORRADOR con las líneas confirmadas
    por el humano. NUNCA hace submit. NO escribe en Tango.

    supplier:     name del Supplier de ERPNext (obligatorio).
    lineas_json:  JSON [{item_code, qty, rate}] — solo líneas confirmadas.
    r.message: {ok, purchase_receipt, docstatus} (docstatus SIEMPRE 0 = borrador).
    """
    if not supplier:
        frappe.throw("supplier requerido")
    if not frappe.db.exists("Supplier", supplier):
        frappe.throw(f"Supplier no encontrado: {supplier}")
    lineas = json.loads(lineas_json) if isinstance(lineas_json, str) else lineas_json
    lineas = [l for l in (lineas or []) if l.get("item_code") and float(l.get("qty") or 0) > 0]
    if not lineas:
        frappe.throw("No hay líneas confirmadas con item_code y cantidad > 0")
    for l in lineas:
        if not frappe.db.exists("Item", l["item_code"]):
            frappe.throw(f"Item inexistente: {l['item_code']}")

    doc = frappe.get_doc({
        "doctype": "Purchase Receipt",
        "supplier": supplier,
        "company": company or frappe.defaults.get_user_default("Company"),
        "items": [{
            "item_code": l["item_code"],
            "qty": float(l["qty"]),
            "rate": float(l.get("rate") or 0),
        } for l in lineas],
    })
    doc.insert(ignore_permissions=True)   # queda en BORRADOR (docstatus=0)
    frappe.db.commit()
    return {"ok": True, "purchase_receipt": doc.name, "docstatus": doc.docstatus}


# ==================================================================== FASE 2
# "Confirmar revisión" (T2/T3): confirmación HUMANA. CERO escritura a Tango.
# Orden ESTRICTO: (1) Supplier -> (2) si_ocr_layout -> (3) Items nuevos -> (4) Excel.

_ITEM_GROUP_DEFAULT = "Ferretería"


def _default_uom() -> str:
    for u in ("unidad", "Nos", "Unit"):
        if frappe.db.exists("UOM", u):
            return u
    return "Nos"


def _default_supplier_group() -> str:
    for g in ("Local", "All Supplier Groups"):
        if frappe.db.exists("Supplier Group", g):
            return g
    return frappe.db.get_value("Supplier Group", {}, "name") or "All Supplier Groups"


def _get_or_create_supplier(cuit: str, nombre: str):
    """(name, creado): Supplier por tax_id==CUIT; lo CREA si no existe (nativo).
    creado=True solo si se dio de alta en esta llamada."""
    cuit_n = _normalizar_cuit(cuit)
    if cuit_n:
        existing = frappe.db.get_value("Supplier", {"tax_id": cuit_n}, "name")
        if existing:
            return existing, False
    if not (nombre or "").strip():
        frappe.throw("No se puede crear el proveedor: falta la razón social (nombre) del OCR.")
    doc = frappe.get_doc({
        "doctype": "Supplier",
        "supplier_name": nombre.strip(),
        "tax_id": cuit_n or None,
        "supplier_group": _default_supplier_group(),
        "supplier_type": "Company",
    })
    doc.insert(ignore_permissions=True)
    return doc.name, True


def _guardar_layout_supplier(supplier: str, cuit: str, meta: dict) -> bool:
    """Guarda el layout aprendido por el OCR en Supplier.si_ocr_layout (JSON).

    El layout viene en meta['layout_learned'] = {cuit: {zonas...}}. Se persiste
    la entrada del CUIT del proveedor. DEFENSIVO: si el campo si_ocr_layout aún
    no existe en Supplier (lo agrega Forge, requiere migrate) se saltea sin
    romper. Devuelve True si se guardó."""
    learned = (meta or {}).get("layout_learned") or {}
    cuit_n = _normalizar_cuit(cuit)
    layout = learned.get(cuit_n) or learned.get(cuit) or (learned if learned else None)
    if not layout:
        return False
    if not frappe.get_meta("Supplier").get_field("si_ocr_layout"):
        frappe.log_error(
            f"si_ocr_layout no existe en Supplier (pendiente Forge/migrate); "
            f"layout de {supplier} no persistido.", "ocr_proveedores")
        return False
    frappe.db.set_value("Supplier", supplier, "si_ocr_layout",
                        json.dumps(layout, ensure_ascii=False))
    return True


def _crear_item_nuevo(item_code, item_name, supplier, codigo_proveedor="", barcode="",
                      is_stock_item=1, si_iva_pct=None):
    """Crea el Item (idempotente por item_code). Si ya existe, asegura el vínculo
    con el proveedor y el barcode sin duplicar. Devuelve el name.

    is_stock_item: del checkbox de la grilla (Vega). Solo se aplica al CREAR uno
    nuevo — a un Item ya existente no le tocamos el flag de stock."""
    item_code = (item_code or "").strip()
    if not item_code:
        frappe.throw("Falta el código de artículo (item_code) para un ítem nuevo.")
    if frappe.db.exists("Item", item_code):
        doc = frappe.get_doc("Item", item_code)
        if supplier and not any(r.supplier == supplier for r in (doc.supplier_items or [])):
            doc.append("supplier_items", {"supplier": supplier, "supplier_part_no": codigo_proveedor or ""})
        if barcode and not any(r.barcode == barcode for r in (doc.barcodes or [])):
            doc.append("barcodes", {"barcode": barcode})
        doc.save(ignore_permissions=True)
        return doc.name
    doc = frappe.get_doc(item_payload_nuevo(
        item_code, item_name, supplier, codigo_proveedor, barcode,
        _ITEM_GROUP_DEFAULT, _default_uom(), is_stock_item, si_iva_pct))
    doc.insert(ignore_permissions=True)
    return doc.name


def _generar_excel_tango(created_items, proveedor):
    """SEAM con Forge: Excel de importación a Tango de los ITEMS NUEVOS.
    Devuelve file_url o None si el generador de Forge aún no está disponible.
    NO escribe en Tango — es un archivo que Constantino importa a mano."""
    if not created_items:
        return None
    try:
        # Impl REAL de Forge (contrato documentado en su docstring: "Atlas invoca en el
        # Confirmar de la Fase 2", firma `build_tango_import_excel(created_items) -> {file_url}`).
        # El módulo ocr_suppliers.tango_export era un stub NotImplementedError -> quedó sin usar.
        from sistema_industrial.tango_sync.article_export import build_tango_import_excel
        result = build_tango_import_excel(created_items)
        return result.get("file_url") if isinstance(result, dict) else result
    except (ImportError, NotImplementedError):
        return None
    except Exception as exc:
        frappe.log_error(f"ocr_proveedores excel tango: {exc}", "ocr_proveedores")
        return None


def _receipt_defaults(company: str = None) -> dict:
    """{company, set_warehouse} para la Recepción de Compra (stock-in).

    SEAM con Forge (ocr_suppliers.stock_config.receipt_defaults, MSG_038/041):
    resuelve company + warehouse destino de forma configurable por site_config
    (`ocr_default_company` / `ocr_default_warehouse`). Si el módulo de Forge aún
    no está deployado, cae a un resolver local equivalente para no bloquear."""
    try:
        from sistema_industrial.ocr_suppliers.stock_config import receipt_defaults
        return receipt_defaults(company)
    except (ImportError, NotImplementedError):
        comp = (company or frappe.conf.get("ocr_default_company")
                or frappe.defaults.get_user_default("Company")
                or frappe.defaults.get_global_default("company")
                or frappe.db.get_value("Company", {}, "name"))
        wh = frappe.conf.get("ocr_default_warehouse")
        if not (wh and frappe.db.exists("Warehouse", wh)):
            wh = None
            for hint in ("Ferretería", "Ferreteria", "Almacén Principal", "Almacen Principal"):
                wh = frappe.db.get_value(
                    "Warehouse",
                    {"company": comp, "is_group": 0, "disabled": 0,
                     "warehouse_name": ["like", f"%{hint}%"]}, "name")
                if wh:
                    break
            if not wh:
                wh = frappe.db.get_value(
                    "Warehouse", {"company": comp, "is_group": 0, "disabled": 0}, "name")
        return {"company": comp, "set_warehouse": wh}


def _crear_recepcion_borrador(supplier, pr_lineas, company=None):
    """Crea la Purchase Receipt en BORRADOR (docstatus=0) con los renglones de la
    factura. NUNCA hace submit — el stock+costo entran cuando Constantino la
    submitea (Regla 8, Nova/MSG_033). 100% ERPNext, nada a Tango.

    pr_lineas: [{item_code, qty, rate}] ya filtradas (qty>0, decision match/nuevo).
    Devuelve {purchase_receipt, warning}: name del borrador o None + un aviso
    legible si no se pudo armar (nunca rompe el flujo de creación de items)."""
    if not pr_lineas:
        return {"purchase_receipt": None, "warning": None}
    try:
        d = _receipt_defaults(company)
        if not d.get("set_warehouse"):
            return {"purchase_receipt": None,
                    "warning": "No se pudo resolver un depósito destino: configurá "
                               "'ocr_default_warehouse' en site_config. No se creó la "
                               "Recepción de Compra (los artículos sí se crearon)."}
        # Aviso si algún renglón no mueve stock (is_stock_item=0): la PR se arma
        # igual pero ese renglón no cargará stock al submitear (Nova/MSG_033).
        no_stock = [l["item_code"] for l in pr_lineas
                    if not frappe.db.get_value("Item", l["item_code"], "is_stock_item")]
        doc = frappe.get_doc({
            "doctype": "Purchase Receipt",
            "supplier": supplier,
            "company": d["company"],
            "set_warehouse": d["set_warehouse"],
            "items": [{
                "item_code": l["item_code"],
                "qty": float(l["qty"]),
                "rate": float(l.get("rate") or 0),
            } for l in pr_lineas],
        })
        doc.insert(ignore_permissions=True)   # BORRADOR (docstatus=0) — sin submit
        frappe.db.commit()
        warning = None
        if no_stock:
            warning = ("Estos artículos no llevan control de stock (is_stock_item=0) "
                       "y no cargarán stock al submitear la recepción: "
                       + ", ".join(no_stock))
        return {"purchase_receipt": doc.name, "warning": warning}
    except Exception as exc:
        frappe.log_error(f"ocr_proveedores recepcion borrador: {exc}", "ocr_proveedores")
        return {"purchase_receipt": None,
                "warning": f"No se pudo armar la Recepción de Compra: {exc}. "
                           "Los artículos sí se crearon."}


@frappe.whitelist()
def confirmar(invoice_id, decisiones_json):
    """Confirmación humana de la revisión (Fase 2, T2/T3). Contrato Vega/MSG_032.
    CERO escritura a Tango, sin auto-submit. Solo lo que el humano confirmó (Regla 8).

    ORDEN ESTRICTO: (1) Supplier -> (2) si_ocr_layout -> (3) Items nuevos -> (4) Excel.

    invoice_id:      = el job_id que devolvió subir_factura.
    decisiones_json: JSON [{idx, line_id, decision, item_code, codigo_barras, is_stock_item}]
      - decision "match":  item_code = Item existente elegido (no crea nada). Entra
                           igual a la Recepción de Compra (qty/precio del OCR).
      - decision "nuevo":  item_code = código del humano; codigo_barras opcional.
                           item_name (=descripción) y codigo_proveedor se toman del
                           job (Redis) por idx. is_stock_item (bool, default true) →
                           control de stock del Item nuevo (checkbox de la grilla).
      - decision "omitir": no se hace nada.

    r.message: {ok, proveedor_creado, created_items, tango_excel, purchase_receipt,
                recepcion_warning}
      - proveedor_creado:   name del Supplier SOLO si se dio de alta ahora, si no null.
      - created_items:      [{item_code, origen:"nuevo", item_name}] de los creados.
      - tango_excel:        file_url del .xlsx, o null si Forge aún no lo generó.
      - purchase_receipt:   name de la Recepción de Compra en BORRADOR (docstatus=0),
                            o null si no se pudo armar (ver recepcion_warning). El
                            humano la submitea para cargar stock+costo (Regla 8).
      - recepcion_warning:  aviso legible si algún renglón no lleva stock o no se
                            pudo crear la recepción; null si todo ok.
    """
    job = _load_job(invoice_id)
    if job is None:
        frappe.throw("invoice_id desconocido o expirado — reprocesá la factura.")
    decisiones = json.loads(decisiones_json) if isinstance(decisiones_json, str) else decisiones_json
    if not decisiones:
        frappe.throw("No hay decisiones para confirmar.")

    prov = job.get("proveedor", {}) or {}
    meta = job.get("meta", {}) or {}
    ocr_by_id = {str(l.get("idx", i)): l for i, l in enumerate(job.get("lineas", []))}

    def _linea(d):
        return ocr_by_id.get(str(d.get("idx", d.get("line_id", "")))) or {}

    # (1) Supplier — crear si no existe
    supplier, creado = _get_or_create_supplier(prov.get("cuit", ""), prov.get("nombre", ""))

    # (2) si_ocr_layout — guardar el layout aprendido en el Supplier
    _guardar_layout_supplier(supplier, prov.get("cuit", ""), meta)

    # (3) Items nuevos (decision == "nuevo") + renglones para la Recepción.
    #     - created_rich: para el Excel de Forge.
    #     - created_out:  objetos {item_code, origen, item_name} para Vega (MSG_040).
    #     - pr_lineas:    renglones de la PR (match + nuevo, NO omitir): item_code,
    #                     qty=cantidad OCR, rate=precio_unitario OCR.
    created_rich, created_out, pr_lineas = [], [], []
    for d in decisiones:
        decision = (d.get("decision") or "").lower()
        if decision in ("omitir", ""):
            continue
        line = _linea(d)
        qty = float(line.get("cantidad") or 0)
        rate = float(line.get("precio_unitario") or 0)
        if decision == "match":
            code = (d.get("item_code") or "").strip()
            if code and qty > 0:
                pr_lineas.append({"item_code": code, "qty": qty, "rate": rate})
            continue
        if decision != "nuevo":
            frappe.throw(f"decision desconocida en la línea {d.get('idx')}: {decision!r}")
        desc = line.get("descripcion", "")
        cod_prov = line.get("codigo_proveedor", "")
        # is_stock_item del checkbox de la grilla (Vega/MSG_040), default 1.
        lleva_stock = d.get("is_stock_item", d.get("lleva_stock", True))
        name = _crear_item_nuevo(d.get("item_code"), desc, supplier, cod_prov,
                                 d.get("codigo_barras") or "",
                                 is_stock_item=1 if lleva_stock else 0)
        created_out.append({"item_code": name, "origen": "nuevo", "item_name": desc})
        created_rich.append({"item_code": name, "item_name": desc,
                             "codigo_proveedor": cod_prov, "barcode": d.get("codigo_barras") or ""})
        if qty > 0:
            pr_lineas.append({"item_code": name, "qty": qty, "rate": rate})

    frappe.db.commit()

    # (4) Excel de Tango de los NUEVOS (Forge). Sin escritura a Tango.
    tango_excel = _generar_excel_tango(created_rich, {**prov, "supplier": supplier})

    # (5) Recepción de Compra en BORRADOR (stock-in nativo, sin submit — Nova/MSG_033).
    recepcion = _crear_recepcion_borrador(supplier, pr_lineas)

    return {
        "ok": True,
        "proveedor_creado": supplier if creado else None,
        "created_items": created_out,
        "tango_excel": tango_excel,
        "purchase_receipt": recepcion["purchase_receipt"],
        "recepcion_warning": recepcion["warning"],
    }
