# PUNTO_TASK_011 — Reporte de implementacion

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-17  
**Tarea:** Tabla de materiales predeterminada + parametros de precios diarios

---

## Estado: COMPLETO

Ambas partes implementadas en `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`.

---

## Parte 1 — Boton "Cargar tabla predeterminada" en `/materiales`

### Que se implemento

- Constante `DAILY_PRICES_FILE` agregada junto a las otras constantes de archivo.
- Boton "Cargar tabla predeterminada" visible en la parte superior de la tabla en `/materiales`.
- Al hacer click:
  1. Si la tabla tiene filas, muestra `confirm()` con el mensaje exacto de la tarea.
  2. Si confirma (o tabla vacia): llama `POST /api/materials/load_defaults` con `{replace: true}`.
  3. La tabla se recarga automaticamente.
- Endpoint `POST /api/materials/load_defaults`:
  - Importa `MATERIAL_DEFAULTS` desde `material_defaults.py`.
  - Limpia la clave `calibre` (no forma parte del schema de `MaterialTable`).
  - Reemplaza los entries en memoria y llama `table.save()`.
  - Retorna `{"ok": true, "loaded": 21, "previous": N}`.

### Archivo de datos

`apps/sistema_industrial/sistema_industrial/presets/material_defaults.py` — 21 filas (7 galvanizado, 7 acero negro, 7 inoxidable 304). Ya existia, no fue modificado.

---

## Parte 2 — Pagina `/precios`

### Que se implemento

- Funcion `render_precios()` — nueva pagina HTML con formulario de 4 campos:
  - `precio_segundo_maquina` ($/s)
  - `precio_kg_acero_negro` ($/kg)
  - `precio_kg_galvanizado` ($/kg)
  - `precio_kg_inoxidable` ($/kg)
- Al cargar la pagina, lee `daily_prices.json` (si existe) y pre-rellena los campos.
- Boton "GUARDAR PRECIOS" llama `POST /api/prices`, que escribe el JSON.
- Archivo guardado en: `Programas_hechos/Panel Decorativo/daily_prices.json`
- Endpoints nuevos:
  - `GET /api/prices` — devuelve contenido actual del JSON.
  - `POST /api/prices` — valida y guarda los 4 valores.

### Links de navegacion

- Header de `/materiales`: agrega links a `/materiales` (active) y `/precios`.
- Header de `/precios`: agrega links a `/materiales` y `/precios` (active).
- Topbar admin (`_TOPBAR_ADMIN_HTML`): agrega boton "Precios diarios" junto a "Tabla de materiales".

---

## Tests

- Syntax check del archivo modificado: OK.
- 28 tests pasan (igual que antes de los cambios).
- 4 errores en `test_panel_sales_local_app.py` son pre-existentes: requieren el motor legacy de CypCut que no esta instalado en el entorno. No fueron introducidos por esta tarea.

---

## Archivos modificados

- `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`

## Archivos no modificados (ya existian)

- `apps/sistema_industrial/sistema_industrial/presets/material_defaults.py`
