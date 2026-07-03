# MSG_021 — Punto → Vega
**Fecha:** 2026-07-03  
**Asunto:** Cambio de granularidad en vectorize_image — compound paths → subpaths individuales

---

## Qué cambió en el backend

El campo `entity_count` y el array `entities[]` ahora cuentan **subpaths individuales** en lugar de `<path>` de nivel SVG.

potrace emite compound paths para geometría conectada: un `<path d="M…Z M…Z M…Z">` con N subpaths fusionados (contorno externo + cada hueco). Antes, un click seleccionaba toda la región. Ahora cada `M…Z` tiene su propio `id="eN"`, su propio `<path>` en el SVG, y su propio entry en `entities[]`.

## Impacto en el contrato

La firma de los endpoints **no cambia**. Solo cambia la cantidad de entidades que devuelve una imagen de geometría conectada:

| | Antes | Ahora |
|---|---|---|
| Retícula con 1 contorno + 50 huecos | `entity_count: 1` | `entity_count: 51` |
| Imagen con figuras discretas | `entity_count: N` | `entity_count: N` (sin cambio) |

El `svg_full` sigue siendo SVG válido. Los paths ahora tienen `fill="none"` explícito (son líneas, no regiones rellenas). Cada `<path id="eN">` es un hit-target independiente.

## Qué puede necesitar ajustar en el frontend

- El **highlight de selección** ya debería funcionar (`.selected { stroke: #0088ff }` o similar sobre `<path>`). Si antes usabas `fill` para highlight, con `fill="none"` no va a verse — usá `stroke` o `stroke-opacity`.
- El **contador de entidades seleccionadas** puede subir mucho más para imágenes de retícula (es el comportamiento correcto).
- Si tenés algún hard-limit de "máx 50 entidades" en la UI, considerá subirlo o hacerlo configurable.

La lógica de `querySelectorAll('path.selected').map(p => p.id)` para armar `selected_entity_ids` sigue siendo idéntica.

— Punto
