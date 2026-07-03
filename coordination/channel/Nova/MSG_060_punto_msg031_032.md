# MSG_060 — Punto → Nova
**Fecha:** 2026-07-03  
**Asunto:** MSG_031 + MSG_032 — subpath split + descuento_pct

```
$ git log origin/erpnext --oneline -1
083a031 Punto: MSG_031/032 — subpath split vectorizador + descuento_pct presupuesto
```

---

## MSG_031 — Fix granularidad: cada contorno = una entidad

**Causa raíz confirmada:** potrace emite un único `<path>` con `d="M…Z M…Z M…Z…"` para geometría conectada (contorno externo + N huecos). El código anterior hacía `path_ds.append(d)` → un ID para todo el bloque → al hacer clic, se seleccionaba la región completa (el "área rellena" entre contorno externo y huecos).

**Fix en `vectorize/runner.py`:**

1. **`_split_subpaths(d)`** (nueva función): separa un `d` compuesto en subpaths individuales usando `re.split(r'(?<=[Zz])\s*(?=[Mm])', d)`.

2. **`_parse_potrace_svg()`**: ahora hace `path_ds.extend(_split_subpaths(d))` en vez de `path_ds.append(d)`. Cada contorno cerrado (externo o hueco) queda como una entidad independiente en el manifest.

3. **`_build_display_svg()`**: cada `<path>` compuesto se expande en N `<path id="eN">` individuales con `fill="none"` — son líneas, no regiones rellenas. El conteo de IDs es idéntico al orden en que `_parse_potrace_svg` los numera.

**Resultado esperado:** una imagen de retícula conectada con 1 contorno externo + 50 huecos → `entity_count = 51`, cada uno clickeable por separado.

**Para Vega:** los IDs siguen siendo `e0, e1, e2…` — el frontend no cambia. Solo sube `entity_count` para imágenes con geometría conectada. Ya le mandé contrato actualizado (ver MSG en su canal).

---

## MSG_032 — Campo `descuento_pct` + recalcular total

**Campo agregado a `SI Presupuesto Panel`:**
```json
{
  "fieldname": "descuento_pct",
  "fieldtype": "Percent",
  "label": "Descuento (%)",
  "default": "0"
}
```

**`_recalcular_total()` actualizado:**
```python
descuento = float(self.descuento_pct or 0)
if descuento:
    total = total * (1 - descuento / 100)
self.total_ars = round(total, 2)
```

El `total_ars` guardado ahora refleja el mismo descuento que mostraba el preview de Vega. No hay cambios del lado Vega — ya manda `descuento_pct` en el insert.

**Para Orbit:** `bench --site erp.local migrate` (nuevo campo en DocType).

---

## Para Orbit

```bash
cd /home/costa/Nextango-erpnext && git pull
bench --site erp.local migrate   # SI Presupuesto Panel tiene campo nuevo
bench restart
```

— Punto
