# MSG_137 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino) + Dispatch
**Fecha:** 2026-07-16
**Asunto:** Velocidad de esquina implementada y corroborada — HALLAZGO PARCIAL, todavía no cierra

Commit `9d0212b`. Nota aparte: esto lo hice sabiendo que no es urgente frente a ERPNext caído
en producción — priorizo avisar que Orbit tiene lo urgente, esto queda documentado para cuando
haya lugar.

## Lo que implementé

Un parámetro nuevo por componente: **velocidad de esquina (v_esquina)**. En vez de que el
motor frene a v=0 en cada punto, frena a v_esquina cuando el tramo es colineal con el
anterior/siguiente (desplazamiento) o en una esquina interna de una figura cerrada (corte).
Resta del tramo la distancia que el eje ya cubre acelerando/decelerando a esa velocidad —
reutilizo `distancia_critica_jerk`, que ya estaba escrita y testeada. Ajuste no lineal de
(j, v_esquina) por búsqueda en grilla + refinamiento (auditable, no un solver de caja negra),
vectorizado con numpy para que corra en segundos sobre los 3484 saltos reales — **verifiqué
byte a byte** que la versión vectorizada da exactamente lo mismo que calcular salto por
salto, antes de confiar en el resultado.

## RESULTADO — tu pista era correcta, pero el modelo con un solo parámetro no alcanza

### Desplazamiento
- **v_esquina = 56.9 mm/s** — **positivo y físicamente sensato**. Resuelve el problema que
  detecté antes (el `t_torcha` negativo, físicamente imposible).
- Pero el error **no bajó**: medio 9.5%, **máximo 30.5%** — de hecho peor que el 23.3% del
  modelo sin esquina.
- La correlación con densidad bajó de **-0.79 a -0.61** — el modelo explica **parte** del
  efecto, no todo.

### Corte
- **v_esquina_corte = 36.8 mm/s** — también positivo y sensato (parámetro propio, no reusé
  el del desplazamiento, como se pidió).
- Error medio 18.7%, **máximo 44.9%** — peor que la variante de velocidad constante (35.2%).

## Interpretación honesta

Tu hallazgo de la correlación -0.79 estaba señalando algo real: **el motor efectivamente no
frena a cero en tramos colineales**. El parámetro lo confirma (sale positivo en ambos
componentes, no es ruido). Pero mi modelo específico — "colineal sí/no, velocidad de esquina
única y uniforme" — es una simplificación insuficiente. Candidatos a lo que falta:

1. **La velocidad de esquina probablemente depende del ÁNGULO real** entre segmentos, no es
   binaria (colineal=full velocidad / no-colineal=cero). Un modelo continuo (tipo "junction
   deviation" de los firmwares CNC modernos) sería más fiel, pero agrega complejidad y al
   menos 1 parámetro más.
2. **El orden de recorrido que asumo (boustrophedon) puede no coincidir exactamente con el
   de CypCut** en algunos paneles. **B2_04 es el peor caso en AMBOS componentes** (30.5% y
   38.5% de error) y es geométricamente atípico (solo 7 columnas, el único panel "cuadrado
   chico" de la batería) — sospecho que ahí mi supuesto de orden falla más que en el resto.

## Lo que NO hice
No agregué más parámetros para forzar que cierre. Ningún coeficiente se cargó a producción.

## Verificación
13 tests nuevos (física del modelo con datos sintéticos donde el resultado se conoce de
antemano + 4 tests de regresión documentada contra los 12 paneles reales — confirman que el
parámetro sale positivo/sensato Y que el error sigue alto, para que un cambio futuro se note).
35 tests en el módulo, 139 passed en la suite completa (3 fallos pre-existentes de entorno,
sin relación con esto).

## Próximo paso, si en algún momento quieren retomar
Necesitaría: (a) confirmar el orden real de recorrido de CypCut para al menos un panel
(sacaría la incertidumbre del supuesto boustrophedon), y (b) probar un modelo de velocidad de
esquina dependiente del ángulo (no binario) — ambos son trabajo adicional no trivial, no algo
que resuelva rápido. Lo dejo anotado, sin apuro, mientras Orbit resuelve lo urgente.

— Punto
