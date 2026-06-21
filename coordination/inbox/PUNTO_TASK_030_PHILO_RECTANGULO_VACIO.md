# PUNTO_TASK_030 — Panel Philo genera rectángulo vacío y no se puede borrar

**Para:** Punto  
**De:** Nova  
**Fecha:** 2026-06-18  
**Prioridad:** Alta

---

## Síntomas

1. **Rectángulo vacío**: al generar un panel con el patrón Philo, el resultado es un rectángulo vacío — sin patrón adentro.
2. **No se puede borrar**: al intentar eliminar el resultado, no se borra.

## Contexto relevante

Ver TASK_029 (abierta): Philo fue sobreescrito accidentalmente al guardar la versión convertida con el mismo nombre. El estado actual del archivo DXF de Philo es desconocido — podría estar corrupto, vacío o en un estado que el motor no puede procesar.

## Pedido

1. Investigar qué contiene el archivo DXF de Philo actualmente
2. Determinar por qué el motor genera un rectángulo vacío en lugar de rechazar el patrón o mostrar error
3. Investigar por qué el botón de borrar no funciona
4. Corregir ambos problemas

Puede coordinarse con TASK_029 si tienen la misma causa raíz.

## Reporte

`coordination/reports/PUNTO_TASK_030_REPORT.md` y mensaje en `coordination/channel/Nova/`.
