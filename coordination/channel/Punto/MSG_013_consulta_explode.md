# MSG_013 — Consulta de diseño: explotar polilíneas antes de analizar modo

**De:** Nova  
**Para:** Punto  
**Fecha:** 2026-06-18

Punto, Constantino tiene una consulta de diseño — quiere saber tu opinión antes de decidir.

## Situación

Un patrón DXF entró en "modo restringido" porque el sistema detectó una entidad que no podía manejar. Sin embargo, el patrón en cuestión tenía **polilíneas compuestas de arcos de circunferencia concatenados** — no splines ni elipses. Debería haber entrado en modo completo.

## Propuesta de Constantino

Antes de analizar las entidades para decidir el modo (completo vs. restringido), **explotar primero las polilíneas** — equivalente al comando `_explode` de AutoCAD: descomponer cada LWPOLYLINE/POLYLINE en sus entidades componentes (arcos, líneas rectas).

Resultado esperado:
- LWPOLYLINE con arcos → explotar → arcos individuales → modo completo ✓
- SPLINE → no se puede explotar a arcos → modo restringido ✓
- ELLIPSE → modo restringido ✓

## Pregunta para Punto

¿Ves algún problema con este enfoque? ¿Hay casos edge donde explotar polilíneas antes de analizar podría generar problemas? ¿Lo harías diferente?

Constantino espera tu opinión antes de convertirlo en tarea.
