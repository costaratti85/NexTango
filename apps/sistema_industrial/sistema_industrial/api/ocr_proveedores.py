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
        job_id=job_id,
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

def _procesar_job(job_id: str, file_url: str):
    """Worker encolado: OCR (seam) -> resolver Supplier -> match Items -> guardar."""
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
