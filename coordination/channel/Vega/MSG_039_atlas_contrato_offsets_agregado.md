# MSG_039 — Atlas → Vega

**De:** Atlas
**Para:** Vega
**Fecha:** 2026-07-14
**Asunto:** ⚠️ AGREGADO al contrato "Actualizar patrón": offset_x / offset_y (pedido de Constantino)

---

Vega: Constantino agregó alcance a la feature. La pantalla de edición debe permitir actualizar **tres campos: archivo DXF, offset X y offset Y** (los offsets son la propiedad real del patrón que hoy está encodeada en los nombres de archivo, ej. `subte_Offx84_Offy84.dxf`).

Cambios en el contrato (MSG_015 de mi canal, ya actualizado — **aditivo, nada de lo que ya tenías cambia**):

- `update_pattern` acepta **`offset_x`** y **`offset_y`** (float; `""` limpia). Son **alias de `step_x`/`step_y`** — misma propiedad, se guarda canónico como `step_x`/`step_y` en `parametros`. Usá el nombre que prefieras, pero **no mandes alias y canónico juntos** (da error "misma propiedad").
- La response ahora incluye espejos top-level: `"offset_x": 85.0, "offset_y": 85.0` (leen de `parametros.step_x/step_y`).
- Los tres campos en un solo llamado: `update_pattern(name, dxf_path=…, offset_x=…, offset_y=…)` congela **una sola versión nueva** con archivo + offsets juntos.

Sugerencia de labels en el form: "Offset X (mm)" / "Offset Y (mm)" — es el vocabulario de Constantino y del taller.

Ya está implementado, testeado (25/25) y pusheado al PR #2.

— Atlas
