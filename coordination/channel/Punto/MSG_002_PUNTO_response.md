# MSG_002_PUNTO_response

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-17  
**Re:** Check-in — estado y preguntas

---

## Estado actual

Las tres tareas de la sesión de hoy están completas:

| Tarea | Estado | Reporte |
|---|---|---|
| TASK_016 — Conversor splines + server crash | ✓ | `coordination/reports/PUNTO_TASK_016_REPORT.md` |
| TASK_017 — Navbar uniforme + limpiar admin | ✓ | `coordination/reports/PUNTO_TASK_017_REPORT.md` |
| TASK_018 — Resultado y presupuestos | ✓ | `coordination/reports/PUNTO_TASK_018_REPORT.md` |

También tienen reporte de sesiones anteriores: TASK_008 a TASK_015.

---

## Observación sobre el inbox

Hay 7 tareas en `coordination/inbox/` sin reporte correspondiente:

- `PUNTO_TASK_001_PRESET_DXF_OUTPUT.md`
- `PUNTO_TASK_001_UI_PANEL_REDESIGN.md`
- `PUNTO_TASK_002_PANEL_DXF_CONTRACT.md`
- `PUNTO_TASK_002_UI_DXF_CORRECTION.md`
- `PUNTO_TASK_003_GALLERY_THUMBNAILS.md`
- `PUNTO_TASK_004_DEUDA_TECNICA_THUMBNAILS.md`
- `PUNTO_TASK_005_FIX_ARC_DIRECTION.md`
- `PUNTO_TASK_006_MATERIAL_TABLE_SCREEN.md`
- `PUNTO_TASK_007_RESTRICTED_DXF_MODE.md`

Entiendo que fueron completadas antes de que existiera el sistema de reportes (pre-commit 8deb2fd / 822d49f). Pero no lo confirmé. ¿Las puedo dar por cerradas o necesitás que revise alguna?

---

## Preguntas

1. **Tests con `tmp_path`**: cuatro tests en `test_panel_sales_local_app.py` tienen ERRORs por `PermissionError: [WinError 5]` en `C:\Users\vendo\AppData\Local\Temp\pytest-of-vendo`. Es un problema de permisos del directorio temporal de pytest en Windows, pre-existente. ¿Querés que lo resuelva o lo dejamos así?

2. **Spline CONVERTER en la app**: el conversor DXF (TASK_016 / TASK_015) funciona pero el resultado solo se puede cargar manualmente. ¿Hay algún flujo de "cargar DXF convertido directamente desde el conversor" que esté pendiente?

---

## Bloqueos

Ninguno. Listo para recibir próximas tareas.
