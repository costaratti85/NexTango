# MSG_143 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino) + Dispatch
**Fecha:** 2026-07-17
**Asunto:** Adenda a MSG_142 — terminó de llegar la investigación de CAM/precisión, con mejor verificación

Uno de los procesos de investigación siguió trabajando después de que mandé MSG_142 y volvió
con resultados MEJOR verificados (leyó papers completos, no solo resúmenes). Esto reemplaza
la parte más floja de mi reporte anterior (el punto de "CAM/estimación de tiempo industrial",
que until until until until until until había marcado como poco confirmado).

## Confirmado leyendo la fuente completa (no resumen)

**Paper de 2021** (Ward, Sencer, Jones, Ozturk — *Int. J. Adv. Manuf. Technol.*, arXiv
2102.02062 — PDF completo, 8 páginas, leído entero): confirma exactamente la distinción que
veníamos suponiendo:
- **CAM tradicional**: *"simula el movimiento de la máquina en base al feedrate comandado y
  la geometría del camino"* — sin modelar cómo el control real interpola. Impreciso.
- **Simulación cinemática avanzada**: modela la dinámica real del interpolador con
  look-ahead y una **"velocidad mínima de esquina" calculada analíticamente** a partir de
  los límites cinemáticos de la máquina — el mismo mecanismo que Junction Deviation, en
  espíritu. **Cita textual: "los tiempos de ciclo reales pueden estimarse con más del 90% de
  precisión", superando ampliamente al CAM tradicional.**

## Hallazgo nuevo — relevante para nuestro caso específico

**Patente real de la industria (US6728657, Mori Seiki):** describe un método HÍBRIDO —
fórmula cinemática (distancia + velocidad + aceleración) para el movimiento de los ejes,
**más una base de datos que se actualiza continuamente con tiempos REALES medidos en cada
corrida de la máquina** para las funciones auxiliares (cambios de herramienta, etc.).

Esto es literalmente la misma filosofía que ya veníamos aplicando sin saberlo: simulación
cinemática para el movimiento (corte + desplazamiento) + un valor PRESCRIPTO/medido para el
perforado (que ya decidimos tratar como constante, no como algo derivado del movimiento
puro). No es una coincidencia rara — es el patrón estándar de la industria para separar
"lo que se puede modelar por física" de "lo que se mide y prescribe directo".

## Honestidad sobre lo que NO se pudo confirmar
Varias cifras de error que habían aparecido en búsquedas preliminares (3%, 8%, 36%, etc.)
**no se pudieron verificar leyendo la fuente real** (papers detrás de paywall) — quedan
descartadas. La única cifra que sostengo con confianza es el ">90%" del paper de 2021.

Tampoco se pudo confirmar el algoritmo interno de los CAM comerciales de corte de chapa
(Trumpf TruTops, Hypertherm ProNest, SigmaNEST) — sus páginas oficiales no publican el
detalle, lo tratan como propiedad intelectual. Esto confirma algo que ya sospechábamos: no
vamos a poder "copiar" el algoritmo exacto de CypCut — solo aproximarlo con el modelo de
referencia (GRBL: trapezoidal + Junction Deviation) y calibrarlo contra datos reales, que es
justo el plan.

No cambia la recomendación de MSG_142 — la refuerza con evidencia externa mejor verificada.

— Punto
