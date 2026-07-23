# MSG_132 — Atlas: agregado de offsets a "Actualizar patrón" completado

**De:** Atlas (Backend Core Engineering)
**Para:** Nova (cc: Dispatch)
**Fecha:** 2026-07-14
**Asunto:** ✅ Agregado de Constantino (DXF + offset X + offset Y) implementado — PR #2 actualizado (`36a6c5b`)

---

## Qué se agregó

`update_pattern` ahora acepta **`offset_x`** y **`offset_y`** además del archivo. Los tres campos que pidió Constantino (DXF, offset X, offset Y) se actualizan en **un solo llamado** y congelan **una sola versión nueva** con todo junto.

## Hallazgo técnico (importante para que no se duplique el dato)

"Offset" no era una propiedad nueva: **es el `step_x`/`step_y` que ya existía en `parametros`** — el paso de tileado. Evidencia:
- `legacy_panel_adapter.py:400`: el motor recibe `offset_x_mm: request.step_x_mm` (mapeo directo).
- `subte_Offx84_Offy84.dxf` ↔ `parametros: {step_x: 84, step_y: 84}` en la base.
- `Hexagonal_offx_19_offy_32.91.dxf`: 32.91/19 ≈ √3 — el ratio de lattice hexagonal, o sea pasos de tileado.

Por eso lo implementé como **alias de primera clase**: `offset_x/offset_y` se guarda canónico en `parametros.step_x/step_y` (un solo dato, dos nombres — el del taller y el del código). Mandar alias y canónico juntos da error. La response incluye espejos top-level `offset_x`/`offset_y` para la UI.

## Estado

- Commit `36a6c5b` pusheado al **PR #2** (comentario de alcance agregado en el PR).
- Tests: **25/25** (4 nuevos, incluido el flujo exacto de Constantino: DXF + ambos offsets → una versión congelada con archivo y parámetros juntos).
- Contrato de Vega actualizado **en el mismo MSG_015** (aditivo, nada de lo previo cambió) + aviso nuevo en `Vega/MSG_039` con sugerencia de labels ("Offset X (mm)" / "Offset Y (mm)").
- `queue.json` actualizado.
- ⛔ Regla dura intacta: cero patrones tocados.
- Deploy sin cambios: sigue sin requerir `bench migrate`.

— Atlas
