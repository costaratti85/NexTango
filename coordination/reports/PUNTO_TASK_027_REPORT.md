# PUNTO_TASK_027_REPORT — Regresión etiqueta DXF en producción

**Agente:** Punto  
**Fecha:** 2026-06-18  
**Estado:** COMPLETADO

---

## Causa raíz

TASK_025 modificó `dxf_batch_compiler.py` + `dxf_writer.py` — un flujo genérico que **NO es el utilizado en producción**.

El flujo real de producción es:

```
panel_sales_local_app._run_all_batches()
  → layout.arrange_cad_result_items(items)    ← genera TextLabel con texto largo
      → MixedDXFExporter().save(arranged, path)
          → item.export_dxf(msp)               ← TextLabel.export_dxf() sin justificación
```

Dos problemas en ese flujo:

1. **`layout/cad_result_layout.py` línea 49**: usaba `f"{material} {thickness} mm"` → texto largo tipo `"Chapa doble decapada 0.9 mm"`
2. **`geometry/text_label.py`** `export_dxf()`: sin parámetro de justificación → texto left-aligned por default de DXF

---

## Fix aplicado

### Archivo 1: `geometry/text_label.py`

Agregado parámetro `right_align=False` (default False para no romper etiquetas de cantidad).  
Cuando `right_align=True`, usa `ezdxf.enums.TextEntityAlignment.RIGHT` en `set_placement()`.

```python
def export_dxf(self, msp):
    text_entity = msp.add_text(self.text, dxfattribs={"height": self.height})
    if self.right_align:
        from ezdxf.enums import TextEntityAlignment
        text_entity.set_placement((self.x, self.y), align=TextEntityAlignment.RIGHT)
    else:
        text_entity.set_placement((self.x, self.y))
```

### Archivo 2: `layout/cad_result_layout.py`

Agregada función `_abbreviate_material(material, thickness)` que lee `material_table.json` y genera el formato corto:
- hierro → `N°{calibre}`
- galvanizada → `Galv N°{calibre}`
- inox304 → `Inox 304 {espesor}mm`
- inox430 → `Inox 430 {espesor}mm`

El `row_label` ahora usa:
```python
row_label = TextLabel(
    _abbreviate_material(material, thickness),
    -200,
    current_row_y + 150,
    TEXT_HEIGHT,
    right_align=True,   # ← texto a la derecha de x=-200, fuera del área de corte
)
```

Las `quantity_label` (`f"x{item.quantity}"`) no cambian — `right_align` por default es `False`.

---

## Verificación

```
Chapa doble decapada 0.9mm  → N°20
Chapa doble decapada 1.25mm → N°18
Chapa galvanizada 0.9mm     → Galv N°20
Inoxidable 430 1.25mm       → Inox 430 1.25mm
Inoxidable 304 1.0mm        → Inox 304 1mm
```

28 entradas verificadas. 49 tests pasan (sin cambio respecto a sesión anterior).

---

## Nota

La etiqueta de material en `dxf_batch_compiler.py` (TASK_025) sigue siendo correcta para ese flujo genérico pero ese flujo no es el de producción.
