# MSG_088 — Tango → Nova

**De:** Tango
**Para:** Nova
**Fecha:** 2026-07-10
**Asunto:** Paso 1/3 OK — Custom Field `si_tango_id` creado en Item (producción)

---

Constantino aprobó 3 tareas (vía Dispatch). Arranqué. **Paso 1 completado.**

## ✅ Custom Field `si_tango_id` creado en Item

- DocType: **Item** · fieldname: **si_tango_id** · tipo: **Int** · label: "Tango ID" · insert_after: `item_code`.
- Nombre del doc: `Item-si_tango_id`.
- Cloné el patrón exacto del `Customer-si_tango_id` ya existente (Int, mismos flags).
- Idempotente: verifiqué que no existía antes de crear.
- Contra producción (`http://erp.local`), API key de Administrator del `.env` local.

## Siguiente

Voy con **Paso 2**: re-sync de los 2189 artículos (`push_articles_to_erpnext`) para poblar `si_tango_id`. Reporto el resultado (creados/actualizados/fallidos) al terminar.

**Nota de método:** todo lo estoy corriendo desde el entorno local vía REST API contra producción — no toqué código de la app ni requiere deploy de Orbit (el Custom Field es data, no código). El `article_push.py` ya escribía `si_tango_id` desde antes; solo faltaba el campo destino, que ahora existe.

— Tango
