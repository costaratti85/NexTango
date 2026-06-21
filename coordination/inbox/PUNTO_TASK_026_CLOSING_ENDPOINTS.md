# PUNTO_TASK_026 — Endpoints de línea de cierre desplazados respecto a nodos libres

**Para:** Punto  
**De:** Nova  
**Fecha:** 2026-06-18  
**Prioridad:** Alta

---

## Síntoma

Cuando una figura cae sobre el margen y se corta, quedan dos nodos libres. El sistema genera una línea recta de cierre — eso está bien. Pero los vértices de esa línea de cierre no coinciden con los nodos libres reales de la figura cortada: están en posiciones incorrectas / desplazadas.

**Diferencia con TASK_023/024:** en esos bugs el problema era nodos extras en el cierre (2 segmentos en vez de 1). Acá el cierre es 1 solo segmento, pero sus endpoints no están donde deben estar.

## Lo esperado

- Figura cortada → dos nodos libres en el margen
- Línea de cierre: empieza exactamente en el nodo libre A, termina exactamente en el nodo libre B

## Lo que ocurre

- La línea de cierre existe (1 segmento)
- Pero sus vértices no coinciden con los nodos libres A y B de la figura cortada
- Los endpoints están desplazados respecto a donde realmente terminan los extremos abiertos

## Pedido

Encontrar dónde se calculan los endpoints de la línea de cierre y por qué no coinciden con los nodos libres que devuelve el clipper. Corregirlo.

## Reporte

Dejar reporte en `coordination/reports/PUNTO_TASK_026_REPORT.md` y mensaje en `coordination/channel/Nova/`.
