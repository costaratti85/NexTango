# MSG_149 — Cybelec: la SECUENCIA de plegados en el DELEM DA-53T

**De:** Cybelec (Especialista en plegado CNC / motor Estun E21)
**Para:** Nova (para Constantino)
**Fecha:** 2026-07-18
**Asunto:** Qué hace el DA-53T para elegir el orden de los dobleces — respuesta focalizada
**Antecede:** MSG_148 (análisis general del manual)

---

Constantino, fui al manual con tu prioridad y lo barrí entero buscando específicamente el tema secuencia. Reporte técnico completo en `coordination/reports/CYBELEC_DELEM_DA53T_SECUENCIA_REPORT.md`. **No implementé nada.**

Te doy la respuesta derecho, aunque no sea la que esperabas.

## El DA-53T no elige la secuencia. La elige el operario, a mano.

No tiene algoritmo automático. No sugiere. No asiste. No avisa si el orden que elegiste va a chocar. Lo único que te da para ordenar los pliegues es una lista y seis botones para editarla a mano: agregar, insertar, borrar, marcar, mover e intercambiar pliegues.

Busqué sistemáticamente por todo el manual (132 páginas) por secuencia, orden, automático, colisión, optimización, alcanzabilidad, estrategia, regla. **Cero heurísticas de ordenamiento.** Revisé también el índice de parámetros del anexo: no existe ni un parámetro relacionado con secuenciación.

## Y hay una razón de fondo: el control no sabe cómo es la pieza

Esto es lo más importante que saqué, y creo que te va a servir para entender por qué nuestro enfoque es distinto.

El DA-53T trabaja con lo que llama un **"programa numérico"**: para el control, un trabajo es **una lista de pliegues con números sueltos** — ángulo, cota del tope, profundidad, herramientas, largo de plegado. Nada más.

El control **nunca sabe**:
- cómo es la pieza desplegada (no hay chapa plana, ni contorno, ni lista de alas),
- qué ala se conecta con qué ala,
- cómo queda la pieza después de cada pliegue,
- qué lado queda contra el operario, ni si hay que voltearla o girarla.

Sin la forma de la pieza **es imposible** evaluar si lo ya plegado va a chocar contra el punzón, si vas a llegar al tope, o cuántas veces vas a tener que dar vuelta la pieza. Por eso el orden lo tenés que poner vos: **sos el único que sabe cómo es la pieza.**

Nuestro motor arranca al revés: le damos la geometría (las alas con sus ángulos y signos) y de ahí sale todo lo demás. Es lo que nos habilita a secuenciar solos.

## Qué colisiones sí calcula (y cuáles no)

**NO calcula** el choque de la pieza plegada contra el punzón o la matriz. Nada. Es justo el corazón de nuestro cerebro — incluido el fin de carrera que acabamos de recuperar — y el DA-53T ni lo intenta.

**Sí calcula** tres cosas, todas alrededor del tope:

1. **Pieza contra el dedo del tope**, usando las medidas del dedo. Es la única colisión pieza-máquina que hace.
2. **El dedo contra las herramientas mientras se mueve.** Define una **zona prohibida en X "siguiendo el contorno del punzón y la matriz"**: el tope no puede acercarse más allá de ese X mínimo. Y si tiene que entrar ahí, sube el dedo primero, mueve X, y después baja el dedo. Lo mismo para moverse de costado (eje Z): pasa por un X intermedio seguro.
3. **El tope se retira solo** apenas la trancha pisa la chapa, así el ala sube sin pegarle al dedo.

## Criterios para elegir la mejor secuencia: ninguno

El manual no dice **nada** sobre alcanzar el tope, minimizar volteos, que te quede pieza para sostener, o apoyar en plano y no en inclinado.

Y acá va el dato importante: **todos esos criterios que ya tenemos implementados no salieron del DELEM — salieron del Cybelec DNC 880**, cuyo manual ya habíamos estudiado:

1. Largo mínimo contra el operario (que puedas sostener la pieza)
2. Mínimo de volteado / pivotado / basculado
3. Manipulación óptima
4. Máximo de plegados contra el mismo tope
5. No apoyar sobre segmento inclinado
6. Apoyo (qué nodo descansa contra el tope)

**Para el problema de la secuencia, el Cybelec sigue siendo nuestra mejor referencia — muy por encima de este DELEM.** El DA-53T es un control de gama más baja en ese aspecto.

## Lo único que arma pasos solo: el cilindrado

La única vez que el control genera pasos por su cuenta es en el cilindrado: le das radio y cantidad de segmentos y arma los plegados. Detalle bueno: por defecto hace **el primero y el último a media medida** porque sale mejor, y si el segmento le queda muy chico para la V que tenés puesta, **te pregunta** si recalcula con todos iguales. Es lo más cerca de "decisión asistida" que llega.

## Qué nos llevamos igual

Aunque no secuencie, hay tres cosas aprovechables:

1. **La zona prohibida en X sacada del contorno de la herramienta.** Hoy nosotros usamos un X mínimo fijo de 5 mm. Derivarlo del perfil real de la herramienta sería más correcto, y además nos serviría como **filtro rápido** antes de correr la simulación completa de choque (que es la parte lenta de nuestro cerebro).
2. **El tope que se retira al pisar la chapa.** Nosotros hoy chequeamos el dedo quieto durante todo el golpe. **Pregunta concreta: en la ADIRA, ¿el tope se retira solo cuando la trancha pisa?** Si sí, algunos choques que hoy marcamos con ⚠ pueden no ser reales, y te estamos descartando secuencias buenas.
3. **El dedo modelado con hasta 4 escalones** de apoyo (altura y largo de cada uno), en vez de nuestro escalón único de 30 mm.

## Aclaración honesta

Los controles Delem que **sí** hacen programación gráfica y secuencia automática son los modelos superiores de la línea, no éste. Este manual no los describe, así que no puedo traerte sus reglas desde esta fuente. Si querés esa referencia hay que conseguir el manual del modelo gráfico — pero te aviso de entrada: probablemente tampoco publique el algoritmo. El Cybelec tampoco lo publicó (documentó los *criterios*, y el algoritmo estaba compilado adentro del `Dnc.dll`, que ya intentamos y no se puede extraer).

## Conclusión

El DA-53T **no nos da nada para copiar en secuenciación, porque no secuencia**. Pero deja dos conclusiones útiles:

- **Estamos por delante.** Elegir el orden solo, con choque contra las herramientas y fin de carrera, es de una gama superior a este control.
- **Confirma nuestro diseño.** La razón por la que el DA-53T no puede secuenciar es que no modela la pieza. Que nosotros partamos de la geometría es exactamente lo que nos habilita a hacerlo.

Del resto del manual (factor K, tonelaje, materiales) ya te mandé el detalle en MSG_148 — el resumen es que no publica ni una fórmula, y lo más valioso de ahí era la base de datos de correcciones de ángulo.

Quedo con la pregunta del tope retráctil de la ADIRA, que es la que puede cambiar resultados reales del cerebro.

— Cybelec
