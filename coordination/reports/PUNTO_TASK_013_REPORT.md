# PUNTO_TASK_013_REPORT — Fix etiqueta DXF + dropdowns en cascada material/espesor

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-17  
**Estado:** Completado

---

## Parte 1 — Fix posición de etiqueta en archivos DXF

### Archivo modificado

`apps/sistema_industrial/sistema_industrial/cutting/dxf_writer.py`

### Cambios realizados

1. **Nueva función `_text_right(x, y, value)`**: Emite una entidad DXF TEXT con right-alignment usando los group codes `72=2` (horizontal justification), `11`/`21` (second alignment point). El borde derecho del texto queda en X, extendiéndose hacia la izquierda.

2. **Una etiqueta por fila**: Se introdujo `labeled_y: set[float] = set()` antes del loop. La etiqueta se emite solo la primera vez que aparece un valor de `r.y` — las piezas en la misma fila comparten `r.y` y por lo tanto solo generan una etiqueta.

3. **Posición de la etiqueta**:
   - X: `-200` (a la izquierda del área de dibujo que empieza en X=30)
   - Y: `r.y + r.height / 2` (centrado vertical de la fila)

### Verificación

- Para 2 piezas en la misma fila (mismo `r.y`) + 1 pieza en fila separada → se generan exactamente 2 entidades TEXT (una por fila).
- La coordenada X=-200 aparece en el archivo generado.
- Los group codes de right-alignment (`72`, `2`, `11`, `21`) están presentes.

---

## Parte 2 — Dropdowns en cascada: material → espesor

### Archivo modificado

`apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`

### Cambios realizados

#### 2a. `MaterialTable.add()` — soporte de campo `calibre`

El método `add()` ahora incluye `calibre` en el dict normalizado:
- Si el entry tiene `calibre`, se guarda como string (ej: `"20"`).
- Si no viene, se guarda `"-"` (default para Inoxidable y entradas manuales sin calibre).

#### 2b. `_handle_material_load_defaults()` — incluye `calibre`

Se eliminó el strip del campo `calibre` que antes excluía ese campo al cargar la tabla predeterminada. Ahora se lee `entry.get("calibre", "-")` y se persiste junto a los demás campos.

El archivo `material_defaults.py` ya tenía el campo `calibre` en todos los registros (con `"-"` para Inoxidable 304), por lo que no requirió modificaciones.

#### 2c. GET `/api/materials` — devuelve `calibre`

El handler `_handle_material_list()` devuelve `table.list()` directamente, que ya incluye el campo `calibre` ahora que `add()` y `load_defaults` lo preservan. Sin cambios al handler en sí.

#### 2d. HTML/JS — dos dropdowns en cascada

Se reemplazó el combo único `p-mat-combo` por dos dropdowns:

- **`#p-mat-tipo`** (Material): se puebla con los materiales únicos del API response en orden de primera aparición.
- **`#p-mat-espesor`** (Espesor): inhabilitado hasta que se seleccione material. Al seleccionar:
  - Galvanizado / Acero negro → opciones con formato `N°{calibre} - {espesor_mm}mm`
  - Inoxidable (detectado por `.toLowerCase().includes('inox')`) → `{espesor_mm}mm`

La cache `_allMaterials` se carga una sola vez (o al presionar el botón refresh `⟳`). Los hidden inputs `p-material` y `p-espesor` se rellenan igual que antes.

---

## Criterios de aceptación — estado

| # | Criterio | Estado |
|---|----------|--------|
| 1 | Etiquetas en DXF a X=-200, right-aligned, sin superponerse | OK |
| 2 | Una sola etiqueta por fila horizontal | OK (verificado: 2 piezas en fila → 1 TEXT) |
| 3 | Step 3 muestra dos dropdowns (material, espesor) | OK |
| 4 | Dropdown espesor deshabilitado hasta seleccionar material | OK |
| 5 | Galvanizado/Acero negro → "N°XX - X.XXXmm" | OK |
| 6 | Inoxidable → "X.Xmm" | OK |
| 7 | Hidden inputs `p-material` y `p-espesor` se rellenan | OK |
| 8 | Tests existentes siguen pasando | OK (27 passed, error pre-existente en tmp_path de Windows no relacionado) |

---

## Tests ejecutados

```
27 passed, 4 deselected (tests de tmp_path omitidos por restricción de permisos de Windows preexistente)
```

Los tests unitarios de `MaterialTable`, `render_form`, `render_admin` y los de patrones pasan sin modificaciones.
