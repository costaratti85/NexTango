# MSG_014_PUNTO_tasks027_028_done

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-18  
**Re:** TASK_027 y TASK_028 — completadas

---

## TASK_027 — Etiqueta DXF (regresión TASK_025)

**Causa raíz:** TASK_025 modificó el flujo genérico (`dxf_batch_compiler.py`) pero el flujo de producción usa `cad_result_layout.py` → `TextLabel.export_dxf()` — dos archivos distintos que no estaban tocados.

**Fix:**
- `geometry/text_label.py`: nuevo parámetro `right_align=False`; cuando `True` usa `TextEntityAlignment.RIGHT` de ezdxf
- `layout/cad_result_layout.py`: función `_abbreviate_material()` que lee `material_table.json`; `row_label` ahora usa formato corto + `right_align=True`
- Las `quantity_label` (`x{n}`) no cambian

**Reporte:** `coordination/reports/PUNTO_TASK_027_REPORT.md`

---

## TASK_028 — Líneas de cierre fuera del margen (patrón "philo")

**Diagnóstico directo de Constantino:** la línea de cierre conectaba el segundo y el último nodo en vez del primero y el último. Solo en patrones con arcos CW ("philo"), no en "subte" (solo líneas).

**Causa raíz:** `add_arc()` creaba `ArcSegment(cx, cy, r, a2, a1)` para arcos CW pero sin `_flipped=True`. El flag `_flipped` ya existía en `ArcSegment` exactamente para este caso (invierte `start_point()`/`end_point()` sin cambiar qué arco se dibuja en export). Faltaba setearlo.

**Fix:** una línea en `arc_rebuilder.py`:
```python
cw_arc = ArcSegment(cx, cy, r, a2, a1)
cw_arc._flipped = True
fig.add(cw_arc)
```

**Resultado:** línea de cierre en arco CW — gap = 0.0 mm, endpoints exactamente en el margen.

**Reporte:** `coordination/reports/PUNTO_TASK_028_REPORT.md`

---

## Estado

49 tests pasan. Listo para próximas tareas.
