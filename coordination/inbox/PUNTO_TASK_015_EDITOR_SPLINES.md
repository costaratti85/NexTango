# PUNTO_TASK_015 — Editor de splines: vista superpuesta + borrar entidad + dibujar arco

**De:** Nova  
**Para:** Punto  
**Fecha:** 2026-06-17  
**Prioridad:** Alta

---

## Contexto

La pantalla "Convertir splines — Vista previa antes/después" actualmente muestra dos paneles side-by-side (Original | Convertido). El usuario quiere poder editar el resultado de la conversión directamente en el browser: borrar entidades mal convertidas y reemplazarlas con arcos trazados a mano.

---

## Parte 1 — Vista superpuesta (reemplaza los dos paneles)

En lugar de dos paneles separados, mostrar UN SOLO canvas con ambas capas:

- **Capa original**: trazo gris claro `#bbb`, stroke-width `0.5px` en unidades SVG (equivale a línea fina), opacidad 0.5
- **Capa convertida**: trazo azul `#1a6fa8`, stroke-width `0.5px`, opacidad 1.0

Checkboxes encima del canvas para mostrar/ocultar cada capa:
```
[✓] Mostrar original (gris)   [✓] Mostrar convertido (azul)
```

El canvas debe tener zoom/pan con rueda del mouse y drag (ya existe en el código actual — reutilizar la misma lógica).

El viewBox del SVG combinado es la unión de los bounding boxes de ambos DXFs.

---

## Parte 2 — Editor de entidades del convertido

### Estado del editor

El editor maneja una lista de entidades en JS (`_editEntities[]`), cargada desde el DXF convertido al abrir el canvas. Cada entidad es un objeto:

```javascript
// Línea
{ type: 'line', x1, y1, x2, y2, id }
// Arco
{ type: 'arc', cx, cy, radius, startAngle, endAngle, id }  // ángulos en grados, CCW
```

### Renderizado editable

Las entidades del convertido se dibujan como elementos SVG con `data-id` y cursor pointer. Al hacer hover, se resaltan. Al hacer click, se seleccionan (borde rojo, stroke más grueso).

### Borrar entidad

Tecla `Delete` o `Backspace` con una entidad seleccionada:
1. La entidad se elimina de `_editEntities[]`
2. Se recalculan sus dos endpoints (para arco: start point y end point; para línea: (x1,y1) y (x2,y2))
3. Los dos endpoints quedan en `_freeNodes[]` — se dibujan como círculos rojos rellenos de 4px de radio
4. El cursor cambia a crosshair — "modo arco activo"

### Dibujar arco de reemplazo

Con dos nodos libres activos (`_freeNodes.length === 2`):
1. El usuario mueve el mouse sobre el canvas — se dibuja en tiempo real el arco que pasaría por `_freeNodes[0]`, el punto actual del cursor, y `_freeNodes[1]` (preview en verde punteado)
2. Click confirma: se calcula el arco definitivo y se agrega a `_editEntities[]`
3. Los nodos libres se limpian, se vuelve a modo normal

**Cálculo del arco por 3 puntos** (todo en JS):

```javascript
function arcThrough3Points(p1, p2, p3) {
    // circunscribed circle of triangle p1-p2-p3
    const ax = p1.x, ay = p1.y;
    const bx = p2.x, by = p2.y;
    const cx = p3.x, cy = p3.y;
    const D = 2 * (ax*(by-cy) + bx*(cy-ay) + cx*(ay-by));
    if (Math.abs(D) < 1e-10) return null;  // collinear
    const ux = ((ax*ax+ay*ay)*(by-cy) + (bx*bx+by*by)*(cy-ay) + (cx*cx+cy*cy)*(ay-by)) / D;
    const uy = ((ax*ax+ay*ay)*(cx-bx) + (bx*bx+by*by)*(ax-cx) + (cx*cx+cy*cy)*(bx-ax)) / D;
    const radius = Math.hypot(ax-ux, ay-uy);
    // startAngle = angle from center to p1, endAngle = angle to p3
    const startAngle = Math.atan2(ay-uy, ax-ux) * 180/Math.PI;
    const endAngle   = Math.atan2(cy-uy, cx-ux) * 180/Math.PI;
    return { cx: ux, cy: uy, radius, startAngle, endAngle };
}
```

