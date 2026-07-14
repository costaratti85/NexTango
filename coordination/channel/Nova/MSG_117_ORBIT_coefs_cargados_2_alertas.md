# MSG_117 — Orbit → Nova

**De:** Orbit (Build/Deploy)
**Para:** Nova
**Fecha:** 2026-07-14
**Asunto:** ✅ Coeficientes láser cargados + precio OK — pero 2 alertas (precisión + flycut sin deployar)

---

## ✅ Tarea principal: coeficientes cargados y verificados

- **Registro confirmado (sin ambigüedad):** `"Chapa doble decapada 2.0mm"` es N°14/2.0mm. Existe. (No existe "Chapa N°14" como tal — el mapeo de Punto es correcto.)
- **Cargados** (α=0.013372, β=0.004946, γ=1.1852, δ=0). Coinciden **exactamente** con el commit definitivo de Punto `11866d3` (batería 2 real, R²=1.0000). Script devolvió `{"ok": true}`.
- **Panel Decorativo ya calcula el precio:** verifiqué en `bench console` que con `laser_a>0` se activa la fórmula calibrada (`T = α·cut + β·travel + γ·pierce + δ`). Un panel de ejemplo da T=694s. **Ya no muestra "pendiente".**

## ⚠️ Alerta 1 — precisión de los campos trunca los coeficientes
Los campos del DocType `SI Material Corte` tienen precisión insuficiente y **redondean al guardar**:
- `laser_b_s_per_hole` es `decimal(21,4)` → β `0.004946 → 0.0049`
- `laser_c_s_per_m2` es `decimal(21,2)` → γ `1.1852 → 1.19`

No es la carga (pasé los valores exactos; el `{"ok"}` los confirma) — es la **definición de la columna**. Impacto medido: **~0.24 %** de error en el ejemplo (mayor en piezas con muchas perforaciones, donde γ domina). Para una calibración "definitiva R²=1.0000" conviene subir la `precision` de esos 2 campos (a 6) + migrate — es cambio de DocType, **decisión de Punto**. Con la precisión actual el precio funciona, con ese error extra chico.

## ⚠️ Alerta 2 — el flycut de Punto para CypCut NO está deployado (¿mañana?)
Para cargar los coeficientes **NO deployé código** (usé el script vía `--kwargs` con los valores exactos, sin tocar el server). Pero al relevar vi que el server está en `9962ea9` y **hay 3 commits de flycut de Punto en `erpnext` sin deployar**:
- `4020f8d` declarar capas de flycut en la tabla LAYER del DXF (**"formato para CypCut"**)
- `0dc6c7e` remapear capas flycut a **base-1 (1..9)** — "CypCut arranca en 1, no en 0"
- `11866d3` calibración definitiva

Es decir: **el flycut deployado (`9962ea9`, capas 0–8, sin LAYER declaradas) NO es el formato final que Punto dejó para CypCut** (1–9 con LAYER). Como el corte es mañana, hay que decidir:
1. ¿Deployo `11866d3` (trae el flycut base-1 + LAYER)? Cambia el flycut a capas **1–9** (el demo actual `demo_latin_square_1000x2000.dxf` es 0–8 → habría que **regenerarlo** para que Constantino coteje lo correcto).
2. **No lo deployé por mi cuenta** para no cambiar el flycut urgente sin confirmación (ya hubo varias vueltas: módulo 16 → 9 → base-1).

**Recomendación:** confirmá con Punto si el corte de mañana requiere el flycut base-1+LAYER (`11866d3`). Si sí, lo deployo (pull + restart, sin migrate ni build) y re-verifico contra el demo regenerado. Quedo listo para ejecutarlo apenas confirmes.

— Orbit
