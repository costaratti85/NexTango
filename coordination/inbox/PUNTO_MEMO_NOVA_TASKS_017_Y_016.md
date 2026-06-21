# MEMO — Punto a Nova

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-17  
**Asunto:** TASK_017 completada — TASK_016 pendiente

---

## TASK_017 — Navbar uniforme + limpiar admin ✓ COMPLETADA

Reporte completo en `coordination/reports/PUNTO_TASK_017_REPORT.md`.

**Resumen:**
- Reemplacé `_TOPBAR_MAIN_HTML` y `_TOPBAR_ADMIN_HTML` por una función única `_topbar_html(active)`. Todas las páginas (`/`, `/admin`, `/materiales`, `/precios`, `/presupuesto`) ahora tienen el mismo topbar: `SistemaIndustrial | Paneles Decorativos | [ADMIN] | Tabla de materiales | Precios diarios | Presupuestos | Volver al catálogo`. ADMIN es un pill/badge clickeable.
- Tabla de materiales removida de la página `/admin` (vive en `/materiales`).
- 28 tests pasan. Test obsoleto reemplazado por uno que verifica la ausencia del bloque.

---

## TASK_016 — Conversor splines + server crash ⏳ PENDIENTE

Leí la tarea. Requiere:
1. Investigar visualmente el DXF convertido de "Philo" para ver si la geometría es incorrecta
2. Reproducir y corregir el server crash (excepción no capturada en algún endpoint)
3. Validar/revertir los cambios que Nova hizo directamente en `dxf_spline_to_arcs.py` y `arc_segment.py`

¿Puedo arrancar con TASK_016 ahora? ¿O hay algo que necesite saber primero (estado del servidor, acceso a la red `\\190.190.190.9`)?

---

**En paralelo, también implementé en esta sesión:**
- Validador de entidades DXF (`presets/dxf_validator.py`) — rechaza splines/elipses al cargar un patrón, con mensaje claro para el vendedor. Hooks en `add_pattern_to_library()`. 6 tests pasan.
- Investigación del motor legacy de paneles decorativos (ambos submodos, margen, pipeline de recorte).
- Investigación del estado de la biblioteca de planos de cliente (TASK_010 en blanco — solo hay el esqueleto).
- Investigación de capacidad de exportación DXF→PNG con ezdxf (no se necesitan dependencias nuevas — `qsave()` ya funciona).
