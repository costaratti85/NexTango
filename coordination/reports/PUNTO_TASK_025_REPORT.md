# PUNTO_TASK_025_REPORT — Etiqueta DXF: formato abreviado + justificación derecha

**Agente:** Punto  
**Fecha:** 2026-06-18  
**Estado:** COMPLETADO

---

## Cambios implementados

### 1. Justificación del texto: left → right

**Archivo:** `apps/sistema_industrial/sistema_industrial/cutting/dxf_writer.py`

La función `_text_right` ya existía y ya estaba siendo llamada por `write_rectangles_dxf` (implementada en la misma sesión). El cambio produce etiquetas con group codes DXF `72=2` (right) y segundo punto de alineación `11/21`, lo que hace que el texto termine en X=-200 y se extienda hacia la izquierda sin solapar el área de corte.

### 2. Formato abreviado del material

**Archivos modificados:** `apps/sistema_industrial/sistema_industrial/cutting/dxf_batch_compiler.py`

Se agregó:
- Constante `_MATERIAL_TABLE_FILE` apuntando a `Programas_hechos/Panel Decorativo/material_table.json`
- Función privada `_abbreviated_label(material, thickness_mm) -> str` que lee `familia` del JSON y devuelve el formato abreviado:

| Familia | Formato generado |
|---|---|
| `hierro` | `N°{calibre}` — ej: `N°18` |
| `galvanizada` | `Galv N°{calibre}` — ej: `Galv N°18` |
| `inox304` | `Inox 304 {espesor}mm` — ej: `Inox 304 1.25mm` |
| `inox430` | `Inox 430 {espesor}mm` — ej: `Inox 430 1.25mm` |
| No encontrado | `{thickness_mm}mm` (fallback seguro) |

- `_layout_rectangles` acepta ahora `row_label: str | None = None`
- `compile_cut_batch` calcula `row_label = _abbreviated_label(...)` y lo pasa a `_layout_rectangles`

El `row_label` se asigna como `label` a cada `DxfRect`. `write_rectangles_dxf` ya deduplica por Y-row (`labeled_y` set), por lo que solo aparece una etiqueta por fila.

### Estado de material_table.json

El campo `familia` ya existía en todas las entradas: `hierro` (Chapa doble decapada), `galvanizada` (Chapa galvanizada), `inox430` (Inoxidable 430), `inox304` (Inoxidable 304). No fue necesario agregarlo.

---

## Verificación

```
_abbreviated_label('Chapa doble decapada', 1.25) → 'N°18'
_abbreviated_label('Chapa galvanizada', 1.25)    → 'Galv N°18'
_abbreviated_label('Inoxidable 304', 1.25)       → 'Inox 304 1.25mm'
_abbreviated_label('Inoxidable 430', 1.25)       → 'Inox 430 1.25mm'
_abbreviated_label('chapa', 3.0)                 → '3mm'   (fallback)
```

Tests: 20/20 pasan. Los 6 errores restantes son pre-existentes (PermissionError de pytest `tmp_path` en Windows, no relacionados).

---

## Notas de arquitectura

`_abbreviated_label` en `dxf_batch_compiler.py` es una duplicación deliberada de `_format_material_label` en `panel_sales_local_app.py`. Importar desde `panel_sales_local_app` habría creado un acoplamiento circular (módulo HTTP genérico → compilador de corte). La lógica es simple y es mejor duplicarla que crear esa dependencia.
