"""Endpoints whitelisted para sincronización Tango → ERPNext.

Manual/on-demand sync de clientes (vs. scheduled sync que corre diariamente).
Usa background jobs para no bloquear requests (sync completo de ~8.400 clientes).
"""
from __future__ import annotations

import logging
import frappe

logger = logging.getLogger(__name__)


@frappe.whitelist()
def manual_sync_customers() -> dict:
    """Dispara sync manual de clientes Tango → ERPNext como background job.

    Usa frappe.enqueue para no bloquear el request. El frontend hace polling
    en el job_id para obtener resultados cuando esté listo.

    Returns:
        {
            "job_id": "uuid-xxx",
            "message": "Sincronización de clientes iniciada. Por favor espere...",
            "status": "queued"
        }
    """
    job = frappe.enqueue(
        "sistema_industrial.tango_sync.api._sync_customers_background",
        enqueue_after_commit=True,
        timeout=300,  # 5 min para ~8.400 clientes
    )

    # Debug: log what frappe.enqueue returned
    logger.info("frappe.enqueue returned: type=%s, value=%r", type(job).__name__, job)

    # Frappe v16: frappe.enqueue devuelve un Background Job doc o un string ID
    job_id = None
    if job is None:
        job_id = "queued_but_no_id"  # Fallback: enqueue succeeds but no ID returned
    elif isinstance(job, str):
        job_id = job
    elif isinstance(job, dict):
        job_id = job.get("id") or job.get("name") or str(job)
    elif hasattr(job, "id"):
        job_id = job.id or job.name if hasattr(job, "name") else str(job)
    else:
        job_id = str(job) if job else "queued_no_id"

    return {
        "job_id": job_id,
        "message": "Sincronización de clientes iniciada. Por favor espere...",
        "status": "queued",
    }


@frappe.whitelist()
def get_sync_status(job_id: str) -> dict:
    """Consulta el status de un Background Job de sync de clientes.

    Args:
        job_id: ID del Background Job (devuelto por manual_sync_customers)

    Returns:
        {
            "status": "queued" | "running" | "completed" | "failed",
            "created": int (si completed),
            "updated": int (si completed),
            "failed": int (si completed),
            "total": int (si completed),
            "error": str (si failed),
            "progress": str (ej. "Descargando clientes...")
        }
    """
    if not job_id:
        raise frappe.ValidationError("job_id requerido")

    try:
        job = frappe.get_doc("Background Job", job_id)
    except frappe.DoesNotExistError:
        return {"status": "not_found", "error": f"Job {job_id} no existe"}

    result = {
        "status": job.status,  # "queued", "running", "completed", "failed"
    }

    # Si está completo, parsear output
    if job.status == "completed" and job.output:
        try:
            output_data = frappe.parse_json(job.output)
            result.update({
                "created": output_data.get("created", 0),
                "updated": output_data.get("updated", 0),
                "failed": output_data.get("failed", 0),
                "total": output_data.get("total", 0),
            })
        except Exception as e:
            logger.warning("get_sync_status: no se pudo parsear output: %s", e)
            result["output_raw"] = job.output

    # Si falló, incluir error
    if job.status == "failed" and job.exc:
        result["error"] = job.exc[:500]  # primeros 500 chars del traceback

    # Timestamps útiles
    if job.started_on:
        result["started_on"] = str(job.started_on)
    if job.completed_on:
        result["completed_on"] = str(job.completed_on)

    logger.info("get_sync_status(%s): status=%s", job_id, job.status)
    return result


def _sync_customers_background() -> dict:
    """Worker background que ejecuta el sync de clientes.

    Reutiliza la lógica de sync_customers_from_tango() pero devuelve el resultado
    para que pueda ser inspeccionado vía Background Job polling.

    Returns:
        {
            "created": int,
            "updated": int,
            "failed": int,
            "errors": list[tuple[str, str]]
        }
    """
    from sistema_industrial.tango_sync.http_client import TangoHTTPClient, make_tango_config_from_env
    from sistema_industrial.erpnext_extensions.client import ERPNextClient
    from sistema_industrial.tango_sync.customer_push import push_customers_to_erpnext

    config = make_tango_config_from_env()
    if not config.token:
        msg = "SI_NEXUS_KEY no configurado — sync abortado"
        logger.error("_sync_customers_background: %s", msg)
        raise frappe.ValidationError(msg)

    logger.info("_sync_customers_background: iniciando descarga desde Tango...")
    tango = TangoHTTPClient(config)

    customers = tango.get_customers()
    logger.info("_sync_customers_background: %d clientes descargados", len(customers))

    result = push_customers_to_erpnext(customers, ERPNextClient())
    logger.info(
        "_sync_customers_background: creados=%d actualizados=%d fallidos=%d",
        result.created, result.updated, result.failed,
    )
    if result.errors:
        for code, err in result.errors[:10]:
            logger.warning("  cliente %s: %s", code, err[:200])

    # Devolver dict que será guardado en el job output
    return {
        "created": result.created,
        "updated": result.updated,
        "failed": result.failed,
        "skipped": result.skipped,
        "total": result.total,
        "errors": result.errors,
    }
