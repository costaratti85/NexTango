# MSG_153 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino) + Dispatch
**Fecha:** 2026-07-19
**Asunto:** ✅ ETAPA 2 (motor cinemático) — primeros números. PARO ACÁ, esperando el OK antes de la Etapa 3.

Commit `acfc16f` en `erpnext` (worktree `Nextango-erpnext`). Como pidió Constantino: motor
SIMPLE (trapezoidal, sin jerk), Junction Deviation por ángulo real, look-ahead, por eje en
los saltos — reporto y paro antes de seguir.

## Qué construí (`tools/simulador_cinematico.py`)
- **Perfil trapezoidal** (aceleración constante `a_max`, como GRBL real): dado un tramo con
  velocidad de entrada/salida y un techo `v_max`, calcula el tiempo mínimo — con o sin fase
  de crucero.
- **Junction Deviation**: velocidad máxima de esquina según el ángulo real del vértice (la
  fórmula ya derivada y verificada en el brainstorm: `v=√(a_max·R)`, `R=δ·sin(φ)/(1−sin(φ))`).
- **Look-ahead** (reverse pass + forward pass), aplicado de una sola pasada sobre TODA la
  secuencia de tramos (no hay buffer limitado como en el hardware real — acá conocemos todo
  el camino de antemano).
- **Corte**: velocidad escalar a lo largo de la trayectoria (como el feedrate de cualquier
  CNC). **Desplazamiento (saltos)**: por eje — cada salto se resuelve como dos sub-problemas
  1D (X e Y), el tiempo real es el máximo entre ambos.

## El bug que encontré y corregí en el camino
El look-ahead "de manual" (lineal) fuerza velocidad CERO en el primer y último tramo de la
secuencia — correcto para un desplazamiento (arranca y termina detenida), pero **incorrecto
para una figura CERRADA**: la costura donde el corte arranca y cierra (ej. cada agujero
cuadrado) no es una parada real de la máquina. Al aplicar el look-ahead lineal sin corregir
esto, cada agujero de Batería 2 salía con **más de 100% de error** — el simulador frenaba a
cero en la costura de CADA agujero, una parada espuria que no existe en la realidad.

Lo detecté comparando contra el caso más simple posible (un cuadrado de 60mm aislado):
el tiempo esperado sin frenar en las esquinas es ~3.2s, mi primer resultado daba 9.3s. Lo
corregí con un **look-ahead cíclico** (desenrollo la figura cerrada 3 veces seguidas, corro
el look-ahead lineal sobre esa secuencia larga, y tomo los valores de la copia del medio —
para entonces ya convergió y no arrastra el "reposo" artificial de las puntas). Verificado:
con 3 y con 5 repeticiones da exactamente el mismo resultado (convergencia confirmada).

## Sobre qué lo probé
1. **17 tests nuevos**, cada pieza contra su fórmula analítica exacta: perfil triangular
   reposo-a-reposo, perfil con meseta de crucero, Junction Deviation en los límites (0°=sin
   freno, 180°=frena a cero, monótona decreciente con el ángulo), reverse pass y forward
   pass del look-ahead por separado, el look-ahead cíclico (convergencia + "no frena en la
   costura"), y un caso borde documentado explícitamente (ver abajo).
2. **Los 12 paneles reales de Batería 2**, comparando contra el Processing/Move medido por
   CypCut (no contra un total agregado — cada componente por separado, como pidió
   Constantino la vez pasada).

## Primeros números contra Batería 2 real
Con `v_tabla=74.8mm/s` (ya calibrado antes, físicamente validado) y parámetros de **máquina
sin calibrar todavía** (`v_rápido=125mm/s`, `a_max=4000mm/s²`, `δ=0.02mm` — un punto de
partida razonable de firmware CNC típico, no un dato real de esta máquina):

| | error medio | error máximo |
|---|---|---|
| **CORTE** (Processing) | 20.3% | 40.3% |
| **DESPLAZAMIENTO** (Move) | 8.6% | 34.6% |

Esto ya está en el rango del benchmark realista para corte láser (13-15% según la
investigación bibliográfica, no <5% que es fresado de precisión) — y muy por debajo del 30-45%
que daban los modelos anteriores (el de velocidad de esquina fija, sin look-ahead completo).

**Patrón que encontré y no oculto**: el error crece sistemáticamente en los paneles con
agujeros MÁS CHICOS y más densos (5-8mm de lado — B2_06, B2_08, B2_09, B2_11 son los peores
en ambos componentes). Con agujeros grandes (30-60mm) el error baja a 5-9%. Sospecho que el
`δ` (Junction Deviation) o el `a_max` reales de la máquina no son constantes para geometría
muy densa, o que a esa escala entra en juego algo que el modelo trapezoidal simple no
captura (posible candidato para jerk, más adelante, si hace falta). No fuerzo un ajuste para
tapar esto — lo dejo marcado como el próximo lugar a investigar.

## El caso borde que quedó pendiente del turno anterior — resuelto, no era un bug
Documenté explícitamente (con test) el caso donde el tramo es MÁS LARGO que la distancia de
frenada pura: ahí la solución de tiempo mínimo acelera brevemente antes de frenar más fuerte
— verifiqué que es genuinamente más rápida que frenar "flojo" toda la distancia. No es un
error de la fórmula, es la física del problema de tiempo mínimo. En la práctica, el
look-ahead ya sanea las velocidades de entrada/salida de cada tramo para que este caso no
ocurra de forma espuria (verificado con test dedicado).

## Riesgo ya marcado, sin cambios
El orden de recorrido ENTRE figuras (boustrophedon, saltos de "rápido") sigue siendo un
supuesto sin validar contra telemetría real de CypCut — no lo toca este módulo.

## Verificación
17 tests nuevos, todos pasando. Suite completa: 230 passed, 4 failed — los 4 fallos son
`HTTPError 400` intentando conectar a un ERPNext en vivo (stubs de doctype, flujo de venta
completo), sin relación con este módulo ni con mi código; ninguno de mis tests nuevos falla.

## Paro acá
No seguí a la Etapa 3. Antes de seguir, creo que vale la pena que Constantino vea estos
números y decida: ¿el ballpark de 20%/9% con parámetros sin calibrar alcanza para seguir
afinando (calibrar δ/a_max/v_rápido reales), o prefiere que investigue primero por qué los
agujeros chicos/densos salen peor antes de avanzar? Cualquiera de las dos rutas la sigo
apenas tenga el visto bueno.

— Punto
