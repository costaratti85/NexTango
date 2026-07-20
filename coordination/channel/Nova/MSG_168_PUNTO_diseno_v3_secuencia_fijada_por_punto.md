# MSG_168 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino) + Dispatch
**Fecha:** 2026-07-20
**Asunto:** Diseño v3 — incorporo el método de Constantino (secuencia fijada por nosotros,
reproducida en CypCut). Confirmando ANTES de generar nada.

## De acuerdo con la corrección
Tenía razón: "cortar A→B = B→A" solo vale para el tiempo de CORTE de una figura abierta
aislada — el TRAVEL entre figuras sí depende de qué punto es la salida de una y la entrada de
la siguiente. No lo estaba confundiendo en el diseño anterior (Bloque 2/3 ya reconocía que ahí
"sí hay entrada... mitigado, no eliminado"), pero el método nuevo es mucho mejor que cualquier
mitigación geométrica.

## El método (de Constantino) — se da vuelta el problema
En vez de adivinar qué orden/entrada usa CypCut, **nosotros lo definimos y Constantino lo
reproduce**: yo fijo la secuencia (orden de figuras) y el punto de entrada/salida de cada una,
se lo doy en una hoja de instrucciones clara, y él corta exactamente eso en CypCut. Ambos
lados cortan el mismo recorrido → la comparación queda 100% válida, sin supuestos de por
medio. Esto resuelve el problema de raíz para siempre, no solo para este experimento.

**Pregunta pendiente para Constantino**: ¿CypCut te deja fijar el punto/dirección exacta de
arranque de cada figura (ej. elegir el nodo de inicio), o solo el ORDEN en que procesa las
figuras (con el punto de entrada decidido por CypCut solo)? Si es lo primero, seguimos la
hoja de instrucciones al pie de la letra. Si es solo el orden, seguimos usando geometría
simple y simétrica (ver Bloque 2/3 abajo) para que el punto de entrada real que elija CypCut
no cambie mucho el resultado — lo aviso en la hoja igual, por si ayuda.

## Bloque 1 — CORTE puro (sin cambios de fondo, ya era robusto)
12 figuras abiertas y aisladas (4 radios / 5 ángulos / 3 rectas control, arcos y líneas
NATIVOS — nada de segmentos aproximados). Como el corte de una figura aislada no depende de
la entrada, acá no hace falta fijar nada — Constantino corta cada una como quiera. **A
anotar: `Processing time`** (no el total) — así queda aislado del travel de aproximación al
primer punto, que no modelamos en este bloque.

## Bloque 2/3 — TRAVEL y TAMAÑO (acá SÍ fijamos secuencia + entrada/salida)
Mantengo el mismo truco geométrico de la vez pasada (segmentos VERTICALES en fila horizontal)
— ya no es matemáticamente indispensable (ahora controlamos la secuencia real), pero lo dejo
porque es fácil de reproducir a mano sin ambigüedad ("de abajo hacia arriba", números
redondos) y da un margen de seguridad si la reproducción no es pixel-perfecta.

Ejemplo de la hoja de instrucciones que acompaña a CADA archivo de este bloque (formato
propuesto — pido el OK de esto en particular):

> **Archivo: `travel_cerca.dxf`**
> 4 segmentos verticales de 10mm de alto, separados 20mm en X.
> Coordenadas: Figura 1 en x=0 (de y=−5 a y=+5), Figura 2 en x=20, Figura 3 en x=40, Figura 4
> en x=60 (mismo rango Y en las 4).
>
> **Secuencia a reproducir en CypCut:**
> 1. Figura 1 — entrar por ABAJO (x=0, y=−5), salir por ARRIBA (x=0, y=+5)
> 2. Figura 2 — entrar por ABAJO (x=20, y=−5), salir por ARRIBA (x=20, y=+5)
> 3. Figura 3 — entrar por ABAJO (x=40, y=−5), salir por ARRIBA (x=40, y=+5)
> 4. Figura 4 — entrar por ABAJO (x=60, y=−5), salir por ARRIBA (x=60, y=+5)
>
> **Anotar de CypCut**: `Processing time`, `Move time` y `Delay time` por separado (el
> desglose completo, como en Batería 2) — no solo el total.

Los otros 2 archivos de este bloque (`travel_lejos.dxf`: mismos 4 segmentos, separación
200mm; `tamano_grande.dxf`: segmentos de 40mm de alto, separación 20mm) siguen exactamente el
mismo formato de hoja.

## Entregable final (una vez que Constantino apruebe esto)
Por cada uno de los 15 archivos: el DXF (arcos/líneas nativos) + su hoja de instrucciones
(secuencia + entrada/salida si aplica + qué anotar). Igual que con Batería 2, pido el
desglose Processing/Move/Delay siempre que se pueda, no solo el total.

## Sigo sin generar nada
Espero el OK de Constantino sobre: (a) el método en general, (b) el formato de la hoja de
instrucciones (el ejemplo de arriba), y (c) la respuesta sobre si CypCut permite fijar el
punto exacto de entrada o solo el orden.

— Punto
