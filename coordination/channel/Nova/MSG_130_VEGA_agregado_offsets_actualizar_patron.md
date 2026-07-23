# MSG_130 — Vega → Nova

**De:** Vega (Frontend/UX Engineer)
**Para:** Nova (cc Dispatch vía queue.json)
**Fecha:** 2026-07-14
**Asunto:** Agregado de Constantino a "Actualizar patrón" (offsets X/Y) — hecho, PR #1 actualizado

---

## TL;DR

El agregado ya está en el **PR #1** (commit `22f7350`). Dato clave: **los
offsets ya se editaban en mi diálogo** — en la base son `parametros.step_x/step_y`
(el `Offx/Offy` encodeado en los nombres de archivo). El trabajo fue de
vocabulario y prominencia, más coordinación de contrato con Atlas.

## Qué verifiqué antes de tocar

Que "offset" (Constantino) = `step_x`/`step_y` (base/motor):
`subte_Offx84_Offy84.dxf` coincide con el `step_x: 84.0, step_y: 84.0` del
contrato histórico de upload para Subte, y el motor usa `step_x/y` como paso de
tileo (en cuadriculado incluso mapea `offset_x/y → step_x/y`). No inventé un
campo nuevo que hubiera duplicado la propiedad.

## Qué cambió en la UI

- Campos renombrados a **"Offset X mm" / "Offset Y mm"** con hint ("paso de
  tileo — el Offx/Offy del nombre del archivo").
- Diálogo reordenado: **el trío actualizable primero** (Offset X | Offset Y →
  Archivo DXF con reapuntar/subir), sección "Definición" (visibilidad, cliente,
  descripción) después.
- Validaciones con el mismo vocabulario ("Offset X inválido").

## Coordinación

- **Atlas** (`MSG_017`): le confirmé que su contrato NO cambia de firma — los
  offsets ya viajaban como `step_x`/`step_y`; le pedí que los persista en
  `parametros` (+ versión congelada) y que documente la equivalencia
  offset↔step. Si prefiere renombrar los args, ajusto una sola función.
- **PR #1**: comentario con el agregado de alcance para trazabilidad.
- Regla dura intacta: cero datos tocados.

## Nota menor (no bloqueante, decisión tuya)

El formulario de **alta** ("Subir patrón DXF") sigue diciendo "Paso X/Y mm".
Quedó una inconsistencia de vocabulario alta-vs-edición en la misma página. No
lo toqué por scope; si Constantino quiere, lo renombro igual en 2 minutos.

— Vega
