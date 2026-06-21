# VEGA_TASK_004 — Thumbnails en selector "Modo de distribución"

**Estado:** Completado  
**Fecha:** 2026-06-19  
**Agente:** Vega  

---

## Qué se hizo

Se implementó la Opción C (más simple) del MSG_006:

1. **Nuevo endpoint `/static/tools/<filename>`** en `_do_GET_inner()` de `PanelSalesHandler`:
   - Sirve archivos desde `TOOLS_DIR` (ya definido en línea 89)
   - Bloquea traversal (`..` o `/` en el nombre)
   - Devuelve `Content-Type: image/png` o `image/jpeg` según extensión

2. **`<img>` debajo del radio group** (línea ~2219):
   ```html
   <img src="/static/tools/comparacion_modos.png"
        alt="Comparacion modos de distribucion"
        style="max-width:100%;width:480px;border:1px solid #d0dde8;border-radius:6px;display:block">
   ```
   - `width:480px` para formulario de escritorio
   - `max-width:100%` para mobile (no rompe el layout)
   - Border y border-radius coherentes con el resto del form

## Archivos modificados

- `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`
  - Líneas ~4897-4912: nuevo bloque `if parsed.path.startswith("/static/tools/"):`
  - Líneas ~2219-2223: `<img>` dentro de `.form-group` del modo de distribución

## Imagen servida

`tools/comparacion_modos.png` — 150KB, side-by-side generado por `tools/gen_comparison_thumbnails.py`

## No se modificó

- `tools/comparacion_modos.png` — ya existía, no se regeneró
- `tools/gen_comparison_thumbnails.py` — sin cambios
- No se escribieron tests adicionales (endpoint estático simple, sin lógica de negocio)
