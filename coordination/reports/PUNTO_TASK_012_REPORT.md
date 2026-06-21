# PUNTO_TASK_012_REPORT — Generación de presupuesto

**Autor:** Punto  
**Fecha:** 2026-06-17  
**Estado:** Completo

---

## Resumen

Se implementaron las 4 partes de la tarea en el archivo:
`apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`

---

## Parte 1: `calculate_cost()` + costo por batch

**Funciones añadidas:**

- `_load_daily_prices()` — lee `daily_prices.json`; devuelve `(dict, prices_missing: bool)`.  
  `prices_missing=True` cuando el archivo no existe o todos los precios son 0/None.

- `calculate_cost(consumed_resources, material_name, daily_prices)` — calcula costo material,
  costo máquina y total. Implementación exacta de la spec.

**Integración en `_run_all_batches()`:**

- Se cargan los precios una vez antes del loop sobre ítems.
- Por cada ítem se calcula `cost_entry` y se añade al dict de `all_resources`:
  ```json
  {
    "costo_material": 20.00,
    "costo_maquina": 3.00,
    "costo_total": 23.00,
    "prices_missing": true   // solo cuando aplica
  }
  ```
- Si `consumed_resources` es `None` (material no en tabla), se incluye igual con valores 0.00.

---

## Parte 2: Página `/presupuesto`

**Función:** `render_presupuesto()` (nueva, ~170 líneas)

- Lee `Programas_hechos/Panel Decorativo/last_generate.json` (escrito por `_run_all_batches`).
- Si no existe, muestra mensaje con link a la página principal.
- Genera HTML imprimible con:
  - Header con número de presupuesto, fecha, cliente, trabajo
  - Tabla: Panel | Mat/Esp | Cant | Costo unit. | Subtotal
  - Fila de TOTAL
  - Sección "Recursos totales" (kg, tiempo de máquina, perforaciones acumuladas)
  - Sección "Precios aplicados" (4 parámetros, con indicador de ausencia)
- `@media print` oculta el topbar, barra de acciones y botones.
- Botón "Imprimir / PDF" llama `window.print()`.

**Ruta:** `GET /presupuesto` — añadida en `do_GET`.

**Botón "Ver presupuesto":** añadido en el resultado del generate, junto a "Descargar DXF".

---

## Parte 3: Persistencia JSON

**Archivos nuevos:**

- `PRESUPUESTOS_DIR` = `Programas_hechos/Panel Decorativo/presupuestos/`
- `PRESUPUESTO_COUNTER_FILE` = `Programas_hechos/Panel Decorativo/presupuesto_counter.json`
- `LAST_GENERATE_FILE` = `Programas_hechos/Panel Decorativo/last_generate.json`

**Funciones:**

- `_next_presupuesto_number()` — lee el counter, incrementa, persiste y devuelve el número.
- `_save_presupuesto(presupuesto)` — guarda `PRES_NNNN.json` con la estructura de la spec.

**Flujo:**

1. `_run_all_batches()` escribe `last_generate.json` al final (en bloque try/except para no
   romper el flujo si falla).
2. `render_presupuesto()` lee `last_generate.json`, asigna número y persiste `PRES_NNNN.json`
   al renderizar la página.

---

## Parte 4: Link "Presupuestos" en el topbar del admin

Añadido en `_TOPBAR_ADMIN_HTML`:
```html
<a href="/presupuesto" class="admin-link">Presupuestos</a>
```
Queda entre "Precios diarios" y "Volver al catálogo".

---

## Tests

```
32 passed, 8 warnings in 36.70s
```
Todos los tests existentes siguen pasando sin modificaciones.

Tests adicionales manuales:
- `calculate_cost({"material_kg": 10, "machine_seconds": 60}, "Galvanizado", prices)` → `{costo_material: 20.0, costo_maquina: 3.0, costo_total: 23.0}` ✓
- `calculate_cost({"material_kg": 10, "machine_seconds": 60}, "Acero negro", {})` → `{costo_total: 0.0}` ✓
- Imports de todas las funciones nuevas sin error ✓

---

## Criterios de aceptación

| # | Criterio | Estado |
|---|----------|--------|
| 1 | `POST /generate` incluye `cost` por batch con los 3 campos | ✓ |
| 2 | Sin `daily_prices.json` o precios=0, `cost` tiene valores 0 y `prices_missing: true` | ✓ |
| 3 | Después de generar aparece botón "Ver presupuesto" que abre `/presupuesto` | ✓ |
| 4 | `/presupuesto` muestra tabla de líneas, total, recursos totales, precios aplicados | ✓ |
| 5 | Página imprimible con `@media print` que oculta nav y botones | ✓ |
| 6 | Cada presupuesto queda guardado como `PRES_NNNN.json` | ✓ |
| 7 | Tests existentes siguen pasando | ✓ (32/32) |
