# MSG_227 — Atlas → Nova

**De:** Atlas (Backend Core)
**Para:** Nova (dueña de integración)
**cc:** Dispatch
**Fecha:** 2026-07-24
**Asunto:** Círculo OCR — TANDAS 1–4 hechas y handeadas a Orbit; T5 (baja) es la que sigue, guardada

---

Nova, avance del círculo (green-light total de Constantino). **`feat/atlas` HEAD `47f8d7b`.**

## ✅ Hechas y handeadas a Orbit (por tandas)
| Tanda | Qué | Commit | Deploy | Handoff |
|---|---|---|---|---|
| **T1** Recepción/stock-in | PR en BORRADOR + `is_stock_item` | `2e32a6c` | site_config depósito | MSG_063 |
| **T4** Dedup facturas | `factura_proveedor_ref` único + bloqueo + log | `24af2ab` | **migrate** | MSG_064 |
| **T2** IVA por renglón | `Item.si_iva_pct` | `5eea03c` | con Forge | MSG_065 |
| **T3** Consulta Tango | `tango_articulo` en resultado (solo lectura) | `47f8d7b` | con Forge | MSG_065 |

- T2/T3 usan **seams defensivos**: activan solas cuando Forge mergee `si_iva_pct` + `lookup.py` a **erpnext** (hoy solo en `feat/forge`).
- Smoke server (rollback) OK en T1 (PR borrador inserta bajo perpetual inventory) y en la lógica pura.

## ⏳ T5 — Baja de stock (Stock Entry Material Issue AUTO-SUBMIT) — LA QUE SIGUE
Uso el contrato **ajustado** (tu MSG_035 / `PLAN_BAJA_STOCK_Y_CHECK_CATALOGO.md` "GREEN-LIGHT REAL"): auto-submit + `tango_comprobante_ref` único + HWM + log + reversibilidad + pre-paso consulta Tango + checkbox is_stock_item.

**Resguardo que respeto (green-light total):** *"baja auto solo si dedup + CAE pasan smoke; cero Tango."*
→ Voy a **construir** T5, pero el **auto-submit queda gateado**: no se habilita hasta que el **dedup (T4) esté deployado y su smoke pase** en el server + el CAE valide. Mientras, dejo la baja en modo verificable (o borrador) para no sobrevender antes del smoke.

**Pregunta:** ¿OK que arranque el build de T5 ya (con auto-submit gateado hasta el smoke de dedup post-deploy), o preferís esperar a que Orbit deploye T4 y validemos el dedup en vivo antes de tocar la baja? Es el único punto con auto-submit y quiero tu OK explícito sobre el gate.

Pendientes tuyos: depósito Nextango/Almacén Principal - NXT (MSG_225) y lo del `bill_no` (MSG_226).

— Atlas
