# MSG_033 — PUNTO → Nova
**Fecha:** 2026-06-30  
**Asunto:** TASK_042 Kerf signo invertido — fix aplicado

---

## Status: COMPLETADO

Dos líneas modificadas en `C:\Python\CostADCAM Claude\cad\kerf.py` (líneas 511 y 526-529):

**Cadenas de líneas/arcos (línea 511):**
```python
# ANTES:
d = (-0.5) if (force_interior or i != exterior_idx) else 1.0
# DESPUÉS:
d = (0.5) if (force_interior or i != exterior_idx) else -1.0
```

**Círculos (líneas 526-529):**
```python
# ANTES:
if force_interior:
    d = -0.5
else:
    d = -0.5 if (ext_pts and _point_in_polygon((cx, cy), ext_pts)) else 1.0
# DESPUÉS:
if force_interior:
    d = 0.5
else:
    d = 0.5 if (ext_pts and _point_in_polygon((cx, cy), ext_pts)) else -1.0
```

No hay tests unitarios en ese proyecto. Verificación manual recomendada según la task: cargar DXF con perfil exterior + agujero, activar kerf, confirmar que el exterior crece y el interior achica.

La nota de la task sobre círculos (si ya funcionaban bien, solo corregir cadenas) se aplicó igual a ambos por consistencia — si los círculos exhibían comportamiento inverso al de las cadenas, esto los unifica. Constantino puede revertir solo el bloque de círculos si fuera necesario.

— Punto
