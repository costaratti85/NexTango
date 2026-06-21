# MSG_012_PUNTO_task026_done

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-18  
**Re:** TASK_026 completada — Endpoints de cierre corregidos

---

## Resumen

TASK_026 completada. Los vértices de la línea de cierre ahora coinciden exactamente con los nodos libres reales de la figura cortada. Gap = 0.

## Causa raíz

El `PolylineClipper` clipea **chords** (segmentos rectos entre puntos discretizados), no arcos. El punto de intersección chord-borde NO está sobre la circunferencia.

Cuando `ArcRebuilder` reconstructe el arco, mapea ese punto de vuelta a la circunferencia vía `atan2 + cos/sin`. El arco termina en un punto SOBRE el círculo, mientras que la línea de cierre (`PolylineCloser`) usaba el punto chord-boundary. **Diferencia: ~2.5 micrones** — suficiente para que el visor DXF los muestre como nodos desconectados.

## Fix

En `ArcRebuilder.rebuild_polyline()`: si el último segmento es "closing", se lo procesa al final usando los endpoints **reales** de las entidades reconstruidas:

```python
if has_closing and fig.entities:
    p_start = fig.entities[-1].end_point()
    p_end   = fig.entities[0].start_point()
    add_line(fig, p_start, p_end)
```

La línea de cierre ahora empieza/termina exactamente donde terminan/empiezan los arcos adyacentes.

## Verificación

```
Gap ANTES: ~2.5 micrones
Gap DESPUÉS: 0.0000 mm (exacto)
```

51 tests pasan. Reporte completo: `coordination/reports/PUNTO_TASK_026_REPORT.md`

---

**TASK_026 completada. Listo para próxima tarea.**
