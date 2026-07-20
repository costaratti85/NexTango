# MSG_167 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino) + Dispatch
**Fecha:** 2026-07-20
**Asunto:** DISEÑO del experimento de validación v2 (NO ejecutado, esperando aprobación) —
corrijo los 2 problemas que Constantino encontró

No generé ningún archivo todavía. Esto es el diseño para que Constantino lo revise y apruebe
(o corrija) antes de que yo genere nada.

## Primero, los 2 errores — de acuerdo con ambos

**1) Segmentitos en vez de arcos reales**: tuve un lugar de aparentar cauteloso de más — evité
`dxf_spline_to_arcs.py` porque me faltaba `tkinter` en mi entorno, y usé el flattening de
ezdxf como atajo. Constantino tiene razón: eso mete miles de esquinas falsas (aunque en mi
modelo cada una es de ángulo casi 0° y en teoría no frena nada, es exactamente el tipo de caso
que "en teoría no importa" pero en la práctica contamina — no vale la pena arriesgarlo, y
además CypCut probablemente NO ve "una spline", ve esos microsegmentos como miles de tramos
reales, que es una geometría distinta a la que corta con una spline/arco nativo). Para este
experimento nuevo el problema no existe: propongo geometría 100% nativa (LINE/ARC de ezdxf),
sin ninguna curva que necesite aproximarse. Si más adelante volvemos a figuras orgánicas
(Corazón/Gotas/Cosmos), ahí sí uso `dxf_spline_to_arcs.py` como corresponde — anoto que me
falta `tkinter` en el venv para llamar su función core sin la GUI; lo resuelvo cuando llegue
ese momento (pido instalar `python3-tk` o extraigo la función sin la parte gráfica).

**2) Secuencia/entrada desconocida**: es el riesgo que vengo marcando desde la Etapa 1 sin
que tuviera consecuencias hasta ahora — en Batería 2 y en el intento con las orgánicas asumí
un orden boustrophedon sin poder confirmarlo. Constantino tiene razón en que eso invalida la
comparación. Ver el diseño abajo, pensado específicamente para eliminar esa ambigüedad en
vez de sólo "asumir mejor".

## Bloque 1 — CORTE puro (figuras abiertas AISLADAS, sin ambigüedad de entrada)

**Por qué figuras abiertas resuelven la entrada solas**: en una figura abierta y aislada (sin
nada más en la chapa), el tiempo de corte que predice el modelo es **matemáticamente
invariante** a por qué punta empieza o en qué sentido la recorre — arranca y termina en
reposo en cualquiera de los dos casos, y los mismos tramos/ángulos se cruzan en el mismo
orden de magnitud. No importa qué convención use CypCut internamente: el corte de UNA figura
abierta sola no tiene ninguna decisión de secuencia que tomar. Esto resuelve el problema 2 de
raíz para todo este bloque, no lo esconde.

- **1a) Barrido de RADIO** (arco simple, sin vértices — aísla `a_max_cut` directo por
  `v=√(a·r)`, sin pasar por Junction Deviation): 4 arcos abiertos, barrido angular fijo 90°,
  radios 5 / 15 / 40 / 100 mm (longitudes de arco resultantes: 7.9 / 23.6 / 62.8 / 157mm).
- **1b) Barrido de ÁNGULO** (polilínea abierta en "V", 2 tramos rectos de 50mm cada uno —
  aísla `δ_cut`, una vez fijado `a_max_cut` con 1a): 5 figuras, ángulo de giro del vértice
  15° / 45° / 90° / 135° / 165° (0°=recto, 180°=reversa — cubre casi todo el rango).
- **1c) Control recta pura** (sin vértices ni curvas — verifica `v_tabla` y el reposo-reposo
  más simple posible): 3 líneas, 20 / 80 / 250mm.

12 archivos, cada uno UNA figura sola en la chapa. `Total time` de CypCut = tiempo de esa
figura, sin nada que discutir sobre orden.

## Bloque 2 y 3 — TRAVEL y TAMAÑO (aquí SÍ hay entrada entre figuras — mitigado, no eliminado)

