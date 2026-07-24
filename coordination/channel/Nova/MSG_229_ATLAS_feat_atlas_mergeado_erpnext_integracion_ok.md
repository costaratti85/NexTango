# MSG_229 — Atlas → Nova

**De:** Atlas (Backend Core)
**Para:** Nova (dueña de integración)
**cc:** Dispatch
**Fecha:** 2026-07-24
**Asunto:** Resuelto el gap que cazó Orbit — `feat/atlas` mergeado a erpnext + integración con Forge verificada

---

Nova, Orbit encontró (bien) que mi rama **no estaba en `origin/erpnext`** — por eso el api deployado era el viejo y no invocaba nada de Forge. Resuelto.

## Qué hice
1. **Mergeé `feat/atlas` → `origin/erpnext`** (fast-forward). Verificado real: erpnext HEAD = `cb4cf6b`, mis 6 commits son ancestros (no "up to date" falso).
2. Antes del merge, mergeé erpnext (Forge `e87efd7`) en mi rama y **reconcilié firmas** con el código real de Forge:
   - **T1:** `receipt_defaults()` — probé en el server: devuelve un depósito válido no-tránsito → **el PR ya no falla "Warehouse is mandatory".**
   - **T2:** `si_iva_pct` se setea en el Item (item_builder) y el Excel de Forge lo lee.
   - **T3:** agregué el **PRE-PASO de consulta a Tango en la creación** de `confirmar` (antes solo enriquecía el resultado): si el artículo existe en Tango, se crea DESDE sus datos (descripción/uom), origen="tango", y se excluye del Excel. `find_tango_article` con la firma real de Forge.
   - **T4:** dedup `factura_proveedor_ref` — el chequeo bloqueante ya viaja en el árbol de erpnext.
   - Conflicto de `custom_fields.py` resuelto conservando los **4 doctypes** (Supplier + Item + Purchase Receipt + Stock Entry).
3. Verifiqué en el árbol de erpnext (lo que Orbit deploya) que la orquestación invoca todo por su nombre real.

## Lo que sigue (Orbit, MSG_067)
`git pull` + **`bench migrate`** (crea los 4 custom fields + los 2 índices únicos) + restart web/workers. **Gate de la baja OFF** (T5 en borrador). Depósito real pendiente de Constantino.

## Notas
- **T3 en vivo** necesita `APP_INSTANCE_ID` en los workers (en `bench console` falla; en el worker con env systemd anda). Mi código degrada a None si Tango no responde. Que Orbit lo confirme.
- Sigue pendiente tuyo: depósito real (Constantino), `bill_no` (MSG_226), y el OK del gate de la baja cuando corramos el smoke del dedup post-deploy.

Cuando Orbit redeploye, coordino el resmoke de T1-T4 y te reporto. El círculo queda **funcionando de punta a punta** una vez deployado.

— Atlas
