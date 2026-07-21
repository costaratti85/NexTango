# MSG_169 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino) + Dispatch
**Fecha:** 2026-07-21
**Asunto:** Resultados del experimento de validación v2 — CORTE validado (1.5% error), TRAVEL
necesitaba reajuste (y de paso destapó un problema viejo en Batería 2)

Commit `f72d41f` en `erpnext` (empujado). Cotejé los 15 archivos contra lo que midió
Constantino, componente por componente, medición a ciegas (no miré los números reales hasta
tener mis predicciones calculadas). Va el detalle honesto, incluyendo lo que no cerró.

## BLOQUE 1 — CORTE puro: validado, sin cambios

| Archivo | Predicho | Real | Error |
|---|---|---|---|
| radio_05mm | 0.230s | 0.236s | 2.6% |
| radio_15mm | 0.437s | 0.445s | 1.8% |
| radio_40mm | 0.968s | 0.969s | 0.2% |
| radio_100mm | 2.241s | 2.226s | 0.7% |
| angulo_015° | 1.470s | 1.497s | 1.8% |
| angulo_045° | 1.496s | 1.503s | 0.4% |
| angulo_090° | 1.539s | 1.517s | 1.5% |
| angulo_135° | 1.562s | 1.521s | 2.7% |
| angulo_165° | 1.575s | 1.523s | 3.4% |
| recta_020mm | 0.389s | 0.398s | 2.3% |
| recta_080mm | 1.200s | 1.198s | 0.1% |
| recta_250mm | 3.497s | 3.465s | 0.9% |

**Error medio 1.53%, máximo 3.39%** — con los parámetros de CORTE tal cual estaban
(v_tabla=74.0, a_max=625, δ=0.2), sin tocar nada. Tres experimentos independientes (rectas,
radios, ángulos) validan tres aspectos distintos del modelo por separado y los tres cierran.
No hace falta reajustar CORTE.

## Sobre "el ángulo casi no afecta el Processing" — qué implica

Tenés razón en la observación (15°→165°: solo 1.7% de variación real), y probé bajar/subir δ
para ver si mejoraba — la mejora es marginal (el error máximo baja de 3.4% a ~2.2-2.9% en un
rango AMPLIO de δ, de 0.2 a 1.2), así que no lo fuerzo (regla de siempre: no recalibrar hasta
que "cierre lindo" si la mejora es chica y el parámetro queda mal determinado).

**Por qué el modelo, aun prediciendo bien, no contradice la observación**: Junction Deviation
SÍ predice una `v_esquina` muy distinta entre 15° (120mm/s, no frena nada — más rápido que la
velocidad de tabla) y 165° (4.3mm/s, frena fuerte) — un rango de 27x. Pero como `a_max=625`
es alto respecto de `v_tabla=74`, la frenada y la recuperación alrededor de CADA esquina son
RÁPIDAS (unos pocos mm de distancia, unas pocas centésimas de segundo) — así que aunque la
velocidad en la esquina cambia mucho, el COSTO EN TIEMPO total de esa frenada es chico
comparado con los ~1.35s que tarda la figura completa. Esto es consistente, no es que el
modelo "no vea" el ángulo — es que a esta escala (recorridos de 100mm, a_max alto) el efecto
en tiempo total queda amortiguado. δ sigue débilmente identificado (ya lo había marcado en la
Etapa 3), pero no importa en la práctica: cualquier valor razonable predice bien.

## BLOQUE 2/3 — el corte de los 4 segmentos también cierra

| Archivo | Corte predicho | Corte real | Error |
|---|---|---|---|
| travel_cerca | 1.014s | 1.058s | 4.2% |
| travel_lejos | 1.014s | 1.058s | 4.2% |
| tamano_grande | 2.636s | 2.658s | 0.8% |

## BLOQUE 2/3 — TRAVEL: acá SÍ había que reajustar, y bastante

Con los parámetros viejos (los que salieron de Batería 2: v_rápido=129.5mm/s, a_max=750mm/s²):

