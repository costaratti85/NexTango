# PUNTO_TASK_019 — Arcos invertidos al generar panel con patrón Philo

**De:** Nova  
**Para:** Punto  
**Fecha:** 2026-06-17  
**Prioridad:** Alta — sprint abierto, bug en producción

---

## Síntoma

Al generar un panel con el patrón Philo, cada arco se dibuja invertido: aparece el arco complementario (el "resto" del círculo) en lugar del arco correcto.

El archivo DXF del patrón fue verificado por Constantino — los arcos son correctos ahí. El error aparece en el paso siguiente: cuando el motor toma ese patrón y genera el panel (tiling/transformación).

## Dato diferencial importante

El bug aparece **solo con Philo**. El patrón Subte genera el panel correctamente.

Diferencias entre ambos que pueden ser relevantes:
- Subte: step 84×84, arcos posiblemente todos CCW
- Philo: step 360×623, arcos provenientes de una conversión de splines

Buscar qué hace distinto el motor cuando procesa Philo vs Subte — la causa probablemente está ahí.

## Hipótesis

Inversión de start_angle/end_angle, o problema con la dirección del arco (CCW vs CW) al hacer el tiling. Buscar en el código que transforma arcos al replicar el patrón:

- `process_border_figure()` en el motor legacy
- `arc_rebuilder.py` — función `add_arc()`, especialmente el cálculo de `orientation()` y el swap de `a1`/`a2`
- Cualquier paso que recalcule ángulos de inicio/fin de arcos durante el clip o el tile

## Criterio de aceptación

1. El panel generado con Philo muestra los arcos en la misma dirección que el DXF del patrón
2. Tests existentes siguen pasando
3. Reportar en `coordination/reports/PUNTO_TASK_019_REPORT.md`
