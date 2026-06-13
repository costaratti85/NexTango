# Reporte: Rediseño de la UI del módulo de paneles

**Agente:** Punto  
**Fecha:** 2026-06-11  
**Tarea:** PUNTO_TASK_001_UI_PANEL_REDESIGN

---

## Archivos modificados

### 1. `apps/sistema_industrial/sistema_industrial/presets/legacy_panel_adapter.py`

- **`DEFAULT_LEGACY_DIR`**: Cambiado de `"Paneles decorativos funcionando"` a `"Programas_hechos" / "Panel Decorativo"`.
- **`find_legacy_panel_dir()`**: Reemplazado con búsqueda por ascendencia que camina hasta 6 niveles adicionales desde `parents[4]` del archivo. Resuelve el caso de worktrees de git donde el archivo vive en un subdirectorio del repo real.
- **`LEGACY_PATTERN_TYPES`**: Agregado `"none"` (sin perforar).
- **`LegacyPanelRunRequest`**: Agregado campo `sheet_sizes: list | None` para lotes multi-pieza. Cuando está presente, sobreescribe `width_mm`/`height_mm`/`quantity`.
- **`_build_settings()`**: Maneja el tipo `"none"` generando un tresbolillo con diámetro mayor a la chapa (sin agujeros efectivos). Usa `sheet_sizes` del request cuando está presente.
- **`_raw_request_payload()`**: Incluye `sheet_sizes` en el payload de trazabilidad.
- **Nuevas funciones de librería**: `get_pattern_library_patterns()`, `add_pattern_to_library()`, `delete_pattern_from_library()` — operan sobre `pattern_library.json` del motor canónico dentro del contexto `_legacy_import_context`.

### 2. `apps/sistema_industrial/sistema_industrial/presets/panel_service.py`

- **`LegacyPanelServiceInput`**: Agregado campo `sheet_sizes: list | None`.
- **`legacy_pattern_type_for_panel_mode()`**: Agregado soporte para `"none"`.
- **`normalize_panel_input()`**: Propaga `sheet_sizes` al objeto normalizado.
- **`LegacyPanelService.run()`**: Pasa `sheet_sizes` al `LegacyPanelRunRequest`.

### 3. `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`

Rediseño completo de la UI y del servidor HTTP. Cambios principales:

- **Eliminado**: desplegable "Preset / tipo de panel", campos Filas y Columnas, `selected_mode` en `render_form()`.
- **Nuevo flujo de 10 pasos**: encabezado → forma → perforar toggle → patrón → margen → distribución → material/espesor → lista de piezas → tabla de lotes → generar.
- **Gestión de lotes en browser**: JavaScript acumula lotes en memoria; al generar, serializa como JSON en campo hidden y envía al servidor.
- **`build_sales_input()`**: Actualizado para aceptar `panel_mode="none"`, leer `sheet_sizes_text` (formato `"N de WxH"`), sin `rows`/`columns`.
- **`_run_all_batches()`**: Nueva función que recibe la lista de lotes JSON, ejecuta el motor para cada uno acumulando ítems, y produce un único DXF combinado.
- **Nuevos endpoints HTTP**:
  - `GET /api/patterns` — devuelve librería de patrones como JSON
  - `POST /api/patterns/add` — agrega patrón
  - `POST /api/patterns/delete` — elimina patrón
- **`render_form()`**: Sin parámetro `selected_mode`. La UI está completamente controlada por JS en el browser.

### 4. `tests/test_legacy_panel_adapter.py`

- `test_legacy_panel_adapter_finds_program`: Cambiado `"Paneles decorativos funcionando"` → `"Panel Decorativo"`.

### 5. `tests/test_panel_sales_local_app.py`

