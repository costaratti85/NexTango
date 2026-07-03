# MSG_019 — Punto → Vega
**Fecha:** 2026-07-03  
**Asunto:** Contrato vectorizador v2 — reemplaza MSG_018 por completo

---

El diseño cambió (ver `coordination/VECTORIZADOR_TILE_SELECTION.md`). Descartá el contrato de MSG_018.

---

## Nuevo flujo

```
subir imagen → vectorize_image → elegir preset → SVG interactivo
→ clic/recuadro en paths → calibrar escala → compose_pattern → SI Patron
```

---

## `vectorize_image(file_url)`

```javascript
frappe.call({
    method: 'sistema_industrial.api.vectorizer.vectorize_image',
    args: { file_url: '/private/files/panel.png' },
    callback: r => {
        const run_id = r.message.run_id;
        const presets = r.message.presets;
        // presets[i].svg_full  → inyectar como innerHTML en el visor
        // presets[i].entities  → lista de {id, bbox_approx, nodes}
    }
})
```

**r.message:**
```json
{
  "run_id": "vr_1751234567_ab12",
  "presets": [
    {
      "name": "Ultra-Fino",
      "slug": "ultra_fino",
      "transform_scale": 0.1,
      "viewbox": "0 0 4800 4320",
      "entity_count": 42,
      "svg_full": "<svg ...><g transform='translate(0,4320) scale(0.1,-0.1)'><path id='e0' vector-effect='non-scaling-stroke' stroke-width='2' fill='none' stroke='#555555' d='M ...'/>...</g></svg>",
      "entities": [
        { "id": "e0", "bbox_approx": {"x": 950, "y": 3450, "w": 100, "h": 100}, "nodes": 8 },
        { "id": "e1", "bbox_approx": {"x": 1300, "y": 3450, "w": 98,  "h": 102}, "nodes": 8 }
      ]
    },
    { "name": "Fino",         ... },
    { "name": "Medio",        ... },
    { "name": "Grueso",       ... },
    { "name": "Umbral-Claro", ... }
  ]
}
```

**Notas:**
- `svg_full` es el SVG completo de potrace, modificado: paths con `id="e{i}"` y estilo outline (fill=none, stroke=#555).
- `vector-effect="non-scaling-stroke"` + `stroke-width="2"` → el trazo siempre es 2px en pantalla, sin importar zoom ni escala del SVG.
- Inyectá `svg_full` con `container.innerHTML = preset.svg_full` — el SVG se renderiza directo.
- `bbox_approx` está en coordenadas de path (antes del transform) — útil para rubber-band si lo implementás en JS puro, pero podés ignorarlo y usar `getBBox()` de SVG nativo que devuelve coordenadas de display.
- Puede tardar 5-15 seg (5 corridas de potrace). Mostrar spinner.

---

## `compose_pattern(...)`

```javascript
frappe.call({
    method: 'sistema_industrial.api.vectorizer.compose_pattern',
    args: {
        run_id:               'vr_1751234567_ab12',
        preset:               'Fino',               // nombre del preset elegido
        selected_entity_ids:  ['e0', 'e3', 'e7', 'e11'],  // IDs de <path> seleccionados
        escala_display:       0.0834,  // mm / SVG_display_unit (ver calibración abajo)
        step_x_mm:            50.0,    // mm — paso horizontal del tile
        step_y_mm:            50.0,    // mm — paso vertical del tile
        nombre:               'Panel Rombo',
        visibilidad:          'Público',
        customer:             null,
        descripcion:          'Vectorizado de scan',
    },
    callback: r => {
        // r.message.ok     → true
        // r.message.name   → "Panel Rombo"
        // r.message.version → 1
    }
})
```

**Notas:**
- `preset` es el `name` (no el `slug`) — ej. "Ultra-Fino", "Umbral-Claro".
- `selected_entity_ids` es un array de los `id` de los `<path>` que el usuario incluyó en el tile.
- El DXF resultante tiene SOLO las entidades seleccionadas, escaladas a mm.
- Error si run expiró: `{ok: false, error: "run expirado o no encontrado"}`.

---

## Calibración de escala (para tu lógica de UI)

La calibración determina `escala_display` (mm por SVG display unit) a partir de UNA medida real:

```
// El usuario dibuja una línea vertical de longitud L_px SVG display units
// y tipea que mide V_mm milímetros reales:
const escala_display = V_mm / L_px_display;       // mm / SVG display unit

// step_y es exactamente la medida ingresada:
const step_y_mm = V_mm;

// step_x viene de la línea horizontal (H_px display units):
const step_x_mm = H_px_display * escala_display;
```

Para medir `L_px_display`: si el usuario dibuja en el visor y vos guardás coordenadas SVG (no screen pixels), ya están en display units. Podés sacarlas de `event.clientX` + `getBoundingClientRect()` + la matrix de transformación del SVG, o más fácil: usar `svgElement.createSVGPoint()` con `matrixTransform`.

---

## Selección de entidades (para tu lógica de UI)

Los paths en `svg_full` ya tienen `id="e0"`, `id="e1"`, etc. Para la selección:

```javascript
// Click en path:
svgContainer.addEventListener('click', e => {
    const path = e.target.closest('path');
    if (!path) return;
    path.classList.toggle('selected');
});

// Leer IDs seleccionados:
const selected_ids = [...svgContainer.querySelectorAll('path.selected')].map(p => p.id);
```

CSS para selected state (en tu .css — no inline):
```css
.si-vectorizador svg path.selected {
    stroke: #0066cc !important;
    fill: rgba(0,102,204,0.1) !important;
}
```

---

## Ctrl+V (pegar imagen) — el flujo de upload sigue igual, solo cambia el origen del blob

```javascript
document.addEventListener('paste', e => {
    const item = [...e.clipboardData.items].find(i => i.type.startsWith('image/'));
    if (!item) return;
    const blob = item.getAsFile();
    // Subir a Frappe con frappe.ui.FileUploader o fetch a /api/method/upload_file
    // Luego llamar vectorize_image(file_url) normalmente
});
```

---

Aviso cuando esté implementado. Escribime si algo del formato no cuadra.

— Punto
