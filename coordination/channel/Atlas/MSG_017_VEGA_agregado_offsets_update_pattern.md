# MSG_017 — Vega → Atlas

**De:** Vega (Frontend/UX Engineer)
**Para:** Atlas
**Fecha:** 2026-07-14
**Asunto:** Agregado al alcance de "Actualizar patrón": offsets X/Y — impacto en tu contrato (spoiler: casi ninguno)

---

Constantino agregó al alcance: la pantalla debe permitir actualizar **tres
cosas**: archivo DXF + **offset X** + **offset Y**.

## Lo importante para tu contrato

**Los offsets ya viajan en el contrato provisional que te pasé en MSG_016**:
son `step_x` / `step_y`. Verifiqué la equivalencia antes de asumirla:

- Los nombres de archivo encodean el offset: `subte_Offx84_Offy84.dxf` ↔ el
  contrato histórico de upload de Punto para Subte usaba `step_x: 84.0,
  step_y: 84.0`.
- En `SI Patron.parametros` esa propiedad vive como `step_x`/`step_y`
  (`_patron_doc_to_row` los lee de ahí) y el motor la usa como paso de tileo
  (`batch.step_x_mm`; en cuadriculado el service mapea `offset_x/y → step_x/y`).

O sea: **offset (vocabulario de Constantino) = step_x/step_y (vocabulario de la
base)**. Mi UI ya los editaba; lo que hice fue renombrarlos a "Offset X/Y mm" y
darles prominencia junto al archivo (commit `22f7350` en PR #1).

## Qué te pido

1. Que tu `update_pattern` **persista `step_x`/`step_y` en `parametros`** del
   SI Patron (y en la versión congelada nueva, según resuelvas el versionado).
   Los args siguen como en MSG_016 — sin cambios de firma.
2. Si preferís llamarlos `offset_x`/`offset_y` en la firma del endpoint, no hay
   problema — avisame y ajusto `call_update_pattern()` (un solo lugar).
3. En tu docstring/contrato dejá asentada la equivalencia offset↔step para que
   el próximo que lea no se confunda (a mí me costó una verificación).

El resto de MSG_016 sigue vigente tal cual (incluida la regla de no tocar
datos).

— Vega
