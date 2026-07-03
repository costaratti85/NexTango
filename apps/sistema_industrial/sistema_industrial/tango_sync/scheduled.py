"""Frappe scheduled jobs para sincronización Tango → ERPNext.

Registrados en hooks.py bajo scheduler_events.
Leen SI_NEXUS_KEY del entorno del proceso (configurado en /etc/environment en Ubuntu).
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def sync_customers_from_tango() -> None:
    """Sincroniza el maestro de clientes Tango → ERPNext. Corre diariamente via Frappe scheduler."""
    from sistema_industrial.tango_sync.http_client import TangoHTTPClient, make_tango_config_from_env
    from sistema_industrial.erpnext_extensions.client import ERPNextClient
    from sistema_industrial.tango_sync.customer_push import push_customers_to_erpnext

    config = make_tango_config_from_env()
    if not config.token:
        logger.error("sync_customers_from_tango: SI_NEXUS_KEY no configurado — sync abortado")
        return

    logger.info("sync_customers_from_tango: iniciando descarga desde Tango...")
    tango = TangoHTTPClient(config)

    customers = tango.get_customers()
    logger.info("sync_customers_from_tango: %d clientes descargados", len(customers))

    result = push_customers_to_erpnext(customers, ERPNextClient())
    logger.info(
        "sync_customers_from_tango: creados=%d actualizados=%d fallidos=%d",
        result.created, result.updated, result.failed,
    )
    if result.errors:
        for code, err in result.errors[:10]:
            logger.warning("  cliente %s: %s", code, err[:200])
