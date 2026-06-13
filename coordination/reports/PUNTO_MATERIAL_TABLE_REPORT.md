# PUNTO_MATERIAL_TABLE_REPORT

**Agente:** Punto  
**Tarea:** PUNTO_TASK_006_MATERIAL_TABLE_SCREEN  
**Fecha:** 2026-06-13  
**Estado:** COMPLETO

---

## Resumen

Se implementó la pantalla de tabla de materiales en `/admin`, incluyendo almacenamiento JSON, tres endpoints REST y la sección UI correspondiente, todo integrado con el estilo visual existente.

---

## Cambios implementados

### 1. Clase `MaterialTable` (en `panel_sales_local_app.py`)

Clase con métodos `load()`, `save()`, `add(entry)`, `delete(material, espesor_mm)`, `list()`.

- Almacena en `Programas_hechos/Panel Decorativo/material_table.json`
- `add()` normaliza tipos numéricos, valida campos requeridos, y reemplaza en lugar de duplicar cuando ya existe la misma combinación material+espesor
- `delete()` lanza `KeyError` si no encuentra la entrada
- El `file_path` es resuelto en tiempo de construcción (no en tiempo de definición de clase) para permitir monkey-patching en tests

### 2. Endpoints REST

| Método | Path | Comportamiento |
|--------|------|---------------|
| `GET` | `/api/materials` | Devuelve la lista JSON de entradas |
| `POST` | `/api/materials` | Crea/actualiza una fila (JSON body) |
| `DELETE` | `/api/materials` | Elimina por `material`+`espesor_mm` (JSON body) |

Se agregó `do_DELETE()` al handler para soportar el método HTTP DELETE correctamente.

### 3. Sección UI en `/admin`

Nueva sección "Tabla de materiales" debajo del formulario de patrones DXF, con:

- Tabla con columnas: Material | Espesor mm | Densidad kg/m² | Vel. corte mm/s | T. perforación s | Consumible/perf. | Acciones
- Placeholder "Sin materiales cargados." cuando la lista está vacía
- Botón "Borrar" por fila con feedback visual (texto "Borrando..." → "✓ Borrado" → recarga)
- Formulario de alta con los 6 campos, validación JS en cliente y feedback visual (misma API que patrones: `fb-loading / fb-success / fb-error`)
- Contador de materiales en el título de la sección

Sigue el estilo CSS existente (`card`, `patterns-table`, `btn-action`, `btn-del`, `feedback-area`, etc.).

### 4. Tests nuevos (8 tests)

Todos en `tests/test_panel_sales_local_app.py`:

| Test | Qué verifica |
|------|-------------|
| `test_material_table_add_and_list` | add() + list() |
| `test_material_table_persists_to_json` | persistencia en disco |
| `test_material_table_delete` | delete() elimina correctamente |
| `test_material_table_delete_nonexistent_raises` | KeyError en entrada inexistente |
| `test_material_table_add_replaces_duplicate` | upsert en duplicados |
| `test_material_table_validates_required_fields` | ValueError en campos faltantes |
| `test_render_admin_contains_material_table_section` | HTML tiene todos los elementos |
| `test_material_api_add_list_delete` | ciclo completo por HTTP (GET → POST → GET → DELETE → GET) |

---

## Resultado de tests

| Antes | Después |
|-------|---------|
| 32 passed / 10 errors (pre-existing) | **40 passed** / 10 errors (pre-existing) |

Los 10 errores pre-existentes son todos causados por `PermissionError: [WinError 5]` en el fixture `tmp_path` de pytest en este entorno Windows — no son regresiones de esta tarea.

---

## Archivos modificados

- `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py` — clase MaterialTable, endpoints, UI admin
- `tests/test_panel_sales_local_app.py` — 8 tests nuevos, import de MaterialTable

## Criterios de aceptación

- [x] Sección visible en `/admin` al correr el servidor
- [x] Agregar fila desde formulario persiste en JSON
- [x] Borrar fila con feedback visual
- [x] JSON persiste en `Programas_hechos/Panel Decorativo/material_table.json`
- [x] Tests previos no regresionados (mismo baseline de errores pre-existentes)
- [x] Tests nuevos: 8 tests adicionales, todos pasan
