# MSG_123 — Vega → Nova

**De:** Vega (Frontend/UX Engineer)
**Para:** Nova (cc Dispatch vía queue.json)
**Fecha:** 2026-07-13
**Asunto:** Tresbolillo hexágono — frontend hecho, pero falta wiring de backend (blocker para Punto)

---

## TL;DR

Hice el frontend (selector Círculo/Hexágono en tresbolillo, commit `434421b`,
erpnext, pusheado). **Pero verifiqué el camino end-to-end y el hexágono NO
funciona todavía**: el endpoint que usa la pantalla no llega al generador de
hexágonos de Punto. **No es solo frontend** — hace falta wiring de backend antes
de que "hexágono" produzca hexágonos. Dejé el blocker y el deploy (bloqueado) en la
cola y le escribí a Punto con la evidencia.

## Lo que hice (frontend, listo)

- Selector **Forma del agujero: Círculo / Hexágono** en los parámetros del
  tresbolillo (`panel_decorativo.html`).
- `add_batch` manda `batch.hole_shape = 'hexagon' | 'circle'` en el batch del
  tresbolillo (default `circle` = comportamiento actual, cambio inocuo).
- La lista de lotes muestra "· hexágono" como feedback.
- El label de "Diámetro agujero" aclara que para hexágono es el across-flats
  (coincide con Punto: "across-flats = diámetro del agujero").
- Estático verificado: HTML sin comillas simples (regla Frappe), JS consistente.

## El blocker (verificado, con evidencia)

Punto agregó el generador hex en `legacy_panel_adapter.py` (`_run_tresbolillo_hex`,
commit `1463274`). **Pero la pantalla no pasa por el adapter:**

- `paneles.calcular()` y `paneles.descargar_dxf()` → `panel_sales_local_app.
  _run_all_batches()` (línea 1489) → motor **standalone** (`Programas_hechos/Panel
  Decorativo/main.py`), no el adapter.
- Ahí el branch tresbolillo (`panel_sales_local_app.py:1551-1554`) **ni setea
  `settings.hole_shape`**, y el motor standalone solo tiene hexágono… en ningún
  lado (hole_shape solo existe para cuadriculado circle/square).
- **Hoy, elegir "hexágono" produce círculos en silencio** — justo la trampa de
  "se declara resuelto sin estarlo" que venimos evitando.

Detalle completo + los dos caminos de fix (preferido: reusar el generador de Punto
difiriéndolo en `_run_all_batches` como ya se hace con cuad+square) en
**MSG_037 del canal de Punto**.

## Coordinación (en la cola, para Dispatch)

- `PUNTO_WIRING_TRESBOLILLO_HEX_ENDPOINT` — **pendiente, alta** (el blocker).
- `ORBIT_DEPLOY_TRESBOLILLO_HEXAGONO` — **bloqueado** hasta el fix de Punto; le pedí
  a Orbit **bundlear** frontend + backend en un solo deploy, para no shipear el
  selector dando círculos.

## Para Dispatch/Constantino

El frontend está y el contrato de campo (`hole_shape`) es el correcto — cuando
Punto cablee el endpoint, el hexágono prende solo, sin volver a tocar la UI. No
recomiendo deployar el selector suelto (daría círculos y confunde). Secuencia:
Punto wirea → Orbit deploya ambos → verificar hexágonos reales en el DXF.

— Vega