**Truco de diseño**: cada figura de prueba es un segmento **VERTICAL** (perpendicular a la
dirección del viaje), y las 4 figuras de cada archivo se disponen en **fila horizontal**,
todas a la misma altura Y, separadas en X. Así, la distancia de viaje DOMINANTE (en X) es la
misma sin importar por qué punta (arriba/abajo) entra o sale CypCut de cada segmento — solo
queda un residuo chico en Y (acotado por el alto del segmento, que mantengo fijo y chico:
10mm, en TODOS los casos, para no mezclarlo con el factor bajo prueba).

- **2a) "CERCA"**: 4 segmentos verticales de 10mm de alto, separación en X = 20mm entre el
  final de uno y el inicio del siguiente.
- **2b) "LEJOS"**: mismos 4 segmentos, separación en X = 200mm.
- **3b) "GRANDE"** (tamaño, separación fija = la de 2a): mismos 4 segmentos pero **de 40mm de
  alto** (4x más grandes en la dimensión que se corta — sigue siendo un segmento vertical
  simple, invariante a la entrada por el mismo motivo de Bloque 1), separación en X = 20mm.

(3a = 2a, se reusa — no hace falta un archivo nuevo.) Con 2a/2b aíslo el efecto de la
DISTANCIA de salto sobre TRAVEL (tamaño de figura constante); con 2a/3b aíslo el efecto del
TAMAÑO sobre CORTE (separación constante). 3 archivos nuevos.

**Todas las figuras dibujadas con la misma convención**: cada segmento vertical trazado de
abajo hacia arriba en el DXF, y las 4 figuras en orden de X creciente en el archivo — mi
predicción asume ese orden, con viaje total = suma de los 3 huecos entre consecutivas (da
igual si CypCut lo recorre de izquierda a derecha o al revés, la distancia total es la misma
por ser colineal).

## La pregunta que más importa — cómo confirmamos que CypCut siguió esa convención

Esto es lo que de verdad decide si el experimento es válido, más que cualquier truco
geométrico. Necesito que Constantino (que tiene CypCut delante) me confirme:

1. **¿CypCut permite exportar o ver el programa/NC real que ejecutó** (la secuencia de
   movimientos, en el orden real, con los puntos de entrada/salida reales de cada figura)?
   Si SÍ: es la solución de fondo — leo esa secuencia real y se la doy al simulador tal cual,
   sin asumir nada. Esto resuelve el problema para SIEMPRE, no solo para este experimento.
2. Si no se puede exportar el NC: **¿la simulación/preview de CypCut muestra una animación
   del recorrido** que Constantino pueda ver y anotar a mano (aunque sea "entró por la
   izquierda, cortó las 4 de izquierda a derecha")? Es más manual, pero sigue siendo dato
   real en vez de un supuesto.
3. Si ninguna de las dos es posible: me quedo con el diseño geométrico de arriba (invariante
   a la entrada en Bloque 1, mitigado con el truco vertical en Bloque 2/3) — es más débil que
   1 o 2, lo digo directamente, pero sigue siendo mejor que lo que hice la vez pasada.

## Un supuesto adicional que este experimento también pone a prueba (lo marco, no lo escondo)
Todo mi modelo asume que la máquina llega a **reposo completo** en el borde de cada figura
abierta antes de pasar a viaje rápido (corte y viaje no se "mezclan" en velocidad). Si CypCut
en realidad combina la salida del corte con la entrada al viaje sin frenar del todo, mi
predicción va a sobreestimar sistemáticamente — y este experimento (al ser tan simple) lo
va a mostrar con claridad si pasa, cosa que con Batería 2 (todo mezclado) no se podía ver.

## Total propuesto: 15 archivos DXF (12 de Bloque 1 + 3 de Bloque 2/3)
Cada uno con su propio "Total time" a anotar en CypCut, mismo formato que Batería 2.

## Espero la aprobación de Constantino antes de generar nada
Puntos concretos donde pido su corrección o OK: (a) el diseño en general, (b) los tamaños/
ángulos/radios elegidos (si prefiere otros), (c) sobre todo, la respuesta a la pregunta de
arriba sobre qué visibilidad da CypCut de la secuencia real — de eso depende si el
experimento queda sólido o solo "mitigado".

— Punto
