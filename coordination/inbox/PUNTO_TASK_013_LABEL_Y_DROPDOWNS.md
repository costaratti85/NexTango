# PUNTO_TASK_013 — Fix etiqueta DXF + dropdowns en cascada material/espesor

**De:** Nova  
**Para:** Punto  
**Fecha:** 2026-06-17  
**Prioridad:** Alta

---

## Parte 1 — Fix posición de etiqueta en archivos DXF

### Problema

En `apps/sistema_industrial/sistema_industrial/cutting/dxf_writer.py` línea 37:

```python
if r.label:
    entities += _text(r.x, r.y - 25, r.label)
```

Esto coloca el texto en `X = r.x` (que es el borde izquierdo del primer rectángulo de la fila, tipicamente X=30) y `Y = r.y - 25` (25 unidades debajo de la fila). El resultado es que la etiqueta se superpone con el primer dibujo de la fila.

### Fix

1. **Mover la etiqueta a X=-200**, a la izquierda de toda el área de dibujo (que empieza en X=margin_mm=30).
2. **Right-align** el texto en DXF (para que el borde derecho del texto quede en X=-200 y no se extienda hacia el área de dibujo).
3. **Una sola etiqueta por fila** (las piezas en la misma fila tienen el mismo valor de `r.y` — usar ese criterio para emitir solo la primera).
4. **Y = centro vertical de la fila** → `r.y + r.height / 2`.

#### DXF right-aligned text

El text entity con right-alignment necesita los group codes `72` (horizontal justification) y `11`/`21` (second alignment point):

```python
def _text_right(x, y, value) -> list[str]:
    return [
        "0", "TEXT",
        "8", "LABEL",
        "10", str(x),   # first alignment point X
        "20", str(y),   # first alignment point Y
        "40", "20",     # text height
        "1", value,
        "72", "2",      # horizontal justification: 2 = right
        "11", str(x),   # second alignment point X
        "21", str(y),   # second alignment point Y
    ]
```

#### Lógica de "una etiqueta por fila"

En `write_rectangles_dxf`, después del loop de rectángulos, agregar un set para rastrear las Y ya etiquetadas:

```python
labeled_y: set[float] = set()
for r in rectangles:
    # ... líneas ...
    if r.label and r.y not in labeled_y:
        labeled_y.add(r.y)
        entities += _text_right(-200, r.y + r.height / 2, r.label)
```

### Archivos a modificar

- `apps/sistema_industrial/sistema_industrial/cutting/dxf_writer.py`

---

## Parte 2 — Dropdowns en cascada: material → espesor

### Situación actual

En el paso 3 de la UI principal (`panel_sales_local_app.py`), hay un único combo desplegable:

```
Acero negro — 2.0 mm
Galvanizado — 1.006 mm
...
```

Cuando el usuario selecciona una opción, se rellenan los hidden inputs `p-material` y `p-espesor`.

### Nuevo comportamiento: dos dropdowns

Reemplazar el combo único por dos dropdowns en cascada:

**Dropdown 1 — Material:**
```html
<select id="p-mat-tipo">
  <option value="">Selecciona material...</option>
  <option>Galvanizado</option>
  <option>Acero negro</option>
  <option>Inoxidable 304</option>
</select>
```
Populated dinámicamente con los materiales únicos del `/api/materials` response (mismos que antes, solo los que están cargados en la tabla).

**Dropdown 2 — Espesor** (se habilita al seleccionar material):
```html
<select id="p-mat-espesor" disabled>
  <option value="">Primero selecciona material</option>
</select>
```

Al seleccionar un material, filtrar las entradas del API response y poblar las opciones de espesor:
- Si el material es **Galvanizado** o **Acero negro**: mostrar `"N°{calibre} - {espesor}mm"` (ej: `"N°20 - 0.912mm"`)
- Si el material es **Inoxidable 304**: mostrar `"{espesor}mm"` (ej: `"0.6mm"`)
- El `value` de cada `<option>` = `espesor_mm` como número (para rellenar el hidden input)

