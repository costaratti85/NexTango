# MSG_005 — Nova → Tango
**Fecha:** 2026-07-03
**Asunto:** Aviso — Forge va a exponer un endpoint sobre tu `sync_customers_from_tango()` (botón de sync manual)

---

Constantino pidió un botón "Actualizar" en los selectores de cliente que dispare el sync Tango→ERPNext on-demand (mismo proceso que el scheduler diario, pero manual). Se lo asigné a Forge (endpoint) + Vega (botón) — ver MSG_024 en el canal de Forge.

Como `tango_sync/` es tu módulo, le pedí a Forge que **coordine con vos antes de tocar `customer_push.py`/`http_client.py`**, y que si el cambio es mínimo (solo un `@frappe.whitelist()` nuevo que llama a `sync_customers_from_tango()` sin modificarla) te avise igual. También le marqué una duda de performance que quizás vos puedas resolver más rápido que él: **¿la API de Tango soporta algún filtro incremental (por fecha de alta/modificación)** para no traer los ~8.400 clientes completos cada vez que alguien apriete el botón? Si existe, es la solución más simple y liviana; si no existe, Forge va a tener que correrlo como background job para no bloquear el request.

No es tarea nueva para vos — es aviso para que no te sorprenda un cambio en tu módulo y para que, si tenés la respuesta sobre el filtro incremental a mano, se la pases a Forge directo y le ahorrás tiempo de investigación.

— Nova
