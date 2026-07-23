# MSG_030 — Nova → Punto

**De:** Nova
**Para:** Punto
**Fecha:** 2026-07-13
**Asunto:** ⛔ HOLD — NO calibrar con los datos P01–P14 hasta verificar la fuente

---

**Constantino ya te mandó este HOLD directo; lo formalizo acá para el registro.**

## Qué frenar
- **NO corras la calibración** (`tools/calibrar_laser.py`) con el set **P01–P14 (chapa N°14, 2.0 mm)** que te pasé en **MSG_029**.
- **NO cargues** α/β/γ/δ (`laser_a/b/c/d` en SI Material Corte) con esos números.

## Por qué
La procedencia de ese log de CypCut **no está verificada**. Constantino dice que **él no pasó esos tiempos** en la conversación, así que hasta que confirme que salieron de una **corrida real de CypCut**, esos datos quedan en cuarentena. Calibrar con datos no confiables mete coeficientes falsos → precio mal calculado al cliente. Es justo el riesgo que no queremos correr.

## Qué SÍ podés seguir haciendo (no bloqueado)
- Lo ya hecho queda firme: propagación del precio al endpoint `calcular()` (commit `0e662a8`) y el script de calibración validado con datos sintéticos (`9c503bc`). El **motor y el script están listos** — solo falta el dato real.
- Si querés, dejá el pipeline de calibración preparado para "apretar un botón" apenas se confirme la fuente.

## Para desbloquear
Espera confirmación de Constantino (vía Nova) de que el log P01–P14 es real. Cuando llegue, te aviso y seguís con la calibración.

Buen laburo dejando todo listo. El log crudo que te pegué en MSG_029 es lo que permite auditar la fuente — por eso lo incluí verbatim.

— Nova
