"""Endpoints whitelisted para sincronización Tango → ERPNext.

Manual/on-demand sync de clientes (vs. scheduled sync que corre diariamente).
Usa Redis para trackear estado (Background Jobs no disponible en esta instalación Frappe v16).
"""
from __future__ import annotations

import logging
import json
import time
import uuid
import frappe

logger = logging.getLogger(__name__)

# Redis cache para trackear sync jobs (Background Job doctype no existe)
def _get_redis():
    return frappe.cache()

def _sync_job_key(job_id: str) -> str:
    return f"sync_customer_job:{job_id}"


@frappe.whitelist()
def manual_sync_customers() -> dict:
    """Dispara sync manual de clientes Tango → ERPNext (síncrono con timeout largo).

    No usa Background Jobs (no disponible en esta instalación Frappe v16).
    Usa Redis para trackear el estado y permitir polling del frontend.

    Returns:
        {
            "job_id": "uuid-xxx",
            "message": "Sincronización de clientes iniciada. Por favor espere...",
            "status": "queued"
        }
    """
    # Generar job_id único
    job_id = str(uuid.uuid4())

    # Guardar estado inicial en Redis (TTL 10 min)
    redis = _get_redis()
    job_data = {
        "status": "running",
        "started_at": time.time(),
        "created": 0,
        "updated": 0,
        "failed": 0,
        "total": 0,
    }
    redis.setex(_sync_job_key(job_id), 600, json.dumps(job_data))

    logger.info("manual_sync_customers: job_id=%s, iniciando sync en thread", job_id)

    # Ejecutar el sync sincronicamente (Frappe sin Background Jobs)
    # Enqueue si es posible, sino correr directo
    try:
        frappe.enqueue(
            "sistema_industrial.tango_sync.api._sync_customers_background_redis",
            sync_job_id=job_id,  # RENAMED: job_id es parámetro reservado de frappe.enqueue(), no se reenvía
            enqueue_after_commit=True,
            timeout=300,
        )
        logger.info("manual_sync_customers: job_id=%s enqueued via frappe.enqueue", job_id)
    except Exception as e:
        logger.warning("manual_sync_customers: frappe.enqueue falló, corriendo sincrónico: %s", e)
        # Fallback: correr sincrónico
        _sync_customers_background_redis(job_id)

    return {
        "job_id": job_id,
        "message": "Sincronización de clientes iniciada. Por favor espere...",
        "status": "queued",
    }


@frappe.whitelist()
def get_sync_status(job_id: str) -> dict:
    """Consulta el status de un sync de clientes (almacenado en Redis).

    Args:
        job_id: ID del sync job (devuelto por manual_sync_customers)

    Returns:
        {
            "status": "running" | "completed" | "failed",
            "created": int,
            "updated": int,
            "failed": int,
            "total": int,
            "error": str (si failed),
            "started_at": timestamp,
            "completed_at": timestamp (si completed)
        }
    """
    if not job_id:
        raise frappe.ValidationError("job_id requerido")

    redis = _get_redis()
    job_data_json = redis.get(_sync_job_key(job_id))

    if not job_data_json:
        return {"status": "not_found", "error": f"Job {job_id} no existe o expiró"}

    try:
        job_data = json.loads(job_data_json)
    except Exception as e:
        logger.error("get_sync_status: no se pudo parsear Redis data: %s", e)
        return {"status": "error", "error": "Corrupted job data"}

    # Devolver el estado guardado en Redis
    response = {
        "status": job_data.get("status"),
        "created": job_data.get("created", 0),
        "updated": job_data.get("updated", 0),
        "failed": job_data.get("failed", 0),
        "total": job_data.get("total", 0),
    }

    if job_data.get("error"):
        response["error"] = job_data["error"]

    if job_data.get("started_at"):
        response["started_at"] = job_data["started_at"]
    if job_data.get("completed_at"):
        response["completed_at"] = job_data["completed_at"]

    logger.info("get_sync_status(%s): status=%s", job_id, job_data.get("status"))
    return response


def _sync_customers_background_redis(sync_job_id: str) -> dict:
    """Worker que ejecuta el sync de clientes y guarda resultado en Redis.

    Args:
        sync_job_id: ID del job (para trackear en Redis) — renombrado para evitar colisión con frappe.enqueue(job_id=...)

    Returns:
        {
            "created": int,
            "updated": int,
            "failed": int,
            "errors": list
        }
    """
    from sistema_industrial.tango_sync.http_client import TangoHTTPClient, make_tango_config_from_env
    from sistema_industrial.erpnext_extensions.client import ERPNextClient
    from sistema_industrial.tango_sync.customer_push import push_customers_to_erpnext

    job_id = sync_job_id  # Alias para compatibilidad con el resto del código
    redis = _get_redis()
    job_key = _sync_job_key(job_id)

    try:
        config = make_tango_config_from_env()
        if not config.token:
            raise frappe.ValidationError("SI_NEXUS_KEY no configurado")

        logger.info("_sync_customers_background_redis(%s): iniciando...", job_id)
        tango = TangoHTTPClient(config)

        customers = tango.get_customers()
        logger.info("_sync_customers_background_redis(%s): %d clientes descargados", job_id, len(customers))

        result = push_customers_to_erpnext(customers, ERPNextClient())
        logger.info(
            "_sync_customers_background_redis(%s): creados=%d actualizados=%d fallidos=%d",
            job_id, result.created, result.updated, result.failed,
        )

        # Guardar resultado en Redis
        job_data = {
            "status": "completed",
            "created": result.created,
            "updated": result.updated,
            "failed": result.failed,
            "total": result.total,
            "started_at": redis.get(job_key + ":started_at") or time.time(),
            "completed_at": time.time(),
        }
        if result.errors:
            job_data["error"] = f"{len(result.errors)} clientes con error. Primero: {result.errors[0][1][:200]}"

        redis.setex(job_key, 600, json.dumps(job_data))
        logger.info("_sync_customers_background_redis(%s): resultado guardado en Redis", job_id)

        return job_data

    except Exception as e:
        logger.exception("_sync_customers_background_redis(%s): ERROR: %s", job_id, e)
        job_data = {
            "status": "failed",
            "error": str(e)[:500],
            "started_at": redis.get(job_key + ":started_at") or time.time(),
            "completed_at": time.time(),
        }
        redis.setex(job_key, 600, json.dumps(job_data))
        return job_data
