# MSG_021 — Punto → Nova: TASK_034 v2 — cambio a MTEXT

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-19  
**Ref:** TASK_034 (textos DXF justificados a la derecha)

---

Nova, el fix inicial de TASK_034 no funcionó en el visor de Constantino. Completé la corrección.

---

## Por qué no funcionó el TEXT con halign=2

El DXF generado tenía `group 72 = 2` (RIGHT) correctamente escrito. El visor de Constantino lo ignora y siempre renderiza desde el punto de inserción (izquierda). Este es un comportamiento incorrecto pero común en visores CAD simplificados (CypCut, GStarCAD, etc.).

## Fix (v2): cambio de TEXT a MTEXT

La entidad MTEXT usa `attachment_point` (group 71) para la alineación:
- `71 = 3` → Top-Right: el insert es el borde derecho del texto → visualmente right-aligned
- `71 = 7` → Bottom-Left: el insert es el borde izquierdo → visualmente left-aligned

Esta representación es explícita en la geometría del texto y no requiere que el visor interprete ningún flag de alineación. Todos los visores modernos la soportan.

**Archivo modificado:** `geometry/text_label.py` — `export_dxf()` reemplaza `msp.add_text()` con `msp.add_mtext()` usando el `attachment_point` correspondiente.

## Verificación

- `1.6mm` (label material): MTEXT, insert=(-200, 150), attach=3(TR) ✓
- `x2` (label cantidad): MTEXT, insert=(150, -300), attach=3(TR) ✓
- 31 tests passed ✓

Reporte actualizado: `coordination/reports/PUNTO_TASK_034_REPORT.md`

— Punto
