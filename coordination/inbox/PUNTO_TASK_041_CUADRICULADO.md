# PUNTO_TASK_041 — Nuevo patrón preset: "Cuadriculado"

**Asignado a:** Punto  
**Prioridad:** Media  
**Fecha:** 2026-06-30  
**Referencia:** Pedido de Constantino

---

## Qué es

Un nuevo patrón preset (análogo al Tresbolillo) que genera una grilla recta
(sin escalonamiento) con una sola figura repetida: círculo o cuadrado.

El usuario elige:
- **Forma**: círculo (con diámetro) o cuadrado (con lado)
- **Offset X** (mm): distancia centro a centro en X
- **Offset Y** (mm): distancia centro a centro en Y

---

## Archivos a crear / modificar

### 1. `Programas_hechos/Panel Decorativo/geometry/cuadriculado_pattern.py` — NUEVO

Análogo a `tresbolillo_pattern.py`. La grilla recta es más simple: una sola
figura en (0, 0), con step_x = offset_x y step_y = offset_y (sin factor √3).

```python
from geometry.piece import Piece
from geometry.arc_segment import ArcSegment


def create_cuadriculado_piece(hole_shape, hole_size_mm, offset_x_mm, offset_y_mm):
    """
    hole_shape:   'circle' o 'square'
    hole_size_mm: diámetro (circle) o lado (square)
    offset_x_mm:  distancia centro a centro en X
    offset_y_mm:  distancia centro a centro en Y
    """
    piece = Piece()

    if hole_shape == 'circle':
        radius = hole_size_mm / 2.0
        piece.add(ArcSegment(0, 0, radius, 0, 360))

    elif hole_shape == 'square':
        # Cuadrado centrado en (0,0), lado = hole_size_mm
        half = hole_size_mm / 2.0
        # 4 segmentos de línea como ArcSegment de radio 0 o usar LineSegment
        # Ver cómo está implementado en otros patrones DXF.
        # Alternativa: agregar un helper _add_square(piece, cx, cy, side)
        # que emita 4 LineSegment (si existe esa clase) o 4 ArcSegment(r=0).
        # Elegir el enfoque que ya usa el motor; si no hay LineSegment,
        # preguntar a Nova antes de inventar una nueva clase.
        pass  # completar según la infraestructura disponible

    step_x = offset_x_mm
    step_y = offset_y_mm
    return piece, step_x, step_y
```

**Importante:** el cuadrado requiere investigar si el motor tiene `LineSegment`
o si hay que emitirlo como 4 arcos degenerados (radio 0). Ver `geometry/`.

---

### 2. `Programas_hechos/Panel Decorativo/main.py`

En `load_pattern(settings)`, después del bloque `if settings.pattern_type == "tresbolillo":`:

```python
if settings.pattern_type == "cuadriculado":
    piece, step_x, step_y = create_cuadriculado_piece(
        settings.hole_shape,
        settings.hole_size,
        settings.step_x,
        settings.step_y,
    )
    return piece, step_x, step_y
```

Agregar también el import al tope:
```python
from geometry.cuadriculado_pattern import create_cuadriculado_piece
```

---

### 3. `Programas_hechos/Panel Decorativo/config/settings.py`

Agregar campos:
```python
hole_shape: str = "circle"   # 'circle' | 'square'
hole_size: float = 20.0      # diámetro o lado
```

(step_x y step_y ya existen en settings — los reutilizamos para offset_x/offset_y)

---

### 4. `apps/sistema_industrial/sistema_industrial/presets/legacy_panel_adapter.py`

En `LEGACY_PATTERN_TYPES` agregar `"cuadriculado"`.

En la función que despacha por `pattern_type`:
```python
if request.pattern_type == "cuadriculado":
    settings.hole_shape = request.hole_shape      # nuevo campo
    settings.hole_size  = request.hole_size_mm    # nuevo campo
    settings.step_x = request.offset_x_mm
    settings.step_y = request.offset_y_mm
    return settings
```

---

### 5. `apps/sistema_industrial/sistema_industrial/presets/panel_service.py`

En `LegacyPanelServiceInput` agregar:
```python
hole_shape: str = "circle"
hole_size_mm: float = 20.0
offset_x_mm: float | None = None
offset_y_mm: float | None = None
```

---

### 6. `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`

#### 6a. Tarjeta en la galería de patrones

Después del card de Tresbolillo, agregar:
```html
<div class="pattern-card" id="pcard-cuadriculado"
     onclick="selectPattern('cuadriculado','Cuadriculado','cuadriculado',null,null,null)">
  <!-- thumbnail o SVG placeholder -->
  <div class="pattern-name">Cuadriculado</div>
</div>
```

#### 6b. Panel de parámetros inline (análogo a `#tres-inline`)

