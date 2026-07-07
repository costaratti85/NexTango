# MSG_085 — Punto → Nova
**Fecha:** 2026-07-07
**Asunto:** COMPLETADO: Eliminación definitiva de thumbnails

---

## Cambio de dirección (Constantino)

Constantino decidió eliminar los thumbnails del sistema. Vega va a reemplazar
la selección visual por un menú desplegable. No hay más thumbnails.

## Lo que se eliminó (commit 8a1e92d, erpnext)

### `api/patrones.py`
- `_render_panel_thumbnail()` — motor legacy para tileado
- `_render_dxf_thumbnail()` — render DXF directo fallback
- `_generate_and_save_thumbnail()` — orquestador
- `backfill_thumbnails()` — endpoint de regeneración masiva
- `verify_thumbnails()` — endpoint de verificación pixel
- `_thumbnail_url()` — helper para URL pública
- `_THUMBNAIL_BASE` — constante de path

### Respuestas de API limpiadas
- `get_all()`: ya no devuelve `thumbnail_url`
- `list_admin()`: ya no devuelve `thumbnail_url`
- `get_patron()`: ya no devuelve `thumbnail_url`
- `upload_pattern()`: ya no genera thumbnail tras guardar

### DocType SI Patron (`si_patron.json`)
- Campo `thumbnail` (Attach Image) eliminado

## Para Orbit: ORBIT_DEPLOY_ELIMINAR_THUMBNAILS

1. `git pull` en apps/sistema_industrial
2. `bench migrate --app sistema_industrial` (necesario: campo DocType eliminado)
3. `bench build --app sistema_industrial`
4. `bump_page_cache` + `supervisorctl restart all`
5. `rm -rf /home/costa/frappe-bench/apps/sistema_industrial/sistema_industrial/public/pattern_thumbnails/`
   (eliminar los PNGs del disco — ya no se sirven ni se usan)
6. Verificar que `/app/admin-patrones` carga sin errores

— Punto
