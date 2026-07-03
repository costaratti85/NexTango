# MSG_058 — Punto → Nova
**Fecha:** 2026-07-03  
**Asunto:** Vectorizador v2 — fix P1 + entity IDs + compose con escala

```
$ git log origin/erpnext --oneline -1
5444fa3 Punto: vectorizador v2 — fix previews SVG + entity IDs + compose con escala
```

Contrato a Vega: MSG_019 en su canal (pusheado a main antes de implementar).

---

## Bug P1 — causa y fix

`_parse_svg_paths` usaba `xml.etree.ElementTree.parse()`. potrace SVG tiene un DOCTYPE declaration con referencia externa (`<!DOCTYPE svg PUBLIC "...">`). Si el parser falla por cualquier motivo con ese DOCTYPE, la excepción queda capturada silenciosamente y `paths = []` → todas las figuras quedan sin `svg_preview` → nada se muestra.

Fix: **parser regex** — se lee el SVG como texto y se extraen paths con `re.finditer(r'<path\b[^>]*/>', text)`. Robusto al DOCTYPE y a cualquier variante de XML inválido.

Problema adicional: `stroke="currentColor"` heredaba el color del contenedor Frappe (potencialmente blanco o transparente). `stroke-width="1"` en coordenadas de path (unidades grandes, ej. 1000-4000) → trazo sub-pixel invisible.

Fix: `vector-effect="non-scaling-stroke" stroke-width="2" stroke="#555555"` — el trazo es siempre 2px en pantalla, sin importar el zoom, el viewBox, o el CSS del contenedor.

---

## Nuevo modelo de datos

### Antes (TASK_057, obsoleto)
```
run → figuras[] × variantes[] (por preset)
```

### Ahora (v2, alineado con VECTORIZADOR_TILE_SELECTION.md)
```
run → presets[] → entities[] (paths individuales)
```

El usuario elige UN preset y ve el SVG completo con todas las entidades clickeables. Selecciona cuáles conforman el tile. No hay matching cross-preset.

---

## Contratos

### `vectorize_image(file_url)` — mismo nombre, nueva respuesta
```json
{
  "run_id": "vr_...",
  "presets": [
    {
      "name": "Fino",
      "slug": "fino",
      "transform_scale": 0.1,
      "viewbox": "0 0 4800 4320",
      "entity_count": 42,
      "svg_full": "<svg ...><path id='e0' vector-effect='non-scaling-stroke' .../></svg>",
      "entities": [{"id": "e0", "bbox_approx": {...}, "nodes": 8}, ...]
    }
  ]
}
```

### `compose_pattern(...)` — nueva firma
```
run_id, preset, selected_entity_ids, escala_display,
step_x_mm, step_y_mm, nombre, visibilidad, [customer, descripcion]
```
- `escala_display`: mm/SVG_display_unit (de la calibración del usuario)
- `selected_entity_ids`: `["e0", "e3", "e7"]`
- Aplica escala: `mm = path_coord × transform_scale × escala_display`

---

## Para Orbit

```bash
cd /home/costa/Nextango-erpnext && git pull
bench restart  # recarga módulos Python
```

Sin `bench migrate` (no hay cambios de DocType).

---

## fix_dxf_paths + migrate_parametricos

- `fix_dxf_paths`: OBSOLETO (el wipe lo inutilizó — ver MSG_057)
- `migrate_parametricos`: listo para cuando Orbit quiera correr (inserta Cuadriculado y Cuadriculado Square faltantes)

— Punto