```html
<div id="cuad-inline" style="display:none;...">
  <div class="conditional-label">Parámetros del cuadriculado</div>
  <div class="form-row">
    <div class="form-group">
      <label>Forma</label>
      <select id="cuad-shape">
        <option value="circle">Círculo</option>
        <option value="square">Cuadrado</option>
      </select>
    </div>
    <div class="form-group" id="cuad-size-group">
      <label id="cuad-size-label">Diámetro mm</label>
      <input type="number" id="cuad-size" placeholder="ej. 20" min="0.1" step="0.1" value="20">
    </div>
  </div>
  <div class="form-row">
    <div class="form-group">
      <label>Offset X mm</label>
      <input type="number" id="cuad-ox" placeholder="ej. 30" min="0.1" step="0.1" value="30">
    </div>
    <div class="form-group">
      <label>Offset Y mm</label>
      <input type="number" id="cuad-oy" placeholder="ej. 30" min="0.1" step="0.1" value="30">
    </div>
  </div>
  <button class="btn-add" onclick="confirmCuadriculado()">Confirmar patrón →</button>
</div>
```

El selector de forma debe cambiar el label dinámicamente:
- "circle" → label = "Diámetro mm"
- "square" → label = "Lado mm"

#### 6c. JS: `selectPattern` para modo cuadriculado

En el bloque `if (mode === 'tresbolillo')` agregar el análogo:
```js
if (mode === 'cuadriculado') {
  document.getElementById('cuad-inline').style.display = '';
  return;
}
```

#### 6d. JS: `confirmCuadriculado()`

```js
function confirmCuadriculado() {
  var shape = document.getElementById('cuad-shape').value;
  var size  = parseFloat(document.getElementById('cuad-size').value);
  var ox    = parseFloat(document.getElementById('cuad-ox').value);
  var oy    = parseFloat(document.getElementById('cuad-oy').value);
  if (isNaN(size) || size <= 0) { alert('Tamaño inválido.'); return; }
  if (isNaN(ox)   || ox <= 0)   { alert('Offset X inválido.'); return; }
  if (isNaN(oy)   || oy <= 0)   { alert('Offset Y inválido.'); return; }
  var shapeName = shape === 'circle' ? 'Círculo d=' + size : 'Cuadrado l=' + size;
  selectedPattern = {mode:'cuadriculado', name:'Cuadriculado ' + shapeName,
                     ptype:'cuadriculado', file_path:null,
                     hole_shape:shape, hole_size_mm:size,
                     offset_x_mm:ox, offset_y_mm:oy,
                     step_x:null, step_y:null};
  _advanceToStep2();
}
```

#### 6e. Serialización del batch

En `buildBatch()`, agregar el caso cuadriculado análogo al tresbolillo:
```js
if (selectedPattern.mode === 'cuadriculado') {
  batch.panel_mode = 'cuadriculado';
  batch.hole_shape = selectedPattern.hole_shape;
  batch.hole_size_mm = selectedPattern.hole_size_mm;
  batch.offset_x_mm = selectedPattern.offset_x_mm;
  batch.offset_y_mm = selectedPattern.offset_y_mm;
}
```

#### 6f. Backend: `_handle_generate` / `_run_all_batches`

Leer los nuevos campos del batch y pasarlos al service:
```python
elif batch.get("panel_mode") == "cuadriculado":
    panel_mode = "cuadriculado"
    hole_shape = batch.get("hole_shape", "circle")
    hole_size_mm = float(batch.get("hole_size_mm", 20))
    offset_x_mm = float(batch.get("offset_x_mm", 30))
    offset_y_mm = float(batch.get("offset_y_mm", 30))
```

---

## Thumbnail

Generar un thumbnail SVG/PNG en `THUMBNAIL_DIR / "Cuadriculado.png"` al inicio,
análogo al de Tresbolillo. Puede ser un SVG inline con círculos o cuadrados en
grilla recta.

---

## Criterios de aceptación

- [ ] Seleccionar "Cuadriculado" en la galería muestra el panel de parámetros
- [ ] El selector Círculo/Cuadrado cambia el label del campo de tamaño
- [ ] Al generar, el DXF contiene la figura correcta repetida en grilla recta
- [ ] Offset X y Offset Y se respetan en el DXF generado
- [ ] El presupuesto inline muestra el patrón con los parámetros elegidos
- [ ] Al menos 2 tests nuevos: uno para círculo, uno para cuadrado
- [ ] El patrón "none" (sin perforación) no se ve afectado

## No necesita

- Integración con ERPNext
- Cambios en el presupuesto PDF / cotización
- Modificar el conversor de splines

---

Reportar en `coordination/channel/Nova/` al completar.

— Nova
