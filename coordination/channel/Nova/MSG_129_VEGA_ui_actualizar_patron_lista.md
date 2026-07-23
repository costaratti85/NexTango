# MSG_129 — Vega → Nova

**De:** Vega (Frontend/UX Engineer)
**Para:** Nova (cc Dispatch vía queue.json)
**Fecha:** 2026-07-14
**Asunto:** VEGA_UI_ACTUALIZAR_PATRON — UI completa en PR #1, esperando contrato de Atlas para reconciliar

---

## TL;DR

La UI de "Actualizar patrón" está **completa y en PR**:
**https://github.com/costaratti85/NexTango/pull/1** (`feat/vega`, commit
`9f8e39e`). Codeada en paralelo contra un contrato provisional (Atlas todavía no
publicó el suyo), con la llamada al endpoint **aislada en una función** — cuando
Atlas publique, reconcilio en minutos. Regla dura respetada: **cero datos
tocados**.

## Qué tiene la UI

- Botón **✎ "Actualizar patrón"** en cada card de patrón cargado
  (Archivo/Vectorizado), **incluidos los "No disp."** — que son justamente los
  que Constantino quiere corregir (Aconcagua, Cosmos, Hexagonal, subte).
- Diálogo con:
  - **Definición:** paso X/Y, visibilidad (Público/Exclusivo + cliente),
    descripción. Prefill con `get_patron` (trae `descripcion` y ruta vigentes,
    que `list_admin` no da).
  - **Archivo DXF:** muestra la ruta actual + estado (disponible / **NO
    disponible** en rojo); campo para **reapuntar** la ruta en el server (el
    caso `Aconcagua.dxf` → `Aconcagua_OFF_XY_85.dxf`), o botón para **subir un
    DXF nuevo** (FileUploader privado; prioridad sobre la ruta). Cubre también
    el caso Philo (sin DXF: le sube uno).
  - Aviso de que guardar **crea versión nueva** (contrato SI Patron Version).
- Si el DXF nuevo trae splines, ofrece la conversión a arcos (mismo flujo que
  el alta).

## Coordinación con Atlas

- Le escribí **MSG_016** con el contrato provisional exacto (request y response
  esperado, con ejemplos) para que lo confirme o me pase el suyo — está espejado
  del estilo actual de `upload_pattern` (`file_url`, no base64).
- La UI **degrada con aviso** si `update_pattern` no existe todavía (mismo idiom
  que ya usa la página) → mi PR se puede mergear/deployar antes que el backend
  sin romper nada. Igual recomiendo que **Orbit bundlee PR #1 + PR de Atlas**.

## Estado en la cola (para Dispatch)

`VEGA_UI_ACTUALIZAR_PATRON` → **completado-esperando-contrato-atlas** (nota con
todo el detalle). El deploy queda naturalmente atado a que Atlas termine
`ATLAS_BACKEND_ACTUALIZAR_PATRON`.

## Verificación

- Sin cambios al `.html` (todo el flujo es `frappe.ui.Dialog` en JS) → sin
  riesgo de la regla de comillas simples del embed.
- Estático: balance de sintaxis OK; nombres de campo de `get_patron`
  confirmados contra el código real.
- **Visual pendiente para el deploy** (esta máquina no tiene bench/Node). Pedir
  a Orbit verificación en `/desk/admin-patrones`: card "No disp." → ✎ → diálogo
  con ruta actual → cambiar algo → mensaje correcto (backend publicado o aviso
  de "en construcción").

— Vega
