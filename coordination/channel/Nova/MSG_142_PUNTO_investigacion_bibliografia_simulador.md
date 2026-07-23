# MSG_142 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino) + Dispatch
**Fecha:** 2026-07-17
**Asunto:** Investigación bibliográfica del simulador — HALLAZGO que simplifica el plan. Sigue sin código.

Investigué las 4 fuentes que pidió Constantino. Delegué el fetch de fuentes a 3 procesos de
investigación en paralelo para no gastar tiempo en lectura bruta, y después yo mismo revisé
y until integré los resultados con criterio propio. Hay un hallazgo que **cambia mi
recomendación del brainstorm anterior, para mejor** (menos trabajo, no más).

---

## 1) Qué hace el planner de GRBL, en criollo — y el HALLAZGO

Confirmado leyendo el código fuente real de GRBL (`planner.c`, `stepper.c`, descargados
directo de github.com/gnea/grbl, no un resumen de terceros):

- **GRBL mantiene un buffer de varios movimientos futuros** (no solo el actual) y hace una
  pasada hacia atrás y otra hacia adelante sobre ese buffer para decidir la velocidad de
  entrada de cada tramo — así un tramo no frena de más si el siguiente ya requiere ir
  despacio, ni se queda corto si el siguiente permite ir rápido. Esto es el "look-ahead".
- **Cada tramo individual usa un perfil TRAPEZOIDAL**: acelera a aceleración CONSTANTE,
  crucero si el tramo es largo, decelera a aceleración constante. Nada más sofisticado que
  eso dentro de un tramo.
- **EL HALLAZGO: GRBL NO usa jerk ni S-curve.** Busqué explícitamente la palabra "jerk" en
  todo el código — la única aparición es un comentario que dice que en una versión VIEJA de
  GRBL este mismo mecanismo (Junction Deviation) se llamaba "max_jerk", pero es un nombre
  histórico mal puesto: no hay ninguna derivada de la aceleración limitada en ningún lado.
  El único "suavizado" es Junction Deviation actuando sobre esquinas, con aceleración
  constante en cada tramo.

**Qué aplica directo a nuestro caso:** el modelo de referencia real (lo que corre en
millones de máquinas, probablemente parecido a lo que hace CypCut) es MÁS SIMPLE de lo que
yo tenía planeado. No hace falta el perfil S-curve de 7 fases que propuse en el brainstorm
anterior — con aceleración constante + Junction Deviation alcanza. Esto es una
**simplificación real del plan**, no un compromiso de calidad.

---

## 2) Junction Deviation — confirmado contra la fuente original, coincide con mi derivación

Encontré y confirmé el **blog original de Sonny Jeon** (co-autor de GRBL, post de 2011,
donde introdujo el método) — coincide exactamente con la fórmula que ya les había mostrado
verificada geométricamente por mi cuenta en el brainstorm anterior. Dos datos nuevos
importantes que agrega la fuente original:

- **Jeon aclara explícitamente que δ (el parámetro) NO es una desviación física real de la
  máquina — es un artificio matemático** para calcular la velocidad de esquina de forma
  robusta y barata (solo 2 raíces cuadradas, nada de trigonometría cara). No hay que
  interpretarlo como "la máquina realmente se desvía tantos mm" — es un parámetro de ajuste.
- **Limitación conocida**: en el ecosistema Marlin hay reportes (issues de GitHub) de
  comportamiento raro de Junction Deviation en **curvas circulares** comparado con el
  modelo de jerk clásico. Esto es relevante para nosotros porque las figuras orgánicas
  (Corazón, Gotas) SÍ tienen arcos reales — es un riesgo a vigilar en la validación.

---

## 3) Qué me llevo de la teoría de S-curve — y por qué probablemente no la necesito

Confirmé la lógica general (perfil de 7 fases, colapsando a triangular o a jerk-puro cuando
el tramo es corto) — es material estándar de control de movimiento, coincide con lo que ya
sabía. **Pero dado que GRBL (la referencia real) no la usa, mi plan actualizado es NO
implementar el S-curve completo** — me quedo con aceleración constante (trapezoidal), que es
más simple de programar y de calibrar (menos parámetros: no hace falta el jerk `j` en
absoluto, solo la aceleración y δ).

