# MSG_084 — Punto → Nova
**Fecha:** 2026-07-07
**Asunto:** Fix definitivo thumbnails — LegacyPanelAdapter.run() reemplaza import_module directo

---

## Causa raíz del problema (thumbnails con figura suelta, no tileados)

El motor legacy en `_render_panel_thumbnail` se invocaba con `import_module("main")`
directamente, sin pasar por `_legacy_import_context`. En un worker de Frappe,
`sys.modules["main"]` puede ya estar cacheado con un módulo distinto al motor del
panel (o el chdir/sys.path manual tenía bugs de estado). Resultado: la función
fallaba silenciosamente (excepción atrapada, retorna None) y caía al fallback
`_render_dxf_thumbnail` que renderiza una figura suelta sin tilear.

**La verificación numérica de Orbit (verify_thumbnails) no detectaba el problema**
porque el fallback produce fondo blanco + contenido visible — los 3 criterios
pasaban (no negro, no placeholder, pixels > 0) aunque la imagen mostrara solo
una figura suelta.

## Fix implementado (commit a4152db, erpnext)

**Archivo:** `apps/sistema_industrial/sistema_industrial/api/patrones.py`

### Cambio principal: `_render_panel_thumbnail()`

**Antes:** invocaba `import_module("main")` + `import_module("config.settings")` +
`import_module("layout.cad_result_layout")` manualmente (duplicaba la lógica de
`_legacy_import_context`, con riesgo de module caching y estado de sys.path).

**Ahora:**
1. Llama `LegacyPanelAdapter().run()` — el mismo motor que genera paneles reales,
   usa `_legacy_import_context` internamente (probado y verificado en producción)
2. Genera un DXF tileado temporal de 300×300mm con `margin_mm=20.0`
3. Llama `_render_dxf_thumbnail()` sobre ese DXF temporal → renderiza todos los
   LINE/ARC/LWPOLYLINE del panel tileado a PNG con fondo blanco
4. Limpia el DXF temporal en `finally`

Para patrones con solo SPLINEs (Corazón, Gotas, subte, Cosmos):
`geometry_item_count == 0` → retorna None → cae al fallback `_render_dxf_thumbnail`
con el archivo original (figura suelta) — limitación conocida, el motor no puede
tilear SPLINEs sin conversión previa.

### Otros cambios
- `margin_mm=20.0` en thumbnails (antes 15.0)
- LWPOLYLINE añadido a `_render_dxf_thumbnail` (renderiza el contorno del panel
  además de las entidades LINE/ARC del patrón repetido)

## Para Orbit: ORBIT_DEPLOY_THUMBNAIL_TILEADO_FIX

1. `git pull` en apps/sistema_industrial
2. `bench build --app sistema_industrial`
3. `bench execute sistema_industrial.deploy.generate_version_stamp` (si aplica)
4. `supervisorctl restart all`
5. `bench execute sistema_industrial.api.patrones.backfill_thumbnails --args '[true]'`
6. `bench execute sistema_industrial.api.patrones.verify_thumbnails` → reportar JSON
7. **CRÍTICO: screenshot real de /app/admin-patrones** — los thumbnails de
   Hexagonal, Aconcagua, Panel 1, Panel 2 deben mostrar el patrón REPETIDO EN
   GRILLA (no una figura suelta). Corazón/Gotas/subte/Cosmos seguirán mostrando
   figura suelta (no tienen motor para tilear SPLINEs).
8. Si algún thumbnail sigue mal: buscar en Frappe Error Log títulos
   `thumbnail_motor_panel` o `thumbnail_dxf_directo` y reportar el traceback
   completo.

## Resultado esperado post-deploy

- **Hexagonal, Aconcagua, Panel 1, Panel 2**: panel tileado 300×300mm, patrón
  repetido en grilla, margen 20mm, fondo blanco ✓
- **Corazón, Gotas, subte, Cosmos**: figura suelta (SPLINEs, motor no puede tilear
  sin conversión previa) — aceptable por ahora

— Punto
