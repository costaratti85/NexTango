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
         "confianza": 0..100, "candidatos": [{item_code,item_name,score,reason}...]}
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
# "Confirmar revisión": confirmación HUMANA. CERO escritura a Tango.
# Orden: (1) crear/resolver Supplier -> (2) crear Items NUEVOS -> (3) Excel Tango.

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


def _get_or_create_supplier(cuit: str, nombre: str) -> str:
    """name del Supplier (por tax_id==CUIT); lo CREA si no existe (nativo)."""
    cuit_n = _normalizar_cuit(cuit)
    if cuit_n:
        existing = frappe.db.get_value("Supplier", {"tax_id": cuit_n}, "name")
        if existing:
            return existing
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
    return doc.name


def _crear_item_nuevo(item_code, item_name, supplier, codigo_proveedor="", barcode=""):
    """Crea el Item (idempotente por item_code). Si ya existe, asegura el vínculo
    con el proveedor y el barcode sin duplicar. Devuelve el name."""
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
        _ITEM_GROUP_DEFAULT, _default_uom()))
    doc.insert(ignore_permissions=True)
    return doc.name


def _generar_excel_tango(created_items, proveedor):
    """SEAM con Forge: Excel de importación a Tango de los ITEMS NUEVOS.
    Devuelve file_url o None si el generador de Forge aún no está disponible.
    NO escribe en Tango — es un archivo que Constantino importa a mano."""
    if not created_items:
        return None
    try:
        from sistema_industrial.ocr_suppliers.tango_export import build_tango_import_excel
        return build_tango_import_excel(created_items, proveedor)
    except (ImportError, NotImplementedError):
        return None
    except Exception as exc:
        frappe.log_error(f"ocr_proveedores excel tango: {exc}", "ocr_proveedores")
        return None


@frappe.whitelist()
def confirmar(job_id, decisiones_json, company=None):
    """Confirmación humana de la revisión (Fase 2). CERO escritura a Tango.

    Orden garantizado: (1) resolver/crear Supplier -> (2) crear Items NUEVOS ->
    (3) generar el Excel de Tango de esos items (Forge).

    decisiones_json: JSON [{id, accion, item_code, barcode?, item_name?, codigo_proveedor?}]
      - accion "nuevo": crea el Item. item_code (manual, obligatorio); barcode
        opcional. item_name y codigo_proveedor se toman del OCR (cache) si no vienen.
      - accion "match": usa un Item existente (item_code); no crea nada.
      - accion "omitir": se descarta.

    r.message: {ok, supplier, created_items, matched, omitted, tango_excel, resumen}
    """
    job = _load_job(job_id)
    if job is None:
        frappe.throw("job_id desconocido o expirado — reprocesá la factura.")
    decisiones = json.loads(decisiones_json) if isinstance(decisiones_json, str) else decisiones_json
    if not decisiones:
        frappe.throw("No hay decisiones para confirmar.")

    prov = job.get("proveedor", {}) or {}
    ocr_by_id = {str(l.get("idx", i)): l for i, l in enumerate(job.get("lineas", []))}

    # (1) Supplier (crear si falta)
    supplier = _get_or_create_supplier(prov.get("cuit", ""), prov.get("nombre", ""))

    # (2) Items nuevos primero
    created, matched, omitted = [], [], 0
    for d in decisiones:
        accion = (d.get("accion") or "").lower()
        if accion == "omitir":
            omitted += 1
            continue
        line = ocr_by_id.get(str(d.get("id", d.get("line_id", ""))), {})
        if accion == "nuevo":
            desc = d.get("item_name") or line.get("descripcion", "")
            cod_prov = d.get("codigo_proveedor") or line.get("codigo_proveedor", "")
            name = _crear_item_nuevo(d.get("item_code"), desc, supplier, cod_prov, d.get("barcode") or "")
            created.append({"item_code": name, "item_name": desc,
                            "codigo_proveedor": cod_prov, "barcode": d.get("barcode") or ""})
        elif accion in ("match", "confirmar"):
            code = d.get("item_code")
            if not code or not frappe.db.exists("Item", code):
                frappe.throw(f"Item inexistente para la línea {d.get('id')}: {code}")
            matched.append(code)
        else:
            frappe.throw(f"Acción desconocida en la línea {d.get('id')}: {accion!r}")

    frappe.db.commit()

    # (3) Excel de Tango de los NUEVOS (Forge). Sin escritura a Tango.
    tango_excel = _generar_excel_tango(created, {**prov, "supplier": supplier})

    return {
        "ok": True,
        "supplier": supplier,
        "created_items": created,
        "matched": matched,
        "omitted": omitted,
        "tango_excel": tango_excel,
        "resumen": (f"{len(created)} artículo(s) nuevo(s), {len(matched)} match, "
                    f"{omitted} omitido(s)."
                    + ("" if tango_excel or not created else
                       " (Excel de Tango pendiente: generador de Forge no disponible aún.)")),
    }
