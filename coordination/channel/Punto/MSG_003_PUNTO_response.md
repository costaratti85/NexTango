# MSG_003_PUNTO_response

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-17  
**Re:** TASK_019 completada — Arcos invertidos en Philo

---

## Diagnóstico

El bug estaba en **`ArcSegment.reversed()`** en el motor legacy.

Cuando el `EntityStitcher` encadena las entidades del DXF en figuras cerradas, a veces necesita unir una entidad "al revés" y llama a `.reversed()`. Para una línea esto es invisible (mismo segmento, otra dirección). Para un arco, el código intercambiaba `start_angle ↔ end_angle`, que en convención DXF CCW produce el **arco complementario** — los otros 360-θ grados del círculo.

Verifiqué con datos reales: de los 1.150 arcos del DXF de Philo, **494 (43%)** fueron revertidos por el EntityStitcher. Todos esos se exportaban como el arco complementario.

Un bug secundario en `add_arc()` del `ArcRebuilder`: cuando un arco tiene span < 5°, solo se discretizan 2 puntos. Si la polilínea se invertía, la detección de dirección (producto cruzado = 0) fallaba y asumía CCW incorrecto → arco de ~357° en lugar del correcto de ~3°.

---

## Solución

Dos cambios en el motor:

1. **`arc_segment.py`** — `ArcSegment.reversed()` ahora devuelve el mismo arco con un flag `_flipped`. El flag hace que `start_point()`/`end_point()` se intercambien (para que el stitcher conecte correctamente), pero `export_dxf()` sigue usando los ángulos originales sin cambios → el arco dibujado es correcto.

2. **`arc_rebuilder.py`** — `add_arc()` con 2 puntos ya no asume CCW por defecto. Compara los ángulos calculados contra `source_arc.start_angle` para inferir la dirección real.

---

## Resultado

- Tiles interiores: 0 arcos complementarios (antes: 494 de 1150)
- Tiles de borde: 0 arcos de gran span con radio significativo (antes: ~55)
- 31 tests pasan

Reporte completo: `coordination/reports/PUNTO_TASK_019_REPORT.md`

---

**Sin tareas pendientes. Esperando próximas instrucciones.**
