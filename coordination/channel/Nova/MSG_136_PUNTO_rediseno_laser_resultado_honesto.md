# MSG_136 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino) + Dispatch
**Fecha:** 2026-07-16
**Asunto:** Rediseño de la fórmula — RESULTADO: ningún modelo simple cierra. Reporto el hallazgo, no un ajuste lindo.

Commit `1c79791`. Con el desglose real que me pasaron, corrí las 2 variantes de cada
componente que pidió el consejo. **Ninguna está lista para producción.** Prefiero reportar
esto con toda la evidencia a maquillar un ajuste que no es real.

## DESPLAZAMIENTO — contra el `Move time` real

| Variante | Error medio | Error máx | Problema |
|---|---:|---:|---|
| **A** — salto por salto, jerk reposo-a-reposo, max(tx,ty) | 6.5% | **23.3%** | `t_torcha` sale **negativo** (-0.28s) — signo físicamente incoherente |
| **B** — fila entera de agujeros = 1 solo movimiento | 46.9% | **128%** | Mucho peor — descarta la hipótesis de "cero freno entre saltos" |

La variante A tiene R²=0.998 mirando el ajuste global, pero eso es engañoso — el error por
panel individual llega a 23%, inaceptable para cotizar. Y el signo negativo de `t_torcha`
es una señal de alarma: el ajuste está compensando algo, no describiendo la física.

**El hallazgo real:** calculé la correlación entre "cuántas columnas tiene el panel" (qué
tan denso/regular es el patrón) y "cuánto se desvía el modelo A del tiempo real":
**correlación = -0.79** (fuerte). Los paneles densos (muchos agujeros en fila) tardan
MENOS de lo que predice "cada salto frena por completo", pero MÁS de lo que predice "la
fila entera es un solo movimiento sin pausas". La verdad está en un punto intermedio que
ninguno de los dos modelos simples captura — probablemente el motor no frena a velocidad
CERO en cada punto, sino a una velocidad de "esquina" mayor que cero (como hace cualquier
control CNC moderno con look-ahead).

## CORTE — contra el `Processing time` real

| Variante | Error medio | Error máx |
|---|---:|---:|
| **A** — cada lado del cuadrado = jerk 1D en cada esquina de 90° | 30.1% | 60.7% |
| **B** — velocidad de corte nominal constante (sin jerk) | 17.3% | 35.2% |

Mismo patrón de fondo: los paneles densos rinden mejor de lo que ninguno de los dos modelos
predice. La variante B es simplemente un promedio, no explica el patrón.

## Lo que NO hice, a propósito
- **No cargué ningún coeficiente nuevo a producción.** `set_laser_coefs.py` sigue con α/β
  de la calibración anterior; el pierce sigue prescripto (3s/1s), sin cambios.
- **No forcé un ajuste con más parámetros hasta que "cierre".** Eso sería repetir
  exactamente el error de fondo que estamos corrigiendo — un ajuste matemático que reproduce
  el número pero no la física.

## Próximo paso que propongo (no implementado, necesita validación)
Un modelo de **velocidad de esquina no-cero**: en vez de que el láser frene a v=0 en cada
punto, frena hasta una velocidad de cornering que depende del jerk lateral permitido y del
ángulo (90° para cuadrados). Esto es estándar en control CNC y explicaría por qué las
secuencias densas rinden mejor. Agrega al menos 1 parámetro nuevo, y necesitaría validarse
con el mismo rigor (contra Processing/Move real, no contra el total).

**Alternativa más simple si prefieren no seguir por ese camino:** quedarnos, por ahora, con
el modelo ANTERIOR (regresión conjunta de 4 parámetros contra el total, α=0.013372,
β=0.004948) para pricing — sabiendo que su desglose interno es matemático y no físico (ya
lo reportamos), pero su error total medido fue bajo (0.66% máx). No es lo que pidió el
consejo, pero es lo único que hoy tiene un error aceptable para cotizar. Ustedes deciden.

## Verificación
- 22 tests en el módulo (`test_analisis_laser_fisico.py`), incluidos 2 tests de **regresión
  documentada**: verifican que el error actual sigue siendo alto y que la correlación de
  densidad sigue siendo fuerte — si alguien mejora el modelo después, estos tests van a
  fallar y avisar del cambio, en vez de quedar silenciosamente desactualizados.
- Suite completa: 161 passed (3 fails pre-existentes de entorno, sin relación, confirmado
  en turnos anteriores con git stash).

**Resumen para Constantino:** hice la cuenta con tus datos reales, dos hipótesis por
componente, y ninguna cierra bien todavía. No es un fracaso del enfoque — es evidencia de
que el modelo necesita un ingrediente más (velocidad de esquina, no frenado total) que no
estaba en la propuesta original. Prefiero decirte esto ahora que entregarte un número que
no vas a poder confiar.

— Punto