- Eliminados tests que dependían de `selected_mode` y de `rows`/`columns` en el HTML.
- Actualizado `test_render_form_contains_sales_controls` para los nuevos textos de la UI.
- Eliminados `rows` y `columns` de los form dicts de tests DXF.
- Agregados 4 nuevos tests: `test_render_form_contains_all_steps`, `test_render_form_contains_dxf_pattern_section`, `test_render_form_no_rows_columns_fields`, `test_render_form_no_duplicate_preset_dropdown`.

---

## Compatibilidad del adapter con el motor canónico

**Compatible sin ajustes estructurales.** El motor en `Programas_hechos/Panel Decorativo/` tiene exactamente la misma interfaz que esperaba el adapter:

- `layout/cad_result_layout.py` existe y exporta `arrange_cad_result_items` — el adapter importaba `layout.cad_result_layout`, correcto.
- `dxf/mixed_exporter.py` existe con `MixedDXFExporter().save(...)` — correcto.
- `config/settings.py` tiene la misma clase `Settings` con todos los atributos esperados.
- `main.py` exporta `create_cad_result_items_from_batch(settings)` — correcto.
- `config/pattern_library.py` exporta `PatternLibrary` con `add_pattern()`, `delete_pattern()`, `get_names()`, `get_pattern()` — correcto.

La única diferencia menor: también existe `dxf/cad_result_layout.py` (idéntico a `layout/cad_result_layout.py`). No afecta al adapter.

---

## Descripción del resultado por modo

### Tresbolillo + Cortar en borde (`cut_partial_figures=True`)
Toggle "Si" en perforar, "Tresbolillo", "Cortar en borde". El motor genera el patrón hexagonal completo considerando el margen; los agujeros que caen sobre el límite del área útil se cortan con la forma del clip de la chapa. Resultado: panel con agujeros parciales en los bordes.

### Tresbolillo + Figuras completas centradas (`cut_partial_figures=False`)
Toggle "Figuras completas centradas". El motor calcula cuántos agujeros enteros caben en el área útil, descarta los que no caben completamente, y centra el arreglo simétricamente. Resultado: panel con agujeros completos distribuidos uniformemente, sin cortes.

### Patrón DXF de librería
La UI muestra la lista de patrones de `pattern_library.json`. Al seleccionar uno se cargan la ruta y los offsets. Los controles de agregar y borrar patrones llaman a `/api/patterns/add` y `/api/patterns/delete` que actualizan el JSON en `Programas_hechos/Panel Decorativo/pattern_library.json`.

### Sin perforar (`panel_mode="none"`)
Toggle "No" en perforar oculta toda la sección de patrón y distribución. El adapter setea un diámetro de tresbolillo mayor al doble de la dimensión de la chapa, lo que garantiza que ningún agujero entre. El motor produce únicamente el contorno exterior. Resultado: DXF con solo el rectángulo exterior de la pieza.

### Lote múltiple
Los lotes se acumulan en la tabla JS. Al "GENERAR DXF", todos los lotes se serializan como JSON en `batches_json`. El servidor ejecuta `_run_all_batches()` que procesa cada lote con el motor y produce un único DXF combinado. El layout usa `arrange_cad_result_items()` que agrupa por material/espesor y ordena por cantidad descendente dentro de cada grupo.

---

## Resultado de los tests

```
pytest tests/ (main repo post-cambios)
= 22 passed, 10 errors =
```

Los 10 errors son todos `PermissionError: [WinError 5] Acceso denegado: 'C:\Users\vendo\AppData\Local\Temp\pytest-of-vendo'` — fallo del fixture `tmp_path` de pytest en Windows por un directorio temporal bloqueado. Este problema es **pre-existente** (estaba presente antes de los cambios con 19 passed, 10 errors).

| Estado | Passed | Errors |
|--------|--------|--------|
| Antes (main repo original) | 19 | 10 |
| Después (con cambios) | 22 | 10 |

Los 3 tests adicionales que pasan son los nuevos tests de render que no requieren `tmp_path`. Todos los tests que no dependen del fixture bloqueado pasan correctamente.
