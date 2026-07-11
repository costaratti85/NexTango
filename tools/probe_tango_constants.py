"""Probe de constantes Tango para Nextango.

Enumera CondicionVenta, ListaDePreciosVentas, Moneda y Deposito para
identificar los IDs que se necesitan en el push de Pedidos.

Process IDs descubiertos en TangoDeltaApi-main.zip (2026-07-02):
  CondicionVenta (GVA01)      -> process 2497
  ListaDePreciosVentas (GVA10)-> process 984
  Moneda                      -> process 1660
  Deposito (STA22)            -> process 2941
  Articulos (STA11)           -> process 87
  Clientes (GVA14)            -> process 2117
  Pedidos (GVA21)             -> process 19845

Uso:
    python tools/probe_tango_constants.py
"""
from __future__ import annotations

import os
import sys

# Agregar el path de la app para importar modulos propios
_APP = os.path.join(os.path.dirname(__file__), "..", "apps", "sistema_industrial")
sys.path.insert(0, os.path.abspath(_APP))

# APP_INSTANCE_ID (token Tango) debe venir del entorno — nunca hardcodeado.
# Exportalo antes de correr: export APP_INSTANCE_ID=... (o via .env).
os.environ.setdefault("TANGO_URL", "http://server-t:17000")
os.environ.setdefault("TANGO_COMPANY", "25")

# Importar DESPUES de setear la env var
from sistema_industrial.tango_sync.http_client import (  # noqa: E402
    TangoHTTPClient,
    make_tango_config_from_env,
)

PROCESS_COND_VENTA = 2497
PROCESS_LISTA_PRECIOS = 984
PROCESS_MONEDA = 1660
PROCESS_DEPOSITO = 2941


def probe_process(client: TangoHTTPClient, process: int, label: str) -> list[dict]:
    print(f"\n{'='*60}")
    print(f"  {label}  (process {process})")
    print('='*60)
    try:
        records = list(client._iter_all(process))
    except Exception as exc:
        print(f"  ERROR: {exc}")
        return []

    if not records:
        print("  (sin registros)")
        return records

    print(f"  Total: {len(records)} registros")
    # Mostrar primeros 20
    for r in records[:20]:
        print(f"  {r}")
    if len(records) > 20:
        print(f"  ... y {len(records) - 20} mas")
    return records


def main() -> None:
    config = make_tango_config_from_env()
    print(f"Tango URL : {config.base_url}")
    print(f"Company   : {config.company}")
    print(f"Token     : {config.token[:8]}..." if config.token else "Token     : (sin token)")

    client = TangoHTTPClient(config=config)

    probe_process(client, PROCESS_COND_VENTA,   "CondicionVenta (GVA01) — ID_GVA01, COND_VTA, DESC_COND")
    probe_process(client, PROCESS_LISTA_PRECIOS, "ListaDePreciosVentas (GVA10) — ID_GVA10, NRO_DE_LIS, NOMBRE_LIS")
    probe_process(client, PROCESS_MONEDA,        "Moneda — para ID_MONEDA (ARS = 'PES')")
    probe_process(client, PROCESS_DEPOSITO,      "Deposito (STA22) — ID_STA22, COD_STA22, NOMBRE_SUC")

    print("\nBusca en la salida:")
    print("  - CondicionVenta: cual es la condicion habitual de Nextango (30 dias, contado, etc.)")
    print("  - ListaPrecios:   cual es la lista principal (numero 1, 2, etc.)")
    print("  - Moneda:         ID de la moneda local (simbolo '$' o 'ARS')")
    print("  - Deposito:       cual deposito usar para los pedidos")


if __name__ == "__main__":
    main()
