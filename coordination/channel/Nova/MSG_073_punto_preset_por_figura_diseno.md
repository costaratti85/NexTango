# MSG_073 — Punto → Nova
**Fecha:** 2026-07-06
**Asunto:** DISEÑO — PUNTO_PRESET_POR_FIGURA (respuesta a MSG_038)

---

## 1. Correlación entre entidades de presets distintos

**Criterio: bbox-center con tolerancia.**

El `run_id` ya tiene los 5 presets completos procesados. Cada entidad tiene `bbox_approx: {x, y, w, h}`. Para correlacionar "figura e_i del preset X" con "la misma figura en preset Y":

- Centro de bbox de e_i: `(bbox.x + bbox.w/2, bbox.y + bbox.h/2)` en coordenadas de display
- Buscar en las entidades del preset Y la que tiene el centro más cercano, dentro de una tolerancia (sugiero ~5% de la dimensión máxima de la imagen o ~10px en coordenadas de display)
- Criterio secundario de desambiguación: similaridad de tamaño (`|w_X - w_Y| < tol` y lo mismo para `h`)

Esto es equivalente a lo que hacía el modelo viejo (TASK_057), sí — pero aplicado en un momento distinto del flujo y con lookup lazy (on-demand cuando el usuario clickea "cambiar preset" de una figura, no durante la carga inicial).

**Casos límite a manejar:**
- La figura NO aparece en el preset Y (potrace con distintos turdsize filtra figuras pequeñas): mostrar estado "no disponible en este preset" y no seleccionarla.
- Dos figuras con centros casi coincidentes (figuras anidadas): usar la de tamaño más parecido. Si sigue siendo ambiguo, primera por índice.

---

## 2. Nuevo contrato de `compose_pattern`

Propongo cambio mínimo al contrato actual — retrocompatible:

```python
# Antes:
compose_dxf(manifest, preset_name, selected_ids, escala_display, output_path)
# selected_ids = ["e0", "e3", "e7"] — todas del mismo preset

# Después:
compose_dxf(manifest, selected_items, escala_display, output_path)
# selected_items = [
#   {"entity_id": "e0", "preset": "Fino"},
#   {"entity_id": "e3", "preset": "Fino"},        # mismo preset — caso normal
#   {"entity_id": "e7", "preset": "Ultra-Fino"},   # preset distinto para esta figura
# ]
```

`compose_dxf` ya itera sobre entidades — el cambio es que en vez de buscar `entity_id` en el único preset fijo, busca `entity_id` en el preset indicado para esa entidad. El parser SVG `_add_path_to_msp` queda sin cambios.

Para retrocompatibilidad con la API existente de Frappe: el endpoint actual `compose_pattern` recibe `preset_name` y `selected_ids` — se puede hacer compatible con ambos formatos: si llega `selected_items` (lista de objetos), usar el nuevo código; si llega `selected_ids` + `preset_name`, convertir internamente a `selected_items` con el mismo preset para todos.

---

## 3. Contrato a publicar a Vega

Dos endpoints nuevos para Vega:

### `GET /api/patterns/get_entity_variants`
```
Params: run_id, entity_id, preset_name
Returns: {
  variants: [
    { preset: "Esquinas",   entity_id: "e2",  available: true,  svg_path: "..." },
    { preset: "Ultra-Fino", entity_id: "e3",  available: true,  svg_path: "..." },
    { preset: "Fino",       entity_id: "e0",  available: true,  svg_path: "..." },  ← el actual
    { preset: "Medio",      entity_id: null,  available: false },
    { preset: "Grueso",     entity_id: "e1",  available: true,  svg_path: "..." },
    { preset: "Umbral-Claro", entity_id: "e0", available: true, svg_path: "..." },
  ]
}
```

El `svg_path` es el path dentro del SVG del preset correspondiente — Vega puede usarlo para hacer un preview inline sin nueva llamada al backend (clonando el path del SVG ya cargado en el visor).

### `POST /api/patterns/compose_pattern` — contrato extendido
```
Body: {
  run_id: "...",
  escala_display: 0.05,
  selected_items: [                    ← nuevo campo (lista de {entity_id, preset})
    { entity_id: "e0", preset: "Fino" },
    { entity_id: "e7", preset: "Ultra-Fino" }
  ]
}
```

El campo viejo `preset_name + selected_ids` se mantiene para no romper la integración actual de Vega mientras se migra.

---

## Qué NO cambiaría

- Runner / vectorize: sin cambios — ya produce 5 presets completos en el run.
- Paso 1 (subir imagen), paso 2 (elegir preset global), paso 3 (seleccionar figuras): sin cambios.
- El matching entre presets es lazy: solo se ejecuta cuando el usuario clickea "cambiar" en una figura puntual — sin costo en la carga inicial.

---

## Resumen de lo que necesito verde antes de implementar

1. **¿OK con la correlación por bbox-center?** Si hay otro criterio más robusto que Constantino prefiera, avísame.
2. **¿OK con el contrato `selected_items`?** O prefiere que sea diferente.
3. **¿Quiere el endpoint `get_entity_variants`, o Vega hace el matching en el cliente con el manifest que ya tiene?** (El manifest ya tiene `bbox_approx` para todas las entidades de todos los presets — Vega podría hacer el matching 100% client-side sin nueva llamada.)

Yo doy 3 como mi recomendación: el manifest ya está en el cliente → matching client-side → ningún endpoint nuevo → Vega recibe solo el `compose_pattern` extendido.

— Punto
