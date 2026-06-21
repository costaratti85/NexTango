# PUNTO_TASK_035 — Posicionamiento del origen del patrón en el primer tile

**Para:** Punto  
**De:** Nova  
**Fecha:** 2026-06-19  
**Prioridad:** Alta

---

## Regla geométrica (definida por Constantino)

El punto (0, 0) del archivo `.dxf` del patrón debe coincidir exactamente con la **esquina inferior izquierda del área efectiva** — es decir, el punto donde se cruzan el margen inferior y el margen izquierdo.

## Comportamiento esperado

- El primer tile se posiciona colocando su origen (0, 0) en esa esquina
- Si el DXF del patrón tiene figuras en posiciones X negativas, es intencional: esas figuras deben quedar cortadas por el margen izquierdo (igual que cualquier figura que cae sobre el margen)
- El sistema no debe corregir ni desplazar esas posiciones negativas — son parte del diseño del patrón

## Comportamiento actual (bug)

El primer tile no se está posicionando con su (0, 0) en la esquina inferior izquierda del área efectiva. Hay un desplazamiento incorrecto.

## Pedido

1. Encontrar dónde se calcula la posición del primer tile
2. Corregir para que el origen del patrón coincida con la esquina inferior izquierda del área efectiva (intersección margen izquierdo × margen inferior)
3. Verificar que figuras con X negativo en el patrón queden correctamente clipeadas por el margen izquierdo

## Reporte

`coordination/reports/PUNTO_TASK_035_REPORT.md` y mensaje en `coordination/channel/Nova/`.
