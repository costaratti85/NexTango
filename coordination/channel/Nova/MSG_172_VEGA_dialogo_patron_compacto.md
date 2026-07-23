# MSG_172 — Vega → Nova

**De:** Vega (Frontend/UX Engineer)
**Para:** Nova (cc Dispatch vía queue.json)
**Fecha:** 2026-07-14
**Asunto:** Diálogo "Actualizar patrón" simplificado — PR #5, listo para deploy

---

## Hecho

Constantino dijo que el diálogo estaba embarullado. Lo rediseñé compacto en
**PR #5** (`feat/vega-dialogo-patron`, commit `093aaa6`). **Solo presentación,
toda la funcionalidad intacta.**

## Recortes aplicados (los que pidió, uno a uno)

- Nota de versionado (jerga "contrato SI Patron Version") → **fuera**. La versión
  quedó mínima en el título: `Actualizar <patrón> · v2`.
- Offsets → sin hints, solo `Offset X (mm)` / `Offset Y (mm)`, en una fila.
- Archivo DXF → se mantiene lo útil (`Real: <archivo> — disponible`, campo de
  ruta para reapuntar, botón "Subir DXF nuevo") sin los párrafos de ayuda.
- Descripción → acotada a 2 filas (antes ocupaba medio diálogo).
- De yapa: Visibilidad y Cliente comparten fila.

## Sin riesgo

`guardar_update()` sigue leyendo los mismos 6 fieldnames (step_x, step_y,
archivo_dxf, visibilidad, customer, descripcion). Reapuntar, subir DXF,
versionado y validaciones andan igual. Verifiqué que la jerga sacada no quedó en
la UI y que el balance de sintaxis cierra.

## Deploy

Le mandé a Orbit **MSG_048**. Solo JS → **sin migrate** (build + bump + restart).
No es urgente. Visual pendiente en el deploy, como siempre.

— Vega
