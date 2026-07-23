# MSG_144 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino) + Dispatch
**Fecha:** 2026-07-17
**Asunto:** Adenda 2 a MSG_142/143 — cifras concretas y un matiz importante que ajusta mi recomendación

Terminó de llegar la parte de investigación más profunda (leyó papers completos con máquinas
reales de por medio, no solo abstracts). Trae cifras concretas y **un dato que ajusta —no
cambia del todo— mi recomendación anterior.** Se los paso porque es información que cambia
las expectativas de qué resultado es "bueno".

## Cifras concretas confirmadas (leyendo el texto completo, con máquina real de por medio)

| Fuente | Máquina real | Método simple (CAM) | Método cinemático (jerk/look-ahead) |
|---|---|---:|---:|
| Paper 2021, DMG Mori + control Heidenhain | fresado 5 ejes | error 36%–62% (hasta 168% puntual) | error 0.48%–5.59% |
| Paper 2015, Mori Seiki NMV5000 | fresado | tope previo del estado del arte: 75% de precisión (25% de error) | 95% de precisión (~5% error) |
| **Corte LÁSER (IEOM 2023, 338 piezas reales)** | — | — | **13% de discrepancia** en 27 piezas individuales comparadas contra tiempo real de máquina |
| VERICUT (foro de usuarios reales, no paper) | — | sin calibrar: hasta ±30%; calibrado: ±10% | con muchos movimientos cortos: hasta 40-50% de error |

**El dato más importante para nosotros: para corte LÁSER específicamente (no fresado), el
único benchmark real que encontré es 13% de discrepancia.** Esto es la expectativa REALISTA
para nuestro caso — no deberíamos apuntar a "menos de 5%" como en los papers de fresado
aeroespacial de alta precisión. Si nuestro simulador llega a 10-15% de error, eso YA sería
un resultado bueno, consistente con el estado del arte de la industria láser específicamente.

## Un dato contraintuitivo que confirma que estamos enfocando el esfuerzo bien
El paper de 2015 encontró que **el retraso del lazo de control (servo lag) es negligible**
— NO es el factor dominante del error. Lo que realmente determina el tiempo es el algoritmo
de generación de trayectoria (aceleración/jerk/suavizado de esquinas) — exactamente donde
venimos poniendo el esfuerzo.

## El matiz que ajusta mi recomendación anterior
Los usuarios de VERICUT (software de simulación de máquina real, usado en la industria)
reportan que su error grande con movimientos cortos viene de que **VERICUT asume
aceleración LINEAL (trapezoidal, como GRBL) mientras las máquinas reales usan una curva de
aceleración tipo "campana" (bell curve — o sea, jerk-limited, S-curve real).**

Esto es una tensión con lo que reporté en MSG_142: confirmé que GRBL (hardware de bajo
costo, código abierto) usa trapezoidal simple sin jerk. Pero el dato de VERICUT sugiere que
máquinas industriales más sofisticadas SÍ tienen una curva de aceleración real más suave
(jerk-limited) — y que asumir trapezoidal cuando la máquina real es "bell curve" genera
justo el tipo de error grande que yo mismo until until until until until until until until
había encontrado en mis intentos anteriores.

**No sé si CypCut se comporta más como GRBL (trapezoidal simple) o como las máquinas de los
papers de fresado (jerk real)** — no tengo forma de saberlo sin probar. Mi recomendación
ajustada: **empezar igual con el modelo más simple (trapezoidal + Junction Deviation)**,
como dije en MSG_142 — es más rápido de implementar y calibrar, y sigue siendo la base
correcta. Pero si al calibrar contra Batería 2 + figuras orgánicas el error se queda alto
(por encima de ese ~13-15% de referencia), el siguiente paso lógico, con evidencia real
detrás, sería agregar un perfil de aceleración no lineal (jerk) — no sería sorprendente que
hiciera falta. Lo dejo como una posible etapa 2b/2c si la etapa 2 simple no alcanza, en vez
de comprometerme de entrada a la versión más compleja.

## Ajuste al plan
Mismo esqueleto de MSG_142 (4 etapas + calibración + validación), con un punto de decisión
extra: en el "punto de decisión 3" (después de calibrar contra Batería 2 + orgánicas), si el
error queda por encima de ~15%, evaluamos agregar el perfil jerk antes de dar por buena la
Etapa 5. Si queda cerca del 10-13%, lo doy por un resultado consistente con lo que reporta la
industria y seguimos a producción.

Sigo sin ejecutar nada. Con esto, la investigación bibliográfica está completa.

— Punto
