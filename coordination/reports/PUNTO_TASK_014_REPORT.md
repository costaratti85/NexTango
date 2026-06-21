# PUNTO_TASK_014 — Reporte de ejecución

**Fecha:** 2026-06-17  
**Tarea:** Renombrar materiales + agregar Inoxidable 430 + 5° parámetro de precio  
**Estado:** COMPLETADO

---

## Cambios aplicados en `panel_sales_local_app.py`

### 1. `calculate_cost()` — nueva lógica de selección de precio (líneas ~549-564)

La condición anterior usaba dos ramas (`galvanizado` / `inoxidable` / else). La nueva usa cuatro:

- `"galvanizado" in mat` → `precio_kg_galvanizado`
- `"430" in mat` → `precio_kg_inoxidable_430`
- `"304" in mat or "inoxidable" in mat` → `precio_kg_inoxidable_304`
- else (chapa doble decapada y otros aceros) → `precio_kg_doble_decapada`

### 2. `_load_daily_prices()` — migración de claves viejas (líneas ~522-532)

Antes de evaluar los precios, se migran claves viejas si existen en el JSON:
- `precio_kg_acero_negro` → `precio_kg_doble_decapada` (con `pop`)
- `precio_kg_inoxidable` → `precio_kg_inoxidable_304` (con `pop`)

El conjunto `relevant_keys` se actualizó de 4 a 5 claves (reemplazando las viejas por las nuevas).

### 3. `render_precios()` — 5 campos (HTML + JS)

**HTML tabla:** 5 filas con IDs y labels correctos:
- `precio_segundo_maquina` — Precio por segundo de maquina ($/s)
- `precio_kg_doble_decapada` — Precio por kg — chapa doble decapada ($/kg)
- `precio_kg_galvanizado` — Precio por kg — galvanizado ($/kg)
- `precio_kg_inoxidable_430` — Precio por kg — inoxidable 430 ($/kg)
- `precio_kg_inoxidable_304` — Precio por kg — inoxidable 304 ($/kg)

**JS `savePrices()`:** array `fields` actualizado con los 5 nombres nuevos.

### 4. `_handle_prices_save()` — set `allowed` con 5 claves (líneas ~4059-4063)

El set `allowed` reemplaza las claves viejas (`precio_kg_acero_negro`, `precio_kg_inoxidable`) por las 5 claves nuevas.

### 5. `render_presupuesto()` — sección "Precios aplicados" (línea ~3568)

La grilla de precios aplicados ahora muestra los 4 precios por kg nuevos más el precio por segundo.

### 6. JS dropdown de espesor en `onMatTipoChange()` (línea ~1876)

La condición `var esInox = tipo.toLowerCase().indexOf('inox') !== -1` fue reemplazada por:

```javascript
var mostrarCalibre = entries[0] && entries[0].calibre && entries[0].calibre !== '-';
```

Así el formato del espesor depende del campo `calibre` del API (no del nombre del material). Si el primer entry tiene `calibre != '-'`, muestra `N°{calibre} - {espesor}mm`; si no, solo `{espesor}mm`.

---

## Verificación

- No quedan referencias a `precio_kg_acero_negro` ni `precio_kg_inoxidable` fuera de la lógica de migración.
- No quedan referencias a `esInox` en el JS.
- Las 5 claves nuevas aparecen consistentemente en: `_load_daily_prices`, `calculate_cost`, `render_precios` (HTML + JS), `_handle_prices_save`, y `render_presupuesto`.
