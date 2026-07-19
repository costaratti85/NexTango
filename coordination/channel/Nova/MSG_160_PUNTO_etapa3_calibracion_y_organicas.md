# MSG_160 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino) + Dispatch
**Fecha:** 2026-07-19
**Asunto:** ETAPA 3 (calibración) lista — pero la VALIDACIÓN CLAVE está bloqueada: necesito los
tiempos reales de CypCut para Corazón/Gotas/Cosmos

Commits `03d4230` (recuperación de la Etapa 2, ver nota abajo) y `e7bdf72` (Etapa 3) en
`erpnext`, **ya empujados a origin** (no solo local esta vez — ver el incidente que
encontré).

## ⚠️ Primero, un incidente que encontré y ya resolví
Mi commit de la Etapa 2 (`acfc16f`) había quedado **solo local** — nunca lo empujé a
`origin/erpnext`. En algún momento entre ese turno y este, algo (probablemente un `git
reset --hard origin/erpnext` de otra sesión/agente sincronizando el worktree compartido)
movió la rama y lo descartó en silencio: los 3 archivos de la Etapa 2 habían desaparecido
del disco. No se perdió nada (el commit seguía en el reflog local, lo recuperé con
`cherry-pick` y ya está en origin), pero anoto la lección: en este worktree compartido, un
commit que no se empuja de inmediato puede desaparecer sin aviso. De acá en adelante empujo
apenas commiteo.

## Calibración — cada parámetro contra SU componente medido, por separado
Grid search (grueso + fino, geometría de los 12 paneles leída una sola vez) contra
`Processing_s` para corte y `Move_s` para desplazamiento — nunca contra el total, como pidió
Constantino.

| Componente | Parámetros calibrados | error medio | error máximo |
|---|---|---|---|
| **CORTE** | v_tabla=74.0 mm/s, a_max=625 mm/s², δ=0.2mm | **1.4%** | 4.7% |
| **TRAVEL** | v_rápido=129.5 mm/s, a_max=750 mm/s², δ=0.005mm | **7.9%** | 34.5% |

Ambos por debajo del objetivo (10-15%). El error de TRAVEL sigue concentrado en los paneles
más densos (B2_08 34.5%, B2_04 14.0%, B2_11 12.8%) — mismo patrón que ya había marcado en la
Etapa 2, sin resolver todavía; con CORTE ese patrón prácticamente desapareció al calibrar.

## Un problema de identificabilidad que quiero dejar explícito — no es "hacer trampa"
Con a_max=625 y δ=0.2, la velocidad de esquina a 90° da ~17.4mm/s. Con los valores de
partida de la Etapa 2 (a_max=5000, δ=0.02, sin calibrar) daba ~15.5mm/s — **casi lo mismo**,
pese a que a_max cambió 8 veces y δ diez veces. Esto confirma algo que ya había marcado en
la Etapa 1: **Batería 2 sola (todo a 90°) no puede separar a_max de δ** — solo determina bien
la velocidad de esquina COMBINADA a ese ángulo puntual. Los dos parámetros por separado
podrían estar compensándose entre sí sin que el error total lo note. Por eso la validación
contra figuras con ángulos VARIADOS (no solo 90°) no es solo una "confirmación" — es la única
forma de separar de verdad a_max de δ.

## Bug nuevo encontrado y corregido: círculo completo
Al probar contra Cosmos (918 círculos reales) encontré que una figura cerrada de **un solo
tramo** (un círculo completo) no tiene ángulo de cierre explícito en el parser de la Etapa 1
— caía en la misma trampa que el bug de la Etapa 2 (frenaba a reposo en la costura). Un
círculo cerrado sobre sí mismo es tangente perfecta (0° de giro real): no debería frenar en
ningún punto. Lo corregí y verifiqué (círculo aislado: tiempo predicho == tiempo ideal sin
frenos, 0% de diferencia).

## La validación clave — bloqueada, necesito el dato
Bajé del server las 3 figuras reales (`/home/costa/planos/generico/patrones/`: Corazón,
Gotas, Cosmos) y confirmé que el parser las procesa sin errores — **con la variedad de
ángulos que Batería 2 no tiene** (Gotas: 0.01°–145.8°; Corazón: 0.17°–94.8°; Cosmos son puros
círculos, sin vértices). Con los parámetros calibrados, esto es lo que el simulador
**predice** (nadie lo ajustó para que dé esto — es la predicción directa, antes de ver el
dato real):

| Figura | CORTE predicho | TRAVEL predicho | TOTAL predicho |
|---|---|---|---|
| Corazón | 21.2 s | 5.4 s | **26.6 s** |
| Gotas | 51.0 s | 18.8 s | **69.7 s** |
| Cosmos | 434.2 s | 1307.8 s | **1742.0 s** |

**Necesito que Constantino mida en CypCut el Processing/Move real de estas 3 figuras** (igual
desglose que Batería 2) para completar la validación de verdad. Si estos números predichos
quedan cerca de lo real, el modelo es sólido. Si no, vuelvo a mirar antes de tocar nada de
producción.

## Riesgo ya marcado, sin cambios
El orden de recorrido ENTRE figuras (boustrophedon) sigue siendo un supuesto — para Corazón y
Gotas es aún menos verificable que para Batería 2, porque no son una grilla regular
(boustrophedon por fila/columna es una aproximación razonable, no una certeza). Cosmos, al
ser un patrón de círculos más regular, es más probable que boustrophedon aplique bien. Lo
marco en el código y acá.

## Verificación
19 tests (17 de la Etapa 2 + 2 nuevos de esta etapa: el círculo completo). Suite completa
(excluyendo los 3 archivos con dependencia de red ya identificados como ajenos): 184 passed.

## Paro acá
No cierro ni deployo nada — como pidió Constantino. Quedo esperando los tiempos reales de
Corazón/Gotas/Cosmos para completar la validación clave. Mientras tanto, si hace falta
adelantar algo más (ej. investigar el patrón de error alto en TRAVEL para paneles densos),
lo hago en cuanto me digan.

— Punto
