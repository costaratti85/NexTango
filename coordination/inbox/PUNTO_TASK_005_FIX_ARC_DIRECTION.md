# PUNTO_TASK_005 — Fix: arcos invertidos en thumbnail

**De:** Nova  
**Para:** Punto  
**Fecha:** 2026-06-13  
**Prioridad:** Alta — bug visible para el vendedor

---

## Problema

Los thumbnails muestran algunos arcos de circunferencia "para el otro lado" respecto al DXF real. El CAD generado es correcto — el bug es exclusivamente en el renderer de bitmaps.

## Diagnóstico

Archivo: `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`  
Función: `generate_pattern_thumbnail()` → función interna `_draw(geom)`, líneas ~189-197.

Los arcos en formato DXF siempre van en sentido **antihorario (CCW)** desde `start_angle` hasta `end_angle`. El renderer actual calcula:

```python
span = geom.end_angle - geom.start_angle
```

Cuando `end_angle < start_angle` (ej: start=300°, end=60°), el resultado es negativo (`span = -240`). Esto hace que `total = radians(-240)`, y matplotlib dibuja el arco en sentido horario — invertido.

## Fix exacto

Línea ~189, agregar una guardia después de calcular `span`:

```python
span = geom.end_angle - geom.start_angle
if span < 0:
    span += 360  # arcos DXF son siempre CCW
```

El código circundante no cambia. El `if span < 0` va entre la línea del `span =` y la del `full_circle =`.

## Criterio de aceptación

- El patrón de ejemplo de Constantino muestra los arcos en la misma dirección que el DXF generado
- 42 tests siguen pasando

## Reportar en

`coordination/reports/PUNTO_ARC_FIX_REPORT.md`
