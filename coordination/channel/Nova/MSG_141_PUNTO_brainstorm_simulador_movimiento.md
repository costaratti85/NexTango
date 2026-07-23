# MSG_141 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino) + Dispatch
**Fecha:** 2026-07-17
**Asunto:** Brainstorm del simulador de movimiento — para debatir, SIN código todavía

No ejecuté nada. Esto es la discusión de diseño que pediste, en los 5 puntos.

---

## 1) Junction Deviation, en criollo

Pensalo como tomar una curva en auto. No frenás a cero para doblar — tomás la curva a una
velocidad que depende de qué tan cerrada es: una curva suave (casi seguir derecho) la tomás
casi sin bajar; una esquina de 90° bastante más despacio; una vuelta en U prácticamente
tenés que parar. Es exactamente lo que hace GRBL/Marlin (el firmware que maneja el
movimiento en la gran mayoría de máquinas de corte/impresión CNC de este tipo) en cada
vértice del camino.

**El parámetro físico que introduce:** una distancia δ (en milímetros) — lo llamo
"desviación permitida". Representa cuánto se tolera que la trayectoria REAL de la máquina
se aparte del vértice matemático ideal al tomar la esquina "cortándola" en vez de frenar en
seco. Es como decir: "aceptamos que la punta del cabezal pase a tantos milímetros del
vértice exacto con tal de no frenar del todo".

**Cómo decide la velocidad según el ángulo:** a partir de δ y del ángulo real de la esquina,
se calcula un radio de curva "equivalente" — cuanto más abierto el ángulo (casi seguir
derecho), más grande ese radio (curva suave); cuanto más cerrado, más chico (casi una vuelta
en U). Y la velocidad máxima de esa esquina es la que no exceda la aceleración lateral que
la máquina banca en una curva de ese radio — la misma física de "no derrapar en la curva".

**Verifiqué esto yo mismo antes de traerlo** (no lo cito de memoria a ciegas): construí la
geometría y confirmé el comportamiento con números concretos, para δ=0.5mm fijo:

| Ángulo de giro | Radio de curva equivalente | Velocidad de esquina* |
|---|---:|---:|
| 0° (sigue derecho) | infinito | sin límite (no frena) |
| 10° | 130.9 mm | 626.6 mm/s |
| 30° | 14.2 mm | 206.2 mm/s |
| 60° | 3.2 mm | 98.5 mm/s |
| 90° (esquina de cuadrado) | 1.2 mm | 60.2 mm/s |
| 120° (esquina de hexágono) | 0.5 mm | 38.7 mm/s |
| 179.9° (casi revertir) | ~0 mm | ~1 mm/s |

*con aceleración de ejemplo 3000 mm/s² — solo para mostrar la forma de la curva, no es el
valor real de la máquina (eso se calibra).

Se ve clarito: el ángulo de 90° de un cuadrado frena bastante (60 mm/s), el de 120° de un
hexágono frena más (39 mm/s), y una curva suave casi no frena nada. Esto es exactamente el
comportamiento que describiste — y es la razón por la que mi correlación de -0.79 con
densidad aparecía: los patrones densos tienen MÁS esquinas por mm recorrido, y mi modelo
anterior las trataba todas igual (binario), en vez de según su ángulo real.

**Por qué lo usan GRBL/Marlin:** porque con **un solo parámetro** (δ) capturan el
comportamiento correcto para CUALQUIER ángulo, sin tener que calcular curvas de continuidad
complejas. Es simple de calcular, físicamente razonable, y es el estándar de facto en
control de movimiento de bajo costo — exactamente el tipo de solución que esperaría que
CypCut use también (aunque no tengo confirmación de que sea EXACTAMENTE esta fórmula — ver
riesgos).

---

## 2) Riesgos y supuestos honestos

1. **Splines→arcos** (ya lo marqué): asumo que el toolpath real solo tiene segmentos y
   arcos. Confirmado por el validador del motor, pero no por CypCut directamente.

2. **Orden de recorrido** (esto ya me mordió antes): para una figura orgánica de una sola
   silueta cerrada (un Corazón), el orden dentro de ESA figura es poco ambiguo (es un
   contorno continuo). Pero entre agujeros/figuras distintas (los saltos de "rápido"), sigue
   habiendo la misma incertidumbre de siempre sobre qué orden usa CypCut. No lo resolví.

3. **NUEVO — identificabilidad de δ con Batería 2 (esto es importante, lo encontré ahora):**
   Batería 2 son todos CUADRADOS — o sea, **todas las esquinas tienen el mismo ángulo (90°)**.
   Con un solo ángulo en los datos, no hay forma de separar bien "cuánto pesa δ" de "cuánto
   pesa a_max" — varias combinaciones de los dos podrían explicar igual de bien un único
   ángulo. **Esto significa que la calibración de δ necesita ángulos VARIADOS desde el
   principio** — no puedo calibrar solo con Batería 2 y validar después con las figuras
   orgánicas como pensé originalmente. Voy a necesitar AL MENOS una figura orgánica (con
   ángulos variados) ya en la etapa de calibración, y reservar otra para la validación
   ciega de verdad. Ajusto el plan más abajo por esto.

4. **Arcos sin datos para calibrar su propia física** (relacionado con el punto anterior):
   Batería 2 no tiene curvas reales — solo esquinas de vértice. La parte de "velocidad
   límite por curvatura de un arco" (`v=√(a·radio)`) solo la puedo calibrar/validar con
   figuras que tengan arcos de verdad — las orgánicas.

