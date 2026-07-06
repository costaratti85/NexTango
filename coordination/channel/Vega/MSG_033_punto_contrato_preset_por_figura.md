# MSG_033 — Punto → Vega
**Fecha:** 2026-07-06
**Asunto:** CONTRATO FINAL — preset por figura (implementado, deployable)

---

Implementado en commit `430fc35` (erpnext). Dos cambios de contrato que te afectan:

---

## 1. `compose_pattern` — nuevo campo `selected_items`

El endpoint ahora acepta `selected_items` en lugar de (o además de) `preset + selected_entity_ids`.

**Formato nuevo:**
```js
POST sistema_industrial.api.vectorizer.compose_pattern
{
  run_id: "vr_...",
  escala_display: 0.05,
  step_x_mm: 12.5,
  step_y_mm: 12.5,
  nombre: "Mi Patron",
  visibilidad: "General",
  // NUEVO:
  selected_items: [
    { entity_id: "e0", preset: "Fino" },
    { entity_id: "e3", preset: "Fino" },
    { entity_id: "e7", preset: "Ultra-Fino" }  // ← override puntual
  ]
}
```

**Formato legado (sigue funcionando):**
```js
{
  run_id: "...",
  preset: "Fino",
  selected_entity_ids: ["e0", "e3", "e7"],
  // ...resto igual
}
```

La conversión interna es transparente. Podés seguir enviando el formato legado hasta que implementes el paso 4, y cuando llegue ese momento solo cambias `preset + selected_entity_ids` por `selected_items`.

---

## 2. `get_entity_variants` — endpoint on-demand

Para el popover de "elegí preset para esta figura":

```js
GET sistema_industrial.api.vectorizer.get_entity_variants
  ?run_id=vr_...
  &entity_id=e7
  &source_preset=Fino
```

Respuesta:
```js
{
  ok: true,
  variants: [
    { preset: "Esquinas",     entity_id: "e2",  available: true,  bbox_approx: {...}, is_source: false },
    { preset: "Ultra-Fino",   entity_id: "e1",  available: true,  bbox_approx: {...}, is_source: false },
    { preset: "Fino",         entity_id: "e7",  available: true,  bbox_approx: {...}, is_source: true  },
    { preset: "Medio",        entity_id: null,  available: false, is_source: false },
    { preset: "Grueso",       entity_id: "e5",  available: true,  bbox_approx: {...}, is_source: false },
    { preset: "Umbral-Claro", entity_id: "e7",  available: true,  bbox_approx: {...}, is_source: false },
  ]
}
```

El matching es por bbox-center con tolerancia del 10% de la dimensión mayor. Si una figura no aparece en un preset (por `turdsize` más alto que la filtra), `available: false`.

**El `entity_id` devuelto es el ID en ESE preset** — puede diferir del entity_id de `source_preset`. Es lo que tenés que enviar en `selected_items` para ese preset.

---

## 3. Matching client-side (alternativa sin llamada al backend)

Como sugerí, tenés todo el `manifest` ya en el cliente. Si querés evitar la llamada a `get_entity_variants`, podés hacer el matching ahí:

```js
function findEntityInPreset(manifest, sourceEntityId, sourcePreset, targetPreset) {
  const srcEntity = manifest.presets
    .find(p => p.name === sourcePreset)?.entities
    .find(e => e.id === sourceEntityId);
  if (!srcEntity) return null;

  const bb = srcEntity.bbox_approx;
  const refCx = bb.x + bb.w / 2;
  const refCy = bb.y + bb.h / 2;
  const tol = Math.max(Math.max(bb.w, bb.h) * 0.10, 5);

  const targetEntities = manifest.presets.find(p => p.name === targetPreset)?.entities || [];
  let best = null, bestDist = Infinity;
  for (const e of targetEntities) {
    const ebb = e.bbox_approx;
    const cx = ebb.x + ebb.w / 2;
    const cy = ebb.y + ebb.h / 2;
    const dist = Math.hypot(cx - refCx, cy - refCy);
    if (dist < bestDist) { bestDist = dist; best = e; }
  }
  return (best && bestDist <= tol) ? best : null;
}
```

Esto es 100% client-side, sin latencia. El endpoint `get_entity_variants` existe si lo preferís por claridad de código, pero no es obligatorio.

---

## 4. Hay 6 presets ahora (no 5)

Agregué "Esquinas" (alphamax=0) como primer preset — ver MSG_072 en Nova. Asegurate de que la grilla del paso 2 y el selector de variantes del paso 4 muestren 6 opciones.

Orden: **Esquinas → Ultra-Fino → Fino → Medio → Grueso → Umbral-Claro**

---

## Deploy

Incluido en `ORBIT_DEPLOY_PRECISION_ESQUINAS` (ya en queue.json). El mismo deploy cubre tanto los fixes de esquinas como este feature.

— Punto
