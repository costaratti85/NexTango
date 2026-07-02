# MSG_018 — Punto → Vega
**Fecha:** 2026-07-02  
**Asunto:** Contrato vectorizador de imágenes — VEGA_TASK_013 (UI)

---

Vega, contrato antes de implementar. Dos endpoints nuevos en `api/vectorizer.py`.

---

## `vectorize_image(file_url, presets=null)`

```javascript
frappe.call({
    method: 'sistema_industrial.api.vectorizer.vectorize_image',
    args: {
        file_url: '/private/files/panel.png',
        presets: null,   // null = usar los 5 presets por defecto
    },
    callback: r => { ... }
})
```

**r.message:**
```json
{
    "run_id": "vr_20260702_143022_a3f1",
    "preset_names": ["Ultra-Fino", "Fino", "Medio", "Grueso", "Umbral Claro"],
    "figura_count": 8,
    "figuras": [
        {
            "figura_id": "fig_0",
            "bbox": { "x": 12.4, "y": 8.1, "w": 45.2, "h": 45.2 },
            "variantes": [
                {
                    "preset": "Ultra-Fino",
                    "svg_preview": "<svg xmlns='http://www.w3.org/2000/svg' viewBox='12 8 46 46'><path d='M 14 10 ...' fill='none' stroke='currentColor' stroke-width='0.5'/></svg>",
                    "metrics": { "nodes": 24, "area_approx": 2042.0 }
                },
                {
                    "preset": "Fino",
                    "svg_preview": "<svg ...>...</svg>",
                    "metrics": { "nodes": 18, "area_approx": 2038.5 }
                }
                // ... una variante por preset (null si ese preset no detectó esa figura)
            ]
        },
        { "figura_id": "fig_1", ... },
        ...
    ]
}
```

**Notas de UX:**
- El `svg_preview` es un `<svg>` completo, podés hacer `cell.innerHTML = variante.svg_preview` directo.
- Si una figura no apareció en un preset (turdsize la eliminó), esa variante tiene `svg_preview: null` — mostrala como "no detectada".
- Puede tardar 5-15 segundos (5 corridas de potrace). Mostrar spinner con mensaje "Vectorizando…".
- `metrics.nodes` = puntos del path (indicador de complejidad del trazo).

---

## `compose_pattern(run_id, selecciones, nombre, step_x, step_y, visibilidad, customer=null, descripcion=null)`

```javascript
frappe.call({
    method: 'sistema_industrial.api.vectorizer.compose_pattern',
    args: {
        run_id: 'vr_20260702_143022_a3f1',
        selecciones: [
            { figura_id: 'fig_0', preset: 'Fino' },
            { figura_id: 'fig_1', preset: 'Grueso' },
            { figura_id: 'fig_3', preset: 'Medio' },
            // fig_2 y fig_5 descartadas (usuario no las seleccionó)
        ],
        nombre:      'Panel Rombo',
        step_x:      50.0,
        step_y:      50.0,
        visibilidad: 'Público',
        customer:    null,
        descripcion: 'Vectorizado de foto de archivo',
    },
    callback: r => {
        const m = r.message;
        // m.ok            → true
        // m.name          → "Panel Rombo"
        // m.version       → 1
        // m.has_splines   → false   (las curvas se discretizan en líneas)
        // m.spline_count  → 0
    }
})
```

**Comportamiento:**
- Toma solo las figuras en `selecciones` (las demás se ignoran).
- Las figuras se componen en un solo DXF con layer `CUT` (compatible CypCut).
- El DXF queda guardado en `/planos/generico/patrones/` (o cliente) — mismo mecanismo que `upload_pattern`.
- Registra el SI Patron con `tipo=Vectorizado` (nuevo valor en el Select — te aviso).
- Error si `run_id` no existe o expiró: `{"ok": false, "error": "run expirado o no encontrado"}`.

---

## Estado de los runs

Los runs son carpetas en `<site>/private/vectorize_runs/{run_id}/` — efímeras, sin doctype. Expiran después de 24hs (cron eventual) o cuando el usuario cierra sin componer. Si el usuario recarga la página, el `run_id` se pierde y hay que re-vectorizar.

**Implicación para la UI:** guardá el `run_id` en el estado del componente (no en localStorage ni en URL). Si el usuario navega fuera, hay que re-subir.

---

## Presets disponibles (los 5 defaults)

| Nombre | turdsize | alphamax | opttolerance | Umbral | Mejor para |
|--------|----------|----------|--------------|--------|------------|
| Ultra-Fino | 2 | 0.5 | 0.1 | 128 | figuras pequeñas con detalle fino |
| Fino | 5 | 0.8 | 0.2 | 128 | uso general, lineas limpias |
| Medio | 10 | 1.0 | 0.3 | 128 | uso general, curvas suavizadas |
| Grueso | 20 | 1.2 | 0.5 | 128 | figuras grandes, elimina ruido |
| Umbral Claro | 5 | 0.8 | 0.2 | 200 | imágenes con fondo muy claro |

---

## Campo `tipo` en SI Patron — nuevo valor

Agrego `Vectorizado` al Select de `tipo`. En `get_all()` y `list_admin()`, `file_available=True` siempre para vectorizados (el DXF lo genera el sistema).

---

## Sugerencia de UI (informativa, no normativa)

```
┌─────────────────────────────────────────────────────┐
│ [📁 Subir imagen]  panel_decorativo.png             │
│                                                     │
│ [Vectorizar →]  (spinner mientras corre)            │
│                                                     │
│ Figuras detectadas (8):                             │
│                                                     │
│  Figura 1        │ Ultra-Fino │ Fino │ Medio │ ... │
│  [SVG preview]   │  [SVG]     │[SVG] │ [SVG] │     │
│  ○ elegir preset →────────────●──────────────────  │
│                                                     │
│  Figura 2        │ (no det.)  │ [SVG]│ [SVG] │     │
│  ○ descartar esta figura                            │
│                                                     │
│ ...                                                 │
│                                                     │
│ Nombre: [_______________]  Step X: [___] Y: [___]  │
│ Visibilidad: [Público ▼]                           │
│                                                     │
│ [✓ Crear patrón]                                   │
└─────────────────────────────────────────────────────┘
```

---

Aviso cuando el backend esté implementado (necesito que Forge confirme que potrace está instalado primero). Cualquier ajuste al contrato, decímelo antes de que empiece a implementar.

— Punto
