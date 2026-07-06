"""Prueba de sync de artículos: primeros N artículos Tango → ERPNext.

Uso:
    python tools/probe_articles_sync.py [N]   # default N=10

Requiere las mismas variables de entorno que el sync masivo:
    APP_INSTANCE_ID (o TANGO_TOKEN), ERPNEXT_API_KEY, ERPNEXT_API_SECRET
"""
from __future__ import annotations

import logging
import os
import sys

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "sistema_industrial"))

from sistema_industrial.tango_sync.http_client import TangoHTTPClient, make_tango_config_from_env
from sistema_industrial.erpnext_extensions.client import ERPNextClient
from sistema_industrial.tango_sync.article_push import push_articles_to_erpnext, _build_item_doc

N = int(sys.argv[1]) if len(sys.argv) > 1 else 10

print(f"\n=== Probe sync articulos Tango -> ERPNext (primeros {N}) ===\n")

# 1. Descargar artículos desde Tango
config = make_tango_config_from_env()
if not config.token:
    print("ERROR: token Tango no configurado (APP_INSTANCE_ID / TANGO_TOKEN)")
    sys.exit(1)

tango = TangoHTTPClient(config)
print("Descargando artículos desde Tango (process 87)...")
articles = tango.get_articles()
print(f"Total descargados: {len(articles)}")

subset = articles[:N]
print(f"\nSubconjunto de prueba ({N} artículos):")
for i, a in enumerate(subset, 1):
    doc = _build_item_doc(a)
    print(f"  {i:2d}. {a.code:25s}  grupo={doc['item_group']:20s}  uom={doc['stock_uom']}  nombre={doc['item_name'][:50]}")

print(f"\nSincronizando {N} artículos hacia ERPNext...")
client = ERPNextClient()
result = push_articles_to_erpnext(subset, client)

print(f"\n=== Resultados ===")
print(f"  Creados:     {result.created}")
print(f"  Actualizados:{result.updated}")
print(f"  Fallidos:    {result.failed}")
print(f"  Total:       {result.total}")

if result.errors:
    print(f"\nErrores ({len(result.errors)}):")
    for code, err in result.errors:
        print(f"  {code}: {err[:200]}")
else:
    print("\nSin errores.")

print("\nDone.")
