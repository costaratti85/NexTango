# Sistema Industrial Nextango

Semilla operativa para construir SistemaIndustrial como app Frappe sobre ERPNext.

Leer primero:
- docs/00_PROJECT_NORTH_STAR.md
- docs/00_BRUJU_MESSAGE_TO_TEAM.md
- docs/24_MONDAY_CODEX_SINGLE_ORDER.md
- docs/29_AGENT_ZOO.md

Primer flujo MVP:
panel decorativo -> cotizacion estilo ERPNext -> pieza pendiente -> cola de corte -> lote DXF por material/espesor.

No se implementa nesting ni G-code. CypCut y el postprocesador existente siguen siendo dueños de eso.

Comandos:
```bash
PYTHONPATH=apps/sistema_industrial pytest -q
PYTHONPATH=apps/sistema_industrial python tools/demo_panel_to_cut_batch.py
```
