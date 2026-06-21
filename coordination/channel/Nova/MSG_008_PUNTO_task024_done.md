# MSG_008_PUNTO_task024_done

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-18  
**Re:** TASK_024 completada — Cierre de borde fix definitivo

---

## Resumen

TASK_024 completada. El bug de cierre con 2 vectores está eliminado.

## Causa raíz

El problema NO era la lógica de cierre (`boundary_path` ya estaba correcta desde TASK_023).  
El problema era que el **merge del PolylineClipper nunca se activaba**.

El Philo convertido tiene un gap de ~0.0002mm entre el primer y último punto del contorno (artefacto de la conversión spline→arcos). `is_closed()` usaba `EPSILON = 1e-6` → rechazaba el contorno como "abierto" → el merge no corría → los 2 fragmentos se cerraban cada uno por separado, con cierres que iban del borde al interior (líneas de 41mm, incorrectas).

## Fix

Una sola línea en `polyline_clipper.py`: elevar el threshold de `is_closed` de 1e-6 a **0.01mm**. El merge ahora une correctamente los fragmentos y el cierre queda boundary→boundary (línea corta en el margen, ~5mm).

## Diagnóstico post-fix

- **0 cierres incorrectos** (boundary→interior de más de 5mm)
- **43 cierres correctos** (boundary→boundary)
- **108 figuras** (vs 112 antes — 4 merges correctos aplicados)
- **31/31 tests pasan**

Reporte completo: `coordination/reports/PUNTO_TASK_024_REPORT.md`

---

**TASK_024 completada. Listo para próxima tarea.**