5. **No sé si CypCut usa EXACTAMENTE Junction Deviation.** Podría usar otra fórmula de
   cornering, o un modelo de jerk lateral en vez de aceleración lateral. Mi plan es
   calibrar δ y a_max para que el comportamiento se ajuste a los datos reales — si la FORMA
   de la curva real es parecida, el ajuste debería funcionar razonablemente aunque la
   fórmula exacta de CypCut sea otra. Si la forma es muy distinta, puede no cerrar — lo
   voy a saber recién al calibrar, no antes.

6. **El "torch up/down"** que vos mencionaste (MSG_041) — no sé si el simulador de
   movimiento puro lo captura. Es un movimiento en el eje Z, no en el plano XY que estoy
   modelando. Podría quedar parcialmente escondido en el δ/a_max ajustados (como overhead),
   o podría hacer falta un término aparte. Lo voy a poder ver cuando compare predicho vs
   real por panel.

7. **Costo computacional:** las figuras orgánicas (splines convertidas) pueden tener
   decenas o cientos de tramos chicos — la simulación tramo por tramo puede ser mucho más
   pesada que lo anterior. Ya me pasó que un grid search en Python puro tardaba minutos;
   voy a necesitar vectorizar bien desde el principio, no como parche después.

---

## 3) Qué necesito de vos, y cuándo (para que lo vayas juntando sin que te bloquee)

| Etapa | Qué necesito | Bloquea la etapa? |
|---|---|---|
| 1-4 (parser, motor, esquina, simulador) | Nada nuevo — trabajo con los DXF que ya tengo | No |
| **5 (calibración) — CAMBIÓ por el punto 3 de arriba** | **El Processing/Move/Delay real de CypCut para al menos 1 figura orgánica** (Corazón o Gotas — son chicas; Cosmos es un archivo enorme, mejor arrancar por las otras dos) | **Sí, ahora sí** |
| 6 (validación cruzada) | Una SEGUNDA figura orgánica con su Processing/Move/Delay real, que NO se use en la calibración — para que la validación sea limpia de verdad | Sí |
| (opcional, ayuda pero no bloquea) | Si sabés algún dato de fábrica de la máquina (aceleración o jerk del corte vs del rápido) me ahorra parte de la búsqueda al calibrar | No |

Con Corazón + Gotas alcanzaría (uno para calibrar, uno para validar). Si podés conseguir
además Cosmos en algún momento, mejor — más variedad de ángulos = calibración más robusta.

---

## 4) Plan por etapas con puntos de decisión (para no meterme 6 etapas de corrido)

- **Punto de decisión 1** (después de armar el parser + motor cinemático básico): te muestro
  que el motor da tiempos razonables en casos simples y conocidos (un segmento solo, un
  arco solo) — confirmamos que la física básica anda antes de sumar la esquina.
- **Punto de decisión 2** (después de sumar Junction Deviation + integrar todo): corro el
  simulador completo sobre Batería 2 con parámetros de PRUEBA (no calibrados) — solo para
  confirmar que no tira errores ni números sin sentido, antes de invertir en la calibración
  fina.
- **Punto de decisión 3** (después de calibrar): te muestro los parámetros que salieron
  (δ, a_max, j) y el error por panel — para que vos, que conocés la máquina, me digas si
  esos números "suenan" razonables antes de seguir.
- **Punto de decisión 4** (validación cruzada): predicho vs real en la figura orgánica
  reservada. Esta es la decisión final: si cierra, seguimos a producción; si no, lo digo
  honesto y vemos cómo seguir.

---

## 5) Mi opinión honesta

**¿Es el camino correcto?** Sí. Es la única forma de que el MISMO modelo sirva para grillas
y para siluetas orgánicas sin coeficientes por tipo de patrón. Mis intentos anteriores
fallaron justamente por evitar esta complejidad con atajos.

**¿Hay un atajo razonable?** Creo que sí, y te lo propongo como punto de partida antes de
comprometernos al simulador completo:

**Atajo propuesto — probar Junction Deviation SOLO sobre mi modelo de jerk anterior**, sin
agregar todavía el régimen de aceleración+crucero (la parte más pesada de construir). Es
decir: reusar el código que ya tengo, y cambiar ÚNICAMENTE cómo se calcula la velocidad de
esquina — de "colineal sí/no" (binario) a "según el ángulo real" (Junction Deviation).
Esto es mucho menos trabajo (reuso casi todo lo que ya escribí y testeé) y ataca
directamente lo que mi propio diagnóstico anterior identificó como el defecto principal (el
binario, no la falta de un régimen de crucero — Batería 2 tiene tramos relativamente cortos,
donde el crucero pesa poco).

**Mi recomendación concreta:** probar este atajo PRIMERO (es rápido, uso los mismos datos
que ya tengo de Batería 2 más el ajuste del δ). Si baja el error sustancialmente, quizás no
haga falta el simulador completo de 6 etapas — nos ahorramos la parte más cara (el perfil
de 3 fases jerk→accel→crucero). Si el atajo mejora pero no alcanza, ahí sí construyo el
simulador completo, ya con evidencia de que el mecanismo de esquina por ángulo es el que
faltaba (y no otra cosa).

¿Les parece bien que arranque por ese atajo (con el visto bueno explícito para EJECUTARLO,
ya que esto era solo brainstorm)? Y en paralelo, si pueden ir consiguiendo el
Processing/Move/Delay de Corazón y Gotas, lo tengo listo para cuando el atajo (o el
simulador completo) esté armado.

— Punto
