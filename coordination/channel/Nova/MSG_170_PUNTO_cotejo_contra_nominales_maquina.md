# MSG_170 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino) + Dispatch
**Fecha:** 2026-07-21
**Asunto:** Cotejo contra los nominales de máquina (75 / 1650 mm/s) — CORTE confirma casi
exacto, TRAVEL destapa una pregunta abierta que no fuerzo a cerrar

## CORTE — el nominal (75mm/s) valida el calibrado (74.0mm/s) casi exacto
Diferencia: **1.3%**. Y el patrón que marcás se ve clarísimo y ya lo tenía reproducido:

- `recta_250mm`: 250mm / 3.465s = 72.15mm/s efectivo — se acerca al nominal porque el tramo
  es largo, alcanza velocidad de crucero la mayor parte del recorrido.
- `radio_05mm`: 7.85mm / 0.236s = 33.26mm/s efectivo — muy por debajo del nominal, porque el
  tramo es tan corto (7.85mm) que nunca llega a acelerar a fondo antes de tener que frenar de
  nuevo (perfil triangular, sin meseta de crucero).

Esto es exactamente lo que predice el modelo con `a_max_cut=625mm/s²` — no hace falta tocar
nada de CORTE, el nominal lo confirma de forma independiente (no lo usé para calibrar, y cae
adentro del rango de error ya reportado en MSG_169).

## TRAVEL — a_max queda bien determinado, v_max NO (y no lo fuerzo)

**a_max_travel ≈ 380mm/s² queda sólido, con o sin el dato de 1650**: `travel_cerca` (60mm de
recorrido en X) y `tamano_grande` (120mm en Y) son tan CORTOS que el modelo nunca llega a
acercarse a ninguna velocidad de crucero — ni a los 199mm/s que había ajustado en MSG_169 ni,
mucho menos, a los 1650mm/s nominales. Fijando `v_max=1650` (el nominal real) y ajustando
SOLO `a_max`, esos dos casos siguen cerrando con **0.24% y 0.25% de error** — prácticamente
sin cambios respecto a MSG_169. Es un buen resultado: la aceleración de desplazamiento no
depende de esta duda.

**`travel_lejos` es el ÚNICO caso que realmente prueba la velocidad de crucero** — y ahí es
donde aparece la pregunta que no puedo cerrar con un solo dato:

- Con `v_max=1650` (nominal) fijo y `a_max=380`: el modelo predice que a los 600mm el
  desplazamiento YA estaría en régimen triangular puro (nunca llegaría ni cerca de 1650mm/s,
  necesitaría ~3535mm solo para alcanzarlo) → predicho 2.53s. **Real: 3.538s — un 40% más
  lento que lo que el nominal + esa aceleración predicen.**
- Con `v_max=199` (el que ajusté en MSG_169, sin conocer el nominal): predicho 3.535s — error
  0.1%.

**No tengo forma honesta de decidir, con UN solo dato de distancia larga, si**: (a) la
máquina tiene un techo de velocidad de desplazamiento PRÁCTICO muy por debajo del nominal
(1650mm/s es spec de catálogo, no necesariamente lo que usa CypCut en operación real — es
común en máquinas industriales tener un límite de "rápido" configurado más bajo que el
máximo mecánico, por seguridad/precisión), o (b) hay algo que mi modelo no captura a esta
escala de distancia (jerk, algún límite del controlador, etc.) que hace que el "efectivo"
en 600mm todavía no sea representativo del régimen de largo plazo. Con un solo punto no lo
puedo separar — sería forzar una historia sin evidencia, así que no lo hago.

## Lo que SÍ dejo como calibración de trabajo (no definitiva)
- `a_max_travel ≈ 380mm/s²` — sólido, confirmado independientemente del debate de arriba.
- `v_rápido ≈ 199mm/s` — sigue siendo mi mejor estimación PRÁCTICA (no la nominal de
  catálogo), pero depende de un solo dato de distancia larga. Lo marco explícitamente como
  la parte más débil de la calibración actual.

## Lo que pediría para cerrar esto de verdad
Un par de distancias más, más largas (ej. 1000mm y 2000mm, mismo criterio de secuencia
fijada que ya usamos) — con eso quedaría claro si el efectivo se estabiliza cerca de 199mm/s
(techo práctico real) o si sigue subiendo con la distancia (y en ese caso, hacia dónde: si
tiende a 1650, o a otro valor intermedio). Con un solo punto no me la juego a decir cuál es.

## No cierro nada
CORTE queda confirmado por partida doble (Batería 2 + este experimento + ahora el nominal).
TRAVEL: `a_max` sólido, `v_max` como pregunta abierta explícita — reporto la incertidumbre en
vez de elegir un número y presentarlo como si estuviera resuelto.

— Punto
