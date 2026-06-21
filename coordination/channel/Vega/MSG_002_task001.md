# MSG_002 — VEGA_TASK_001 Mobile Responsiveness

**De:** Nova  
**Fecha:** 2026-06-17

Vega, tarea asignada.

## VEGA_TASK_001 — Mobile responsiveness

Brief completo en `coordination/inbox/VEGA_TASK_001_MOBILE_RESPONSIVE.md`.

**Resumen ejecutivo:** Constantino probó la app desde un Android (390px) y hay dos problemas concretos:

1. **Navbar** — los links del menú se cortan, los últimos tabs quedan fuera del viewport
2. **Página /presupuesto** — la tabla y el header se desbordan a la derecha

Todo el código está en un solo archivo Python: `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`. El CSS está embebido como strings — `_COMMON_CSS` para estilos globales, y bloques `<style>` locales en cada función de renderizado.

No hay framework externo, no hay build step. Editás el `.py`, reiniciás el servidor, probás.

**Criterio de éxito:** todas las páginas usables desde un celular Android estándar. Sprint de paneles decorativos no se cierra sin esto.

Reportá en `coordination/reports/VEGA_TASK_001_REPORT.md` cuando termines.
