# CYBELEC_DELEM_DA53T_SECUENCIA_REPORT

**Agente:** Cybelec
**Tarea:** Análisis focalizado en SECUENCIA DE PLEGADOS del manual DELEM DA-53T (prioridad de Constantino)
**Fecha:** 2026-07-18
**Estado:** COMPLETO — investigación, sin implementación
**Antecede:** `CYBELEC_DELEM_DA53T_INVESTIGACION_REPORT.md` (análisis general)

---

## RESPUESTA CORTA

**El DA-53T no elige la secuencia de plegados. No tiene algoritmo de secuenciación, ni sugerencia, ni asistencia. El orden lo decide el operario, 100% a mano.**

Y no es una omisión: **estructuralmente no puede hacerlo**, porque el control nunca conoce la forma de la pieza (ver §2).

Barrí el manual completo (132 pág.) con búsquedas sistemáticas sobre `sequence / order / automatic / optimi / suggest / collision / feasible / reachable / geometry / contour / flat / strategy / rule`. **Cero heurísticas de ordenamiento documentadas.** El anexo A (índice de parámetros) tampoco tiene ningún parámetro de secuenciación.

---

## 1. Cómo determina el orden de los dobleces

**Lo determina el operario, con edición manual de una lista.** El juego completo de herramientas de orden es:

| Función | Qué hace |
|---|---|
| **Add Bend** | Agrega un pliegue después del último (copia el último) |
| **Insert Bend** | Inserta un pliegue antes del actual (copia el actual) |
| **Delete Bend** | Borra el pliegue seleccionado |
| **Mark Bend** | Marca un pliegue para moverlo o intercambiarlo |
| **Move Bend** | Mueve el pliegue marcado a otra posición de la lista |
| **Swap Bends** | Intercambia dos pliegues de lugar |

Cita del manual (sección 4.3.1): *"In the table overview of the bend sequence, it is possible to change the order of bends simply by moving a bend to another place."*

Es reordenamiento manual puro. El control **no evalúa, no puntúa, no propone ni advierte** sobre el orden elegido.

---

## 2. Por qué no puede secuenciar: no tiene modelo de la pieza

Ésta es la conclusión de fondo y la más importante para nuestro diseño.

El DA-53T es un control de **"programa numérico"**. Cita de la sección 1.5.1: *"the control offers the possibility to create a program **bend by bend** and adjust specific parameters for each bend independently."*

Lo que el control sabe de un trabajo es **una lista de pliegues con números**, cada uno con:
- Método (aire / a fondo / aplastado / aplastado a fondo)
- Ángulo (o posición Y absoluta, según el parámetro `Angle sel.`)
- Largo de plegado y largo efectivo de plegado (para fuerza y bombeo)
- Posición Z del producto
- Posición del eje X (tope) y ejes auxiliares
- Herramientas (punzón/matriz), corrección de ángulo, mute, paralelismo, apertura

Lo que el control **NO sabe en ningún momento**:
- La **geometría desplegada** de la pieza (no hay largo de chapa plana, ni contorno, ni lista de alas).
- **Qué ala conecta con qué ala** — no hay topología de la pieza.
- **Cómo queda la pieza después de cada pliegue** — no hay simulación de la forma parcial.
- Qué lado queda contra el operario, ni si hay que voltear o girar la pieza.

Sin la forma de la pieza no se puede evaluar si lo ya plegado choca contra el punzón, ni si el tope es alcanzable, ni cuántos volteos exige un orden. **Por eso el operario secuencia a mano: es el único que sabe cómo es la pieza.**

Nuestro motor parte del lado opuesto: nuestro dato de entrada ES la geometría (alas + ángulos con signo), y de ahí derivamos todo. Son dos filosofías distintas de control.

---

## 3. Datos de entrada que exige

Como prerrequisito (sección 1.5.2), antes de poder programar:
- **Librería de materiales**: nombre, resistencia a tracción, módulo E, exponente de endurecimiento `n`.
- **Librería de herramientas**: obligatoria para crear un programa CNC.
  - **Punzón**: altura (se usa en el cálculo de profundidad), ángulo de punta, **radio de punta**, ancho, resistencia máxima, tipo de montaje (head/shoulder mounted).
  - **Matriz**: ancho, altura, **radio de los cantos de la V**, ángulo de V, **apertura de V**, tipo de fondo de V (punta viva / redondo con radio / plano con ancho), resistencia, mute.
- **Geometría del dedo del tope**: hasta 4 niveles de apoyo, con altura del dedo (FH), largo del apoyo (FL) y altura del apoyo (H1), ancho del dedo, offset R.

Y por pieza: espesor y material. **Nunca la forma de la pieza.**

Nótese que las herramientas se definen por **parámetros**, no por perfil CAD. Nosotros dibujamos el perfil real (más potente para colisión, pero más frágil: un dibujo malo = secuencia mala).

---

## 4. Simulación de colisiones: qué hay y qué no

### ❌ NO tiene: colisión de la pieza plegada contra punzón/matriz
No existe en el manual. Es exactamente el corazón de nuestro motor (incluido el fin de carrera que acabamos de re-sincronizar) y el DA-53T no lo intenta.

### ✅ SÍ tiene (1): colisión pieza ↔ dedo del tope
Sección 8.4: *"With the backgauge finger dimensions the R-axis movement and related X-axes movement is taken into account. Also the **workpiece / backgauge collision is computed** using the dimensions."*

Es la única colisión pieza-máquina que calcula, y sale de la geometría multinivel del dedo. Equivale (más rico) a nuestra banda única `[-1.5, mesa + FINGER_H]` con `FINGER_H=30`.

