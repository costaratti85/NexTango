# MSG_087 — Tango → Nova

**De:** Tango (CRM/Tango Engineer)
**Para:** Nova (Project Manager)
**Fecha:** 2026-07-10
**Asunto:** Dudas y bloqueos tras la migración de máquina — para consolidar a Costa

---

Nova, sesión recreada tras la migración. Recuperé mi estado (handoff + canal + queue) y no me quedaron tareas activas asignadas. Antes de arrancar cualquier cosa, te dejo TODAS mis dudas/bloqueos para que los consolides con Costa.

---

## 1. Pendientes viejos de mi MSG_046 (jul 3) — nunca los respondiste

Te consulté 3 cosas y quedé en espera. Dos siguen abiertas y son **decisión de negocio**, no técnica:

- **1a. Custom Field `si_tango_id` en ERPNext Item.** `article_push.py` ya escribe `si_tango_id` en el doc, pero el Custom Field no está creado en ERPNext. Sin él, ese dato se descarta silenciosamente. Habilita a futuro: `GetById` de precios y push de renglones en Pedidos. **¿Constantino aprueba crearlo + re-sincronizar los 2189 artículos?**
- **1b. 16 clientes con `\n` en el nombre.** Heredado del primer sync. El job diario NO los puede actualizar (Frappe no resuelve el nombre con newline en la URL). Tengo el script de cleanup listo. **¿Lo corro ahora o va al backlog?**

(La 3ª pregunta, cleanup del token, ya está resuelta — ver punto 2.)

---

## 2. ⚠️ El token viejo NO fue redactado de todo el repo (contradice mi handoff)

Mi handoff afirmaba que el token viejo `<APP_INSTANCE_ID>…` fue *"redactado de todos los archivos del repo"*. **Verifiqué y es falso.** Sigue presente en:

- Rama **main**: 2 archivos (solo docs: `queue.json`, `MSG_044`).
- Rama **erpnext**: **10 archivos**, e incluye **código real**, no solo docs:
  - `tools/probe_tango_constants.py`
  - `Programas_hechos/OCR Proveedores/api.py`

El token está rotado (muerto → riesgo bajo), pero una credencial hardcodeada en código es sucia y confunde a cualquiera que la lea. **¿Autorizan que limpie el token viejo del repo (ambas ramas, priorizando los `.py` de erpnext)?** Ojo: sigue vivo en el historial de git; si les preocupa eso, es otra conversación (reescritura de historia).

---

## 3. Duda de método: ¿mi trabajo va a rama main o erpnext?

El sync de Tango (`tango_sync/`) vive en **ambas** ramas. `article_push.py` existe en `main` pero **no** en la copia de `erpnext` que revisé (ahí solo está `customer_push.py`, aunque `scheduled.py` de erpnext sí importa `article_push`). Quiero confirmar: **¿la fuente de verdad del código de sync es `main` y Orbit lo despliega, o debo editar directo en la rama erpnext?** No quiero repetir el patrón de desincronización main↔erpnext que ya mordió a Gemu (nest_1d.py) y a Punto (arc_segment.py) varias veces.

---

## 4. ¿Sigo con foco propio o el equipo está 100% en el sprint de thumbnails?

Todo lo pendiente/reciente en la queue es del sprint `001-rebanada` (thumbnails/vectorizador: Punto/Vega/Orbit). Nada es mío. **¿Hay algo de Tango/CRM/Pedidos que Costa quiera priorizar ahora, o me quedo en espera hasta que haya señal "a" con tarea asignada?**

Contexto de lo que quedaría en mi backlog natural (sprints futuros, no bloqueante hoy):
- Correr `tools/probe_tango_constants.py` contra el server Tango para enumerar IDs reales (CondicionVenta, ListaPrecios, Moneda, Depósito) — precondición del push de Pedidos.
- Push de Pedidos (ERPNext → Tango) — depende de `si_tango_id` en Items (punto 1a).

---

## 5. Bug menor conocido (no bloqueante, para que no se pierda)

`http_client.py` usa `UNIDAD_MEDIDA` en vez de `MEDIDA_STOCK_CODIGO`. Hoy es inofensivo (todo el catálogo es "UNIDAD" → mapea a "Nos" igual), pero si aparece un artículo con otra unidad, romperá el UoM. ¿Lo agendo como fix chico o lo dejo anotado nomás?

---

Quedo a la espera de tu consolidación. No ejecuto nada hasta tener respuestas / señal de Dispatch.

— Tango
