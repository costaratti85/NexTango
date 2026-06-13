# PUNTO_ARC_FIX_REPORT — Fix: arcos invertidos en thumbnail

**Agente:** Punto  
**Fecha:** 2026-06-13  
**Tarea origen:** PUNTO_TASK_005_FIX_ARC_DIRECTION.md

---

## Resumen

Se aplicó el fix de una línea en el renderer de thumbnails para corregir arcos DXF que se dibujaban en sentido horario (CW) en lugar de antihorario (CCW).

## Cambio aplicado

**Archivo:** `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`  
**Función:** `generate_pattern_thumbnail()` → `_draw(geom)`, líneas 189-190.

**Antes:**
```python
span = geom.end_angle - geom.start_angle
full_circle = abs(span) >= 359.9
```

**Después:**
```python
span = geom.end_angle - geom.start_angle
if span < 0:
    span += 360  # arcos DXF son siempre CCW
full_circle = abs(span) >= 359.9
```

## Diagnóstico confirmado

Cuando `end_angle < start_angle` (ej: start=300°, end=60°), el cálculo sin guardia producía `span = -240`. Esto hacía que matplotlib usara `radians(-240)` como barrido, dibujando el arco en sentido horario — invertido respecto al DXF real.

Con la guardia `if span < 0: span += 360`, el mismo caso produce `span = 120`, que es el barrido CCW correcto de 120°.

## Verificación de casos

| Caso | start | end | span antes | span después | Correcto |
|------|-------|-----|------------|--------------|----------|
| Arco normal | 0° | 90° | 90 | 90 | si |
| Arco wrap-around | 300° | 60° | -240 | 120 | si |
| Arco wrap-around | 270° | 90° | -180 | 180 | si |
| Circulo completo | 0° | 360° | 360 | 360 | si |

## Resultado de tests

```
32 passed, 9 warnings, 10 errors
```

Los 32 tests que compilan correctamente pasan. Los 10 errores son pre-existentes: falla de permisos de Windows sobre el directorio temporal de pytest (`C:\Users\vendo\AppData\Local\Temp\pytest-of-vendo`), sin relación con este cambio ni con el código de la aplicación.

## Estado

Fix aplicado y verificado. El CAD DXF generado no fue tocado — el fix es exclusivamente en el renderer de bitmaps del thumbnail.