| Archivo | Predicho | Real | Error |
|---|---|---|---|
| travel_cerca | 0.672s | 0.800s | **16.0%** |
| travel_lejos | 4.811s | 3.538s | **36.0%** |
| tamano_grande | 1.191s | 1.137s | 4.7% |

El patrón es claro: en distancias CORTAS mi modelo predecía MENOS tiempo que el real; en
distancias LARGAS predecía MÁS — señal de que la velocidad rápida real es más alta que la
calibrada y la aceleración real es más baja. Reajusté (grid grueso + fino) usando SOLO estos
3 datos limpios:

**v_rápido: 129.5 → 199.0 mm/s** (+54%) · **a_max_travel: 750 → 385 mm/s²** (−49%)

| Archivo | Predicho (nuevo) | Real | Error |
|---|---|---|---|
| travel_cerca | 0.797s | 0.800s | 0.4% |
| travel_lejos | 3.535s | 3.538s | 0.1% |
| tamano_grande | 1.139s | 1.137s | 0.2% |

**δ_travel sigue sin testear** — los 3 casos de este experimento son colineales (ángulo=0°
entre saltos siempre), no aportan ningún dato sobre esquinas en desplazamiento. Queda con el
valor viejo (0.005) sin validar — lo marco para no olvidarlo.

## El hallazgo incómodo — y por qué NO lo escondo
Antes de dar esto por cerrado, crucé el reajuste nuevo contra Batería 2 (12 paneles), para
ver si seguía siendo consistente:

| | Batería 2 (12 paneles) |
|---|---|
| TRAVEL viejo (129.5 / 750) | error medio 7.9%, max 34.5% |
| TRAVEL **nuevo** (199.0 / 385) | error medio **26.2%**, max **51.9%** |

El reajuste que hace perfecto match con este experimento controlado empeora MUCHO contra
Batería 2. Mi lectura honesta: esto **no** es evidencia de que el reajuste esté mal — es
evidencia de que el supuesto de orden boustrophedon de Batería 2 (nunca confirmado, marcado
como riesgo desde la Etapa 1) contaminó la calibración vieja de TRAVEL. Los parámetros viejos
"funcionaban bien" en Batería 2 porque estaban compensando un error de orden con un error de
velocidad — dos errores que se cancelaban parcialmente, no porque describieran la máquina
real. Este experimento nuevo tiene el orden VERIFICADO (nosotros lo fijamos, Constantino lo
reprodujo) — es el dato confiable. Recomiendo: **de acá en adelante, usar Batería 2 solo para
CORTE (ahí sigue andando bien, 1.4%/4.7%) y confiar en este experimento para TRAVEL**, no al
revés.

## Un hallazgo fuera de alcance, pero lo marco
El `Delay` medido (pierce) da ~0.76-0.89s por perforación en estos 15 casos — bastante menos
que la constante PRESCRIPTA que usa producción hoy (`PIERCE_SECONDS_SIN_FLYCUT = 3.0s`, en
`legacy_panel_adapter.py`). No toco esa constante (es de pricing, no de este simulador de
movimiento), pero lo dejo anotado por si a alguien le sirve revisarla aparte.

## Parámetros resultantes de esta etapa
- CORTE: `v_tabla=74.0`, `a_max_cut=625`, `δ_cut=0.2` — **sin cambios**, re-validado.
- TRAVEL: `v_rápido=199.0`, `a_max_travel=385` — **actualizado**. `δ_travel=0.005` — **sin
  testear todavía**, sigue siendo el valor viejo.

## Punto de decisión
No cerré ni deployé nada. Antes de dar la calibración por definitiva, dejo dos preguntas para
Constantino: (1) ¿el hallazgo de Batería 2/boustrophedon amerita un experimento de TRAVEL más
grande (más casos, quizás con δ_travel real, algún salto con giro) antes de confiar del todo
en 3 puntos? (2) ¿seguimos a una nueva etapa con figuras orgánicas (Corazón/Gotas/Cosmos),
ahora que sabemos cómo fijar la secuencia con Constantino, para la validación final de verdad?

— Punto
