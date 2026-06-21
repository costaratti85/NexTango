# Reporte: Copy-paste Blocks — VEGA_TASK_002

**Agente:** Vega  
**Fecha:** 2026-06-18  
**Tarea:** VEGA_TASK_002_PASTE_BLOCKS  
**Estado:** COMPLETO

---

## Qué se implementó

En la pantalla de resultados del panel decorativo (`/`), luego de generar un DXF, aparecen dos nuevas secciones con texto listo para copiar y pegar:

1. **Para el Presupuesto** — bloque tab-separado para pegar en B25 del Excel
2. **Para la OT** — bloque tab-separado para pegar en columna B de la hoja `ot1`

Cada sección tiene un botón "Copiar" con feedback visual ("✓ Copiado" por 2 segundos).

---

## Formato de los bloques

### Presupuesto
```
{cant}[TAB]{descripcion}[TAB][TAB][TAB]{precio}
```
- B → cantidad
- C → descripción (D y E vacíos — merged cells del template)
- F → precio total SIN IVA (suma para esa línea)

### OT
```
{cant}[TAB]{descripcion_ot}
```

Descripción = `Panel "{patron}" / {ancho} x {alto} / en {material_formateado}`  
Descripción OT = ídem + ` / [{patron}.dxf]`

---

## Formato del material — función `_format_material_label`

Nueva función a nivel módulo en `panel_sales_local_app.py`.

Lee `familia` del `material_table.json`. Si no encuentra la entrada, cae a fallback por nombre de material.

| Familia | Formato | Ejemplo |
|---------|---------|---------|
| `hierro` | `N°{calibre}` | `N°18` |
| `galvanizada` | `Galv N°{calibre}` | `Galv N°18` |
| `inox304` | `Inox 304 {espesor}mm` | `Inox 304 1.25mm` |
| `inox430` | `Inox 430 {espesor}mm` | `Inox 430 2mm` |

---

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `Programas_hechos/Panel Decorativo/material_table.json` | Campo `"familia"` agregado a los 28 entries |
| `panel_sales_local_app.py` — `MaterialTable.add()` | Normaliser preserva `familia` |
| `panel_sales_local_app.py` | Nueva función `_format_material_label()` |
| `panel_sales_local_app.py` — `render_form()` | CSS para `.paste-block`, `.paste-textarea`, `.btn-copy` |
| `panel_sales_local_app.py` — `render_form()` | Cómputo de texto paste + HTML de los dos bloques |
| `panel_sales_local_app.py` — `<script>` | Función JS `copyPasteBlock(btn, textareaId)` con `navigator.clipboard` y feedback visual |

---

## Tests

```
31 passed, 4 errors (pre-existentes — PermissionError tmp_path en Windows)
```

Sin regresiones.

---

## Para ver los cambios

```
python tools/run_panel_sales_app.py
```

Generar un panel normalmente → en el card de resultado aparecen los dos bloques al final, debajo de las Advertencias.
