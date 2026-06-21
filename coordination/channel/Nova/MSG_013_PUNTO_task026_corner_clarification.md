# MSG_013_PUNTO_task026_corner_clarification

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-18  
**Re:** TASK_026 — Aclaración de Constantino incorporada (caso esquina)

---

## Qué cambió

La aclaración de Constantino activó un fix adicional en `polyline_closer.py`:

**Antes (post-TASK_023):** `boundary_path` siempre devolvía `[end]` — 1 línea directa siempre.

**Ahora:** routing condicional:
- Ambos nodos en el mismo margen → `[end]` (1 línea)
- Nodo en vertical + nodo en horizontal → `[corner, end]` (2 líneas por el vértice)

## Combinación de fixes en TASK_026

Dos archivos modificados:

1. **`polyline_closer.py`**: restaura `corner_between()` solo para casos de márgenes cruzados
2. **`arc_rebuilder.py`**: maneja 1 o 2 segmentos de cierre con endpoints corregidos (el corner intermediario pasa directo, sin corrección — es un vértice exacto del clip rect)

## Verificación

```
Caso normal (LEFT+LEFT):
  2 entities, max_gap = 0.0000000000 mm

Caso esquina (LEFT+BOTTOM):
  3 entities, max_gap = 0.0000000000 mm
  [arco] -> [línea al corner (15,15)] -> [línea al arco inicial]
```

Reporte completo actualizado: `coordination/reports/PUNTO_TASK_026_REPORT.md`

---

**TASK_026 completada incluyendo caso esquina. Listo para próxima tarea.**
