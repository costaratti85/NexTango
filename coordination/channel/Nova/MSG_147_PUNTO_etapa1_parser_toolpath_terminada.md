# MSG_147 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino) + Dispatch
**Fecha:** 2026-07-17
**Asunto:** ✅ ETAPA 1 (parser de toolpath) terminada — PARO ACÁ, esperando el visto bueno

Commit `f1ec381` (origin/erpnext). Como pidió Constantino: hago la Etapa 1, reporto, y espero
antes de seguir con la Etapa 2.

## Qué construí
Un parser que toma cualquier DXF (LINE, ARC, CIRCLE, LWPOLYLINE con bulge — las splines ya
vienen convertidas antes de llegar acá) y lo descompone en el recorrido real: una secuencia
de tramos (segmento recto o arco) con la longitud, los puntos, y la dirección tangente de
entrada/salida de cada uno. De ahí sale el ángulo real de cada vértice — el insumo que
necesita Junction Deviation (Etapa 3).

## Sobre qué lo probé
1. **Casos sintéticos verificados matemáticamente**: cuadrado (4 tramos, 90° exacto),
   triángulo equilátero (120°, confirmando explícitamente que es el ángulo EXTERIOR del
   polígono, no el interior de 60° — un lugar fácil de confundirse), polígonos regulares de
   5/6/8/12 lados (360°/n exacto en todos). Arcos: longitud, radio y tangentes verificados
   con un arco de 90° y un círculo completo. Conversión bulge→arco verificada con un
   semicírculo (bulge=1.0 → 180° de barrido, radio exacto). Tangencia línea-arco da ángulo
   de giro ≈0° exacto; una reversa completa da 180° exacto.
2. **Batería 2 real** (`B2_01_L60_p70_500x500.dxf`): detecta 37 figuras (36 agujeros +
   contorno), cada agujero da 4 tramos con 4 ángulos de 90° exactos.
3. **Corazón real** (`Corazon.dxf`, convertido de spline a líneas cortas vía flattening de
   ezdxf — no tenía tkinter para la herramienta de conversión con GUI, usé el mismo método
   que ya usa el código de producción para renderizar thumbnails, sin instalar nada): 10
   figuras cerradas (un patrón tileado de 10 corazones), **con ángulos de 0.2° a 94.8°**.
   Esto confirma el hallazgo del brainstorm anterior: Batería 2 (todo a 90°/120°) no alcanza
   para calibrar Junction Deviation sin ambigüedad — el Corazón sí trae la variedad de
   ángulos que hace falta.

## El riesgo que ya me mordió — documentado explícitamente, no asumido en silencio
- **Dentro de una figura cerrada** (un agujero, o el contorno del Corazón): el orden es casi
  objetivo — las entidades se encadenan por continuidad geométrica (el punto final de una
  coincide con el inicio de la siguiente), no hay mucha ambigüedad ahí.
- **Lo que SÍ es una elección mía, no verificable contra CypCut**: el punto exacto donde
  arranca/cierra el corte (dónde "prende y apaga" el láser) y el sentido de recorrido
  (horario/antihorario) — mi parser toma la primera entidad tal como aparece en el archivo
  DXF. No hay forma de confirmar esto sin telemetría real de la máquina.
- **Entre figuras distintas** (agujero a agujero, los saltos de "rápido"): esto NO lo resuelve
  este módulo — sigue siendo responsabilidad del orden boustrophedon que ya usaba antes
  (documentado como supuesto no verificado desde la vez pasada, sin cambios).

## Verificación
14 tests nuevos, todos pasando. Suite completa: 213 passed (los mismos 3 fallos
pre-existentes de entorno, sin relación, ya confirmados en turnos anteriores).

## Paro acá
No seguí a la Etapa 2 (motor cinemático trapezoidal). Espero que Constantino mire este
resultado y dé el visto bueno antes de seguir, tal como pidió.

— Punto
