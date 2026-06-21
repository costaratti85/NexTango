# PUNTO_TASK_034 — Justificación de textos en DXF

**Para:** Punto  
**De:** Nova  
**Fecha:** 2026-06-18  
**Prioridad:** Normal

---

## Síntoma

El texto en el DXF generado sigue apareciendo justificado a la izquierda.

## Solución propuesta por Constantino

1. **Todos los textos del DXF**: justificados a la derecha
2. **Etiquetas de cantidad** (`x2`, `x5`, etc.): además de justificación derecha, mover su posición **150mm hacia la derecha** para compensar y que no se monten sobre las figuras

## Pedido

Aplicar ambos cambios. Verificar en un DXF generado que los textos no se monten sobre la geometría.

## Reporte

`coordination/reports/PUNTO_TASK_034_REPORT.md` y mensaje en `coordination/channel/Nova/`.
