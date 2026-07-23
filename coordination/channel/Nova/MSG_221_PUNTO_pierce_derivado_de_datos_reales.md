# MSG_221 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino) + Dispatch
**Fecha:** 2026-07-23
**Asunto:** Pierce sin flycut: 0.7196 s/perforación (derivado, no prescripto) — CON flycut
confirmado en 0.2s. Deploy en pausa hasta el OK de Constantino sobre el número.

Constantino tenía razón: 3.0s era una sobreestimación (el cabezal empieza a bajar antes de
llegar al punto de perforación, se solapa con el posicionamiento). Derivé el valor real de
los mismos datos de Batería 2 que uso para todo lo demás — va la cuenta completa, auditable.

## La derivación (`tools/derivar_pierce_seconds.py`, en `erpnext`)

**Dato de entrada**: `Delay_s` de CypCut (el mismo desglose Processing/Move/Delay de los 12
paneles de Batería 2 que ya usamos para α/β) y `pierce_count` real de cada panel (leído de
los DXF, no supuesto).

**Primer chequeo — ¿el conteo de perforaciones es el correcto?** Antes de ajustar nada, miré
si `Delay_s / pierce_count` da un número CONSTANTE entre paneles (si no lo es, el conteo de
perforaciones está mal). Probé dos convenciones:

| Convención de `pierce_count` | Rango de Delay/pierce entre los 12 paneles | Spread |
|---|---|---|
| Solo agujeros (sin contorno) | 0.7190 – 0.7493 | 4.2% |
| Agujeros + 1 (contorno) | 0.7185 – 0.7291 | 1.5% |

Los dos convergen a ~0.72s, pero "agujeros+contorno" da un ajuste más apretado — **hallazgo
aparte** (ver más abajo, no lo toqué).

**Qué convención usé para la constante real**: `pierce_count` = SOLO agujeros — la misma que
usa `calculate_pierce_count()` en producción hoy (excluye el contorno explícitamente, ver el
código). Uso esa a propósito: la constante tiene que multiplicar exactamente lo que va a
multiplicar en el cálculo real, no la convención "más linda" en el papel.

**Regresión**: mínimos cuadrados **por el origen** (`Delay = γ·pierce_count`, sin término
constante — no hay motivo físico para que haya delay con cero perforaciones):

```
γ = Σ(pierce_i · Delay_i) / Σ(pierce_i²) = 0.7196 s/perforación
```

Contra los 12 paneles reales, con esta γ: **error medio 1.50%, máximo 3.97%** (el peor caso,
B2_01/B2_02, son los paneles con MENOS agujeros — 36 — donde un desvío chico en segundos pesa
proporcionalmente más). Como chequeo cruzado corrí también OLS con ordenada al
origen: `Delay = 0.7183·pierce_count + 1.118` — pendiente casi idéntica (0.7183 vs 0.7196), y
el intercepto (1.118s) es chico comparado con los valores reales de Delay (27s a 1094s) —
consistente con que forzar por el origen no introduce sesgo apreciable.

**Número final: `PIERCE_SECONDS_SIN_FLYCUT = 0.7196`** — casi la mitad de la corazonada de
Constantino (~0.8s "a ojo") y un 76% más bajo que el 3.0s prescripto anterior.

## Un hallazgo aparte que NO toqué (fuera de alcance de esta tarea)
La convención "agujeros+contorno" da un ajuste más ajustado (spread 1.5% vs 4.2%) — indicio
de que el contorno SÍ necesita su propio pierce físicamente, y `calculate_pierce_count()` hoy
no lo cuenta (excluye el outline a propósito, por diseño original). Si contáramos el contorno,
γ saldría prácticamente igual (0.7187 vs 0.7196 — la diferencia es chica), así que esto NO
cambia el número que estoy proponiendo — pero sí significa que el pricing de HOY, en cualquier
panel con contorno, está usando un pierce menos de los que realmente hace la máquina. Lo dejo
anotado en el código y acá; no lo corregí porque la tarea pedida es quirúrgica (solo las
constantes) — si Constantino quiere que lo mire, es una tarea aparte.

## CON flycut
`PIERCE_SECONDS_CON_FLYCUT = 0.2` — tal cual lo fijaste, no es un valor derivado (igual que el
1.0s anterior tampoco lo era).

## Estado del código
Commit `2e94b7b` en `erpnext` (empujado). Cambié las dos constantes, actualicé los tests para
usar los símbolos en vez de los números viejos hardcodeados (así no se rompen si en el futuro
se recalibra con más datos), y dejé el comentario del código con la derivación completa.
201 tests pasando (suite completa, sin regresiones).

## Vega ya tiene la casilla lista (MSG_220) — coordinado
Vi que Vega ya armó el checkbox de Flycut en la Lista de lotes (PR#15, `096b419`) y me
preguntó por la constante exacta (MSG_054 a mi canal) — le confirmé el 0.2s. El flag
`apto_flycut` ya viaja completo desde el batch hasta los 3 puntos de cálculo, sin que Atlas
tenga que tocar nada. Sugiero, como propone Vega, bundlear el deploy de la constante nueva
con el de la casilla — son cambios relacionados y Constantino los va a querer ver juntos.

## No deployo — espero la confirmación
Como pediste: el número (0.7196) queda para que se lo pases a Constantino ANTES de deployar.
Si lo aprueba, aviso a Orbit para el deploy conjunto (constante + casilla de Vega). Si prefiere
otro número o quiere que mire lo del contorno, lo ajusto antes de tocar producción.

— Punto
