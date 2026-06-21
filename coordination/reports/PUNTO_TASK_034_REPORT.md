# PUNTO_TASK_034 — Justificación de textos en DXF

**Fecha:** 2026-06-19  
**Estado:** Completada (v2 — cambio a MTEXT)

---

## Síntoma reportado (v2)

Los textos del DXF seguían apareciendo a la izquierda en el visor de Constantino aunque `group 72 = 2` estaba correctamente escrito en las entidades TEXT.

**Causa:** La entidad `TEXT` de DXF usa `group 72` (halign) para indicar alineación, pero muchos visores CAD (CypCut, GStarCAD, etc.) lo ignoran y siempre renderizan desde el punto de inserción (`group 10`) con alineación izquierda. Este es un comportamiento incorrecto pero común en visores simplificados.

---

## Solución final: cambio a MTEXT

**Archivo:** `Programas_hechos/Panel Decorativo/geometry/text_label.py`

`TEXT` entity → `MTEXT` entity. La entidad MTEXT expresa la alineación a través de `attachment_point` (group 71), que es universalmente soportado:

- `attachment_point = 3` → TR (Top-Right): el punto de inserción es el borde superior-derecho del texto. El texto se extiende hacia la izquierda. Equivale a right-aligned.
- `attachment_point = 7` → BL (Bottom-Left): el punto de inserción es el borde inferior-izquierdo. El texto se extiende hacia la derecha. Equivale a left-aligned.

```python
def export_dxf(self, msp):
    # MTEXT attachment_point: 3=TR (right-aligned), 7=BL (left-aligned)
    attachment_point = 3 if self.right_align else 7
    msp.add_mtext(
        self.text,
        dxfattribs={
            "insert": (self.x, self.y),
            "char_height": self.height,
            "width": 0,
            "attachment_point": attachment_point,
        },
    )
```

---

## Cambios en layout (v1, sin cambios en v2)

**Archivo:** `Programas_hechos/Panel Decorativo/layout/cad_result_layout.py`

- `row_label`: ya tenía `right_align=True`. Sin cambios.
- `quantity_label`: `right_align=True` + `x = current_x + 150`.

---

## Verificación

Layout real con un item de prueba genera:

| Texto | Insert | attach | Efecto visual |
|-------|--------|--------|---------------|
| `1.6mm` | (-200, 150) | 3 (TR) | Borde derecho en x=-200, texto hacia izquierda |
| `x2` | (150, -300) | 3 (TR) | Borde derecho en x=150, texto hacia izquierda |

DXF raw: `group 71 = 3` en ambas entidades MTEXT.  
Tests: 31 passed, 0 nuevos errores.
