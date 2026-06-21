# PUNTO_TASK_028 — Líneas de cierre fuera del margen

**Para:** Punto  
**De:** Nova  
**Fecha:** 2026-06-18  
**Prioridad:** Alta

---

## Premisa geométrica (no negociable)

El margen es un subespacio de dimensión 1 (un conjunto de segmentos de línea recta). Toda línea de cierre que se dibuja para cerrar una figura cortada por el margen **debe pertenecer a ese subespacio**. Si no pertenece → es un error.

Dicho de otra manera: cualquier línea generada para cerrar una figura abierta tiene que estar montada exactamente sobre el margen. No puede ir por otro lado.

## Síntoma

Constantino verifica que en el DXF generado hay líneas de cierre que **no están sobre el margen**. Líneas que deberían ir de un nodo del margen a otro nodo del margen, pero en cambio van por otro camino que no coincide con la línea del margen.

## Pedido

1. Identificar qué código produce líneas de cierre que no pertenecen al margen
2. Asegurarse de que TODA línea de cierre satisfaga la premisa: sus dos endpoints están sobre el margen y el segmento entre ellos también está sobre el margen
3. Si una línea de cierre requiere pasar por un vértice del margen (caso esquina), los dos segmentos resultantes también deben estar sobre el margen
4. Corregirlo

## Reporte

`coordination/reports/PUNTO_TASK_028_REPORT.md` y mensaje en `coordination/channel/Nova/`.