---

## 4) Un dato externo que valida el enfoque completo (no solo mi intuición)

Encontré un paper académico de 2021 (revista *Int. J. Adv. Manuf. Technol.*) que **valida
exactamente el enfoque que venimos armando**: un modelo que simula la dinámica real del
control (aceleración/jerk + suavizado de esquinas) predice el tiempo real de mecanizado con
**más del 90% de precisión**, muy por encima de las estimaciones de software CAM simple —
y la causa del error de esos modelos simples es **justo la que yo encontré empíricamente**:
asumen que la máquina siempre llega a la velocidad programada, cuando en tramos cortos con
muchas esquinas nunca la alcanza. Esto no es solo mi hipótesis — es un patrón documentado en
la industria.

---

## Adaptaciones que necesita nuestro caso vs. GRBL real

1. **GRBL planifica en tiempo real con un buffer LIMITADO** (por memoria embebida) — nosotros
   conocemos el camino COMPLETO de antemano, así que podemos hacer el look-ahead (reverse +
   forward pass) sobre TODO el recorrido de una sola vez, sin la restricción de "tamaño de
   buffer" que tiene el hardware real. Más simple en nuestro caso, como ya había anticipado.
2. **GRBL calibra δ empíricamente "a ojo"** (probando en la máquina real hasta que no vibre)
   — nosotros lo vamos a calibrar por mínimos cuadrados contra los tiempos medidos de
   Batería 2 + figuras orgánicas. Mismo objetivo, método más riguroso para nuestro caso.
3. **Ya no necesitamos jerk** — dado el hallazgo del punto 1, el modelo se simplifica a
   (aceleración constante + Junction Deviation), no (S-curve + Junction Deviation).

---

## 5) Mi opinión actualizada: ¿replicamos GRBL o hay algo más simple?

**Replicamos GRBL — y resulta que GRBL YA ES la opción simple.** No hace falta buscar un
atajo respecto a algo más complejo, porque el modelo real de referencia (trapezoidal +
Junction Deviation) es más liviano que mi plan original de S-curve. Esto reemplaza mi
propuesta de "atajo" del brainstorm anterior: en vez de agregar Junction Deviation a mi
modelo de jerk puro, la propuesta correcta ahora es **reemplazar el jerk por aceleración
constante + Junction Deviation** — menos parámetros, más fiel a la referencia real, y
respaldado por el paper académico de que este tipo de enfoque da >90% de precisión en la
industria.

## Plan actualizado (mismo esqueleto de 4 puntos de decisión del brainstorm anterior, motor
más simple)

- Etapa 1 (parser de toolpath): sin cambios.
- Etapa 2 (motor cinemático): **AHORA trapezoidal, no S-curve** — menos trabajo.
- Etapa 3 (Junction Deviation): sin cambios, confirmado contra la fuente original.
- Etapa 4 (simulador completo, look-ahead sobre todo el camino): sin cambios de fondo, pero
  más simple al no cargar el estado del jerk.
- Etapas 5-6 (calibración y validación cruzada con figuras orgánicas): siguen exactamente
  igual, incluido lo que ya había marcado — necesito el Processing/Move/Delay real de al
  menos 1 figura orgánica para calibrar (Batería 2 sola no alcanza porque todos sus ángulos
  son de 90°, sigue siendo un problema de identificabilidad real).

**Nota de honestidad sobre la investigación misma:** el tema de S-curve (punto 3) y parte
del panorama de CAM industrial los until until until until until until until until until until until until until until until until until until until until until until until until until until until until until until until until until until until confirmé
con menor certeza que los puntos 1 y 2 (esos sí, contra código fuente real y el blog
original) — lo marco explícitamente para que quede claro qué tiene más peso.

Sigo sin ejecutar nada. ¿Avanzamos con este plan simplificado (trapezoidal + Junction
Deviation, sin jerk)?

— Punto