### ✅ SÍ tiene (2): evitación de choque entre el tope y las herramientas al posicionar
No es colisión de la pieza, sino del **dedo del tope contra el punzón/matriz mientras se mueve**. Se resuelve con zonas de exclusión y una coreografía determinista de movimientos:

- **`X-safety offset`**: define la zona segura (valor mínimo de X) *"following the contour of punch and die"* — o sea un **keep-out en X derivado del contorno de las herramientas**.
- **Zona de seguridad de la matriz:** `SZ = X-safe + SD` (SD = distancia de seguridad definida por el fabricante de la máquina).
- **`Intermediate X for Z-movement`**: X seguro temporal para mover en Z. Con la lógica documentada:
  - X viejo y nuevo fuera de la zona → X y Z se mueven simultáneos.
  - Viejo fuera, nuevo dentro → primero Z, después X.
  - Viejo dentro, nuevo fuera → primero X, después Z.
  - Ambos dentro → va al X intermedio, luego Z, luego X final.
- **`Intermediate R for X-movement`**: si X debe entrar en la zona de seguridad de la matriz → **R sube a posición intermedia → se mueve X → R baja a su posición**.

### ✅ SÍ tiene (3): backgauge retract
*"The backgauge retract is started when the beam is pinching the sheet."* El tope se retira apenas la trancha pisa la chapa, así el ala puede subir sin pegarle al dedo.

---

## 5. Criterios para elegir la mejor secuencia

**Ninguno documentado.** El manual no menciona en absoluto:
- Accesibilidad/alcanzabilidad del tope por pliegue
- Minimización de volteos o giros de la pieza
- Sostenibilidad por el operario (largo mínimo del lado del operario)
- Estabilidad del apoyo (plano vs inclinado)
- Reutilización del mismo nodo de apoyo entre pliegues consecutivos

Todos esos criterios **sí** los tenemos nosotros, y **no vienen del DELEM: vienen del Cybelec DNC 880**, cuyo manual ya minamos y cuyos criterios ya están implementados en nuestro motor:

1. L. MÍN. CONTRA OPERARIO
2. MÍNIMO DE VOLTEADO / PIVOTADO / BASCULADO
3. MANIPULACIÓN ÓPTIMA
4. N° MÁX PLEGADO CONTRA TOPE
5. No apoyar sobre segmento inclinado
6. APOYO (qué nodo descansa contra el tope)

**Conclusión metodológica: para el problema de la secuencia, el Cybelec DNC 880 sigue siendo nuestra mejor referencia documentada, muy por encima de este manual del DELEM.**

---

## 6. Único caso donde el DA-53T sí "arma pasos" solo: cilindrado

La única generación automática de pasos es el **bumping** (cilindrado): dado un radio y un número de segmentos, genera N+1 plegados. Por defecto hace el **primer y último segmento a la mitad** del tamaño de los del medio (mejor resultado), con opción de forzarlos iguales si la V no permite segmentos tan chicos. Si detecta conflicto entre el tamaño de segmento y la apertura de V, **le pregunta al usuario** si recalcula con segmentos iguales.

Es lo más cerca de "decisión asistida" que llega el control, y es un caso 1-D muy acotado (no es secuenciación de una pieza).

---

## 7. Qué nos llevamos igual (aunque no secuencie)

1. **`X-safety offset` — keep-out en X derivado del contorno de las herramientas.** Es una regla barata y robusta: un X mínimo por debajo del cual el tope no puede acercarse. Nos puede servir como **pre-filtro rápido** antes de correr la simulación de colisión completa (que es lo caro en nuestro motor). Hoy tenemos `X_MIN=5` fijo; derivarlo del perfil de la herramienta sería más correcto.
2. **Backgauge retract.** Hoy chequeamos el dedo estático durante todo el golpe. Si en la ADIRA el tope se retira al pisar, algunos choques que hoy marcamos podrían no ser reales → menos falsos positivos.
3. **Dedo del tope multinivel (FH/FL/H1, hasta 4 apoyos)** en vez de nuestra banda única.
4. **Confirmación de arquitectura:** un control real de esta gama exige librería de herramientas y de materiales como prerrequisito, y define herramientas por parámetros. Valida nuestro modelo de útiles.

---

## 8. Aclaración honesta de alcance

Los controles Delem que **sí** hacen programación gráfica y cálculo automático de secuencia son los modelos superiores de la línea (gama gráfica 2D/3D) y su software offline. **Este manual no los describe**, así que no puedo aportar sus reglas desde esta fuente. Si a Constantino le interesa esa referencia, habría que conseguir el manual del modelo gráfico correspondiente — pero aviso de entrada que probablemente tampoco publique el algoritmo (el Cybelec tampoco lo publicó: documentó los *criterios*, y el algoritmo estaba compilado en `Dnc.dll`).

---

## Conclusión para el módulo de plegado

**El DA-53T no nos da nada para copiar en secuenciación, porque no secuencia.** La conclusión útil es doble:

- **Confirmatoria:** el problema que estamos resolviendo (elegir el orden óptimo automáticamente, con colisión contra herramientas) es de una gama superior a este control. Nuestro motor ya está por delante del DA-53T en esto.
- **De diseño:** la razón por la que el DA-53T no puede secuenciar es que **no modela la pieza**. Refuerza que nuestra decisión de partir de la geometría (alas + ángulos con signo) es la correcta y es el habilitador de todo lo demás.

**Nada de esto fue implementado.** Es investigación.

— Cybelec
