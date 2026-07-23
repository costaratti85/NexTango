# MSG_139 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino) + Dispatch
**Fecha:** 2026-07-17
**Asunto:** Simulador de movimiento — ENFOQUE propuesto, antes de meterme a fondo

Constantino tiene razón en el diagnóstico: mis intentos anteriores usaron atajos (largo
promedio de saltos, esquina binaria, orden de recorrido asumido) — no la física real. Acá
va el enfoque que propongo, con un plan por etapas, ANTES de escribir el simulador completo.

## Confirmé algo clave para el diseño
Miré la geometría real de los patrones orgánicos (`Corazon.dxf` en el server): el archivo
crudo tiene SPLINE + LINE. Pero el validador del motor (`dxf_validator.py`) **solo acepta
LINE/ARC/CIRCLE/LWPOLYLINE** — las splines se convierten a arcos ANTES de llegar al motor
(ya hay herramientas de conversión en el repo). **Supuesto que uso para el diseño:** el
toolpath que el simulador tiene que recorrer está compuesto solo de **segmentos rectos y
arcos circulares** — no necesito integrar curvas B-spline directamente. Si esto no fuera
así en algún caso, avisen, porque cambia bastante la Etapa 1.

## Arquitectura propuesta (6 etapas)

**Etapa 1 — Parser de toolpath genérico.** Recorre cualquier DXF (agujero, contorno, figura
orgánica) y lo descompone en una secuencia ordenada de TRAMOS reales: cada tramo es un
segmento recto (longitud, dirección) o un arco (longitud = radio×ángulo, radio, curvatura).
En cada unión entre tramos, calculo el ÁNGULO real del vértice. Esto es la pieza que hace
que la geometría entre por el recorrido, no por un escalar — sirve igual para una grilla de
agujeros que para un Corazón.

**Etapa 2 — Motor cinemático por tramo (perfil S-curve).** Dado un tramo con velocidad de
entrada v_in, de salida v_out, un techo de velocidad v_max (el menor entre la velocidad de
tabla del material y, si es un arco, la velocidad limitada por curvatura: v_max_arco =
√(a_max·radio)), y los parámetros de máquina (jerk j, aceleración a_max) — calculo el tiempo
del tramo con el perfil trapezoidal jerk-limitado estándar de control de movimiento (rampa
de aceleración limitada por jerk → crucero si el tramo es largo → rampa de deceleración).
Es la generalización correcta de mi `(32d/j)^(1/3)` anterior (que era el caso particular
v_in=v_out=0, sin techo de velocidad).

**Etapa 3 — Velocidad de esquina por ÁNGULO (lo que faltaba).** En cada vértice, la
velocidad de esquina depende del ángulo θ entre la dirección de entrada y salida — no
binario. Voy a usar la fórmula de **Junction Deviation** (el estándar de facto en
firmwares CNC/impresión 3D — GRBL, Marlin): con un parámetro δ (mm) y la aceleración
lateral máxima, la velocidad de esquina cae suave con ángulos abiertos y fuerte con ángulos
cerrados — exactamente el mecanismo que pediste. Es 1 parámetro nuevo (δ), estándar y
documentado, no algo que invento.

**Etapa 4 — Simulador completo.** Recorre TODO el toolpath tramo por tramo, propagando
velocidades de entrada/salida entre tramos consecutivos vía la velocidad de esquina, y suma
el tiempo total. Aplica igual a CORTE (Processing) y a DESPLAZAMIENTO (Move — por eje, cada
salto con su distancia real, dominando el eje más lento, como ya veníamos haciendo).

**Etapa 5 — Calibración contra Batería 2.** Ajusto (j, a_max, δ) — separados para corte y
desplazamiento, sin asumir que comparten valor — contra Processing/Move medidos por
separado, panel por panel. Es un ajuste de más dimensiones que los anteriores (3 en vez de
1-2), pero sigo el mismo método: grid search + refinamiento, auditable, reportando si algún
parámetro sale físicamente imposible.

**Etapa 6 — VALIDACIÓN CRUZADA con siluetas orgánicas (el test que importa).** Genero el
toolpath real de Corazón/Gotas/Cosmos con los parámetros de la Etapa 5 (calibrados SOLO con
grillas) y predigo su tiempo. Si coincide razonablemente con el tiempo real de CypCut para
esas figuras — que NO participaron de la calibración — el modelo es real, no un ajuste
sobre-fiteado a agujeros redondos.

## Lo que necesito para la Etapa 6 (no bloquea las etapas 1-5)
El **Processing/Move/Delay real de CypCut** para Corazón, Gotas y/o Cosmos (al menos una,
idealmente 2-3). Mismo formato que la Batería 2. Esto es el dato que voy a necesitar más
adelante — lo aviso ahora para que se pueda ir juntando en paralelo mientras yo avanzo con
las etapas 1-4.

## Decisiones que quiero confirmar antes de calibrar (Etapa 5)
1. **¿j y a_max son los mismos para corte y desplazamiento**, o se calibran por separado?
   Físicamente son límites de LA MÁQUINA (mismos motores), así que deberían compartirse —
   pero mis intentos anteriores mostraron que "asumir la misma física sin validar" salió
   mal una vez. Mi plan: calibrar por separado primero, y si salen parecidos, unificar.
2. **Arcos:** ¿hay valor en modelar `v_max_arco=√(a_max·radio)` desde ya, o lo dejo para
   después si Batería 2 (que son cuadrados/hexágonos, sin arcos reales salvo el propio
   hexágono con esquinas) no tiene curvas para calibrar esa parte? Sospecho que voy a
   necesitar las figuras orgánicas (que sí tienen arcos/curvas) para calibrar/validar esa
   pieza específica — no solo para el test final.

## Riesgo/esfuerzo, con honestidad
Esto es sustancialmente más grande que lo anterior — no es un ajuste de 1-2 parámetros, es
un simulador cinemático completo. Voy a avanzar por etapas y reportar cada una (no voy a
esperar hasta el final para mostrar progreso). Si en la Etapa 5 algún parámetro sale
físicamente imposible, lo digo ahí mismo, no sigo adelante forzando.

¿Avanzo con la Etapa 1 (parser de toolpath), o hay algo del enfoque que quieran ajustar
antes de que me meta a fondo?

— Punto
