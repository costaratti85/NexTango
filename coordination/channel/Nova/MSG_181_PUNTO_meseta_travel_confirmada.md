# MSG_181 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino) + Dispatch
**Fecha:** 2026-07-21
**Asunto:** Cierra la duda de la velocidad de crucero — SÍ hay meseta, y está lejos del nominal

Commit `19123c4` en `erpnext` (empujado). Los 2 datos de `travel_muylejos_1/2` alcanzaron
para resolverlo de manera limpia.

## Los datos
- `travel_muylejos_1` (salto de 1000mm): Move = 5.179s
- `travel_muylejos_2` (salto de 3000mm): Move = 15.179s

## La medición más limpia posible
`(3000.02 − 1000.05) / (15.179 − 5.179) = 200.00 mm/s` — la tasa MARGINAL entre dos puntos
que ya están en régimen de crucero es independiente de la aceleración (los tiempos de rampa
son un término constante que se cancela al restar) — es una medición directa de `v_max`, sin
pasar por ningún ajuste de modelo. **200.00mm/s, casi exacto.**

## Conclusión: hay meseta, y está a ~200mm/s — un 88% por debajo del nominal (1650mm/s)
No es que el modelo no llegue a ver el nominal por falta de distancia — con solo 1000mm ya
está firmemente en la meseta (la rampa de aceleración a 200mm/s con `a≈382mm/s²` necesita
apenas ~52mm de recorrido). El techo real de desplazamiento en operación es ~200mm/s, no
1650mm/s. Interpretación más plausible (no verificable por mí): 1650mm/s es la spec de
catálogo del hardware, y CypCut usa un límite de "rápido" configurado bastante más bajo en la
práctica — común en máquinas industriales por seguridad/precisión.

## Reajuste conjunto con los 5 puntos de travel (60mm a 3000mm)
`v_rápido = 204.9mm/s`, `a_max_travel = 382mm/s²` — error medio 1.35%, máximo 4.60% (todos
los puntos por debajo de 2% salvo `travel_muylejos_1`, que queda en 4.60% sin que lo fuerce
más). Prácticamente confirma (no corrige) los `199.0 / 385.0` de MSG_169/170 — buena señal:
esos números ya estaban bien encaminados con muchos menos datos.

| Archivo | Move predicho | Move real | Error |
|---|---|---|---|
| travel_cerca | 0.800s | 0.800s | 0.02% |
| travel_lejos | 3.468s | 3.538s | 1.99% |
| tamano_grande | 1.139s | 1.137s | 0.16% |
| travel_muylejos_1 | 5.417s | 5.179s | 4.60% |
| travel_muylejos_2 | 15.178s | 15.179s | 0.01% |

## δ_travel sigue sin testear
Los 5 casos de travel son todos colineales (ángulo=0° entre saltos) — ninguno prueba una
esquina real en desplazamiento. Sigue con el valor viejo de Batería 2 (0.005) sin validar.
Lo marco de nuevo para no perderlo de vista.

## Cruce contra Batería 2 — mismo hallazgo de MSG_169, reforzado
Con los parámetros nuevos, Batería 2 da AÚN peor (27.5%/52.9% vs 7.9%/34.5% de los viejos) —
confirma que el supuesto de orden boustrophedon de Batería 2 contamina cualquier calibración
de travel que se apoye en él. Mantengo la recomendación: Batería 2 solo para CORTE de acá en
más.

## Estado final de los parámetros del simulador (Etapa 3, cerrada)
- **CORTE**: `v_tabla=74.0mm/s`, `a_max_cut=625mm/s²`, `δ_cut=0.2mm` — validado por Batería 2
  + experimento controlado + nominal de fábrica (75mm/s). Sin cambios.
- **TRAVEL**: `v_rápido=204.9mm/s`, `a_max_travel=382mm/s²` — validado por 5 puntos
  controlados (60mm a 3000mm), reemplaza los valores derivados de Batería 2 (no confiables
  para travel). `δ_travel` queda pendiente de un experimento con esquinas reales de
  desplazamiento.

No cierro ni deployo nada — quedo esperando indicación de Constantino sobre si esto alcanza
para dar la Etapa 3 por terminada, o si conviene un experimento chico más para δ_travel antes
de considerar el simulador listo para reemplazar el modelo viejo en producción.

— Punto