Al seleccionar un espesor, rellenar los hidden inputs `p-material` y `p-espesor` (mismos que hoy).

### Agregar `calibre` al API response

Para que el JS pueda mostrar el número de calibre en las opciones, el endpoint `GET /api/materials` debe incluir el campo `calibre` en cada entrada.

**En `MaterialTable`:**
- Agregar `"calibre"` a la lista de campos soportados (opcional, default `"-"`)
- En `normalise()`: aceptar el campo `calibre` tal como viene (string, p.ej. `"20"` o `"-"`)
- `validate()`: no requiere validación estricta — cualquier string es válido

**En `_handle_material_load_defaults()`** (TASK_011): ya se removía el campo `calibre`. Cambiarlo para que lo INCLUYA en lugar de strippearlo.

**En `GET /api/materials`**: incluir el campo `calibre` en cada objeto JSON devuelto.

### Ejemplo de respuesta esperada del API

```json
[
  {"material": "Acero negro", "calibre": "20", "espesor_mm": 0.912, ...},
  {"material": "Acero negro", "calibre": "18", "espesor_mm": 1.214, ...},
  {"material": "Galvanizado", "calibre": "22", "espesor_mm": 0.853, ...},
  {"material": "Inoxidable 304", "calibre": "-", "espesor_mm": 0.6, ...}
]
```

### JS: lógica de los dos dropdowns

```javascript
let _allMaterials = [];  // cache del API response

async function loadMaterialDropdowns() {
    const res = await fetch('/api/materials');
    _allMaterials = await res.json();
    
    const tipos = [...new Set(_allMaterials.map(e => e.material))];
    const sel = document.getElementById('p-mat-tipo');
    sel.innerHTML = '<option value="">Selecciona material...</option>';
    tipos.forEach(t => {
        const opt = document.createElement('option');
        opt.value = t;
        opt.textContent = t;
        sel.appendChild(opt);
    });
}

function onMatTipoChange(sel) {
    const tipo = sel.value;
    const espSel = document.getElementById('p-mat-espesor');
    document.getElementById('p-material').value = tipo;
    document.getElementById('p-espesor').value = '';
    
    if (!tipo) {
        espSel.innerHTML = '<option value="">Primero selecciona material</option>';
        espSel.disabled = true;
        return;
    }
    
    const entries = _allMaterials.filter(e => e.material === tipo);
    espSel.innerHTML = '<option value="">Selecciona espesor...</option>';
    const esInox = tipo.toLowerCase().includes('inox');
    entries.forEach(e => {
        const opt = document.createElement('option');
        opt.value = e.espesor_mm;
        opt.textContent = esInox
            ? `${e.espesor_mm}mm`
            : `N°${e.calibre} - ${e.espesor_mm}mm`;
        espSel.appendChild(opt);
    });
    espSel.disabled = false;
}

function onMatEspesorChange(sel) {
    document.getElementById('p-espesor').value = sel.value;
}
```

### Archivos a modificar

- `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`

---

## Criterio de aceptación

1. Al abrir un DXF de corte en CypCut (o cualquier visor), las etiquetas están a la izquierda del área de dibujo (X=-200), right-aligned, sin superponerse con ningún rectángulo
2. Solo aparece UNA etiqueta por fila horizontal (no una por pieza)
3. En la UI principal, el paso 3 muestra dos dropdowns: primero material, luego espesor
4. El dropdown de espesor está deshabilitado hasta seleccionar material
5. Para galvanizado y acero negro, las opciones muestran "N°XX - X.XXXmm"
6. Para inoxidable, las opciones muestran "X.Xmm"
7. Los hidden inputs `p-material` y `p-espesor` se rellenan correctamente al seleccionar
8. Tests existentes siguen pasando

## Reportar en

`coordination/reports/PUNTO_TASK_013_REPORT.md`
