# MSG_032 — PUNTO → Nova
**Fecha:** 2026-06-30  
**Asunto:** TASK_041 Cuadriculado — implementado

---

## Status: COMPLETADO

TASK_041 (patrón Cuadriculado) implementado completo.

---

## Archivos creados / modificados

| Archivo | Cambio |
|---|---|
| `Programas_hechos/Panel Decorativo/geometry/cuadriculado_pattern.py` | **NUEVO** — `create_cuadriculado_piece(hole_shape, hole_size_mm, offset_x_mm, offset_y_mm)` |
| `Programas_hechos/Panel Decorativo/config/settings.py` | +`hole_shape`, +`hole_size` |
| `Programas_hechos/Panel Decorativo/main.py` | +import cuadriculado, +bloque en `load_pattern()` |
| `apps/.../legacy_panel_adapter.py` | +"cuadriculado" en LEGACY_PATTERN_TYPES, +campos en LegacyPanelRunRequest, +branch en `_build_settings()` |
| `apps/.../panel_service.py` | +campos en LegacyPanelServiceInput, +`legacy_pattern_type_for_panel_mode`, +`normalize_panel_input`, +LegacyPanelService.run() |
| `apps/.../panel_sales_local_app.py` | +card galería, +cuad-inline HTML, +JS cuadShapeChanged/confirmCuadriculado, +buildBatch cuadriculado, +renderBatchTable, +_run_all_batches, +build_sales_input, +_panel_mode_to_preset_code |
| `tests/test_panel_sales_local_app.py` | +4 tests (2 unitarios pasan, 2 con tmp_path bloquean por error de permisos de sistema preexistente) |

---

## Diseño

- **Círculo**: un `ArcSegment(0, 0, radio, 0, 360)` centrado en (0,0)
- **Cuadrado**: 4 `LineSegment` formando un cuadrado centrado en (0,0), lado = `hole_size_mm`
- **Grilla**: `step_x = offset_x_mm`, `step_y = offset_y_mm` (sin factor √3 — grilla recta)
- La UI tiene selector Círculo/Cuadrado que cambia el label "Diámetro mm" / "Lado mm" dinámicamente

## Nota de flow

Para cuadriculado en el path de form único (`build_sales_input`), los offsets van en `offset_x_mm`/`offset_y_mm`. `normalize_panel_input` los mapea a `step_x_mm`/`step_y_mm` antes de pasarlos al adapter.

Para el path multi-batch (`_run_all_batches`), el batch dict tiene `offset_x_mm`/`offset_y_mm` y se settean directamente en `settings.step_x`/`settings.step_y`.

---

— Punto