El arco va de `_freeNodes[0]` (startAngle) a `_freeNodes[1]` (endAngle), con p3 = cursor como punto de control. Si el resultado devuelve `null` (puntos colineales), mostrar un aviso y no dibujar.

### Renderizado del arc preview en SVG

Los arcos en SVG se pueden dibujar con `<path d="M x1 y1 A rx ry 0 largeArc sweep x2 y2">`. La dirección (sweep=0 CCW / sweep=1 CW) se determina por el signo del producto vectorial de los tres puntos.

### Botón "Descartar cambios"

Reinicia `_editEntities[]` desde el DXF original convertido. Limpia nodos libres.

---

## Parte 3 — Export y carga del patrón editado

Al hacer click en "Cargar patrón convertido" (que ya existe):

1. Serializar `_editEntities[]` a JSON
2. POST a un nuevo endpoint: `POST /api/patterns/finalize_edit`
   Body: `{ entities: [...], name: "NombrePatron", step_x: X, step_y: Y }`
3. El servidor genera un DXF limpio con las entidades recibidas, lo guarda como archivo temporal, y lo registra como patrón (igual que hace `convert_dxf_splines_clean` hoy)
4. Respuesta: `{ ok: true, file_path: "..." }` → recarga la página

### Endpoint `POST /api/patterns/finalize_edit`

```python
def _handle_finalize_edit(self, body: bytes):
    data = json.loads(body)
    entities = data["entities"]  # list of dicts {type, ...}
    name = data["name"]
    step_x = float(data.get("step_x", 84))
    step_y = float(data.get("step_y", 84))
    
    # Generar DXF con ezdxf desde las entidades
    import ezdxf
    doc = ezdxf.new()
    msp = doc.modelspace()
    for e in entities:
        if e["type"] == "line":
            msp.add_line((e["x1"], e["y1"]), (e["x2"], e["y2"]), dxfattribs={"layer": "ARCOS_CONVERTIDOS"})
        elif e["type"] == "arc":
            msp.add_arc(
                center=(e["cx"], e["cy"]),
                radius=e["radius"],
                start_angle=e["startAngle"],
                end_angle=e["endAngle"],
                dxfattribs={"layer": "ARCOS_CONVERTIDOS"}
            )
    out_path = PATTERNS_DIR / f"{name}_editado.dxf"
    doc.saveas(str(out_path))
    
    # Registrar como patrón (igual que convert flow)
    # ... usar lógica existente de upload pattern
```

---

## Nuevo endpoint `GET /api/patterns/entities?path=...`

Para cargar las entidades del DXF convertido en JS. Devuelve:

```json
{
  "entities": [
    { "type": "arc", "cx": 10.5, "cy": 20.3, "radius": 5.2, "startAngle": 0, "endAngle": 180, "id": "e0" },
    { "type": "line", "x1": 15.7, "y1": 25.5, "x2": 20.1, "y2": 18.3, "id": "e1" }
  ]
}
```

Usar ezdxf para leer el DXF y extraer entidades de la layer `ARCOS_CONVERTIDOS` (o todas si no existe esa layer).

---

## Criterio de aceptación

1. El modal muestra UN solo canvas con ambas capas superpuestas, líneas finas
2. Checkboxes para mostrar/ocultar cada capa
3. Click en una entidad del convertido → se selecciona (resalta)
4. Delete → entidad desaparece, aparecen 2 nodos rojos
5. Mover mouse → preview del arco en verde punteado en tiempo real
6. Click → arco confirmado, nodos limpios
7. "Cargar patrón convertido" exporta el DXF editado y recarga
8. "Descartar cambios" resetea al estado post-conversión
9. Tests existentes siguen pasando

## Reportar en

`coordination/reports/PUNTO_TASK_015_REPORT.md`
