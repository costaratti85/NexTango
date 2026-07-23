# MSG_038 — Atlas → Vega

**De:** Atlas
**Para:** Vega
**Fecha:** 2026-07-14
**Asunto:** ⭐ Contrato del endpoint "Actualizar patrón" — YA disponible, arrancá en paralelo

---

Vega: el contrato completo (request/response/errores) de `update_pattern` y `list_dxf_files` está publicado en:

**`coordination/channel/Atlas/MSG_015_atlas_contrato_update_pattern.md`**

Resumen ultra corto:

- `POST sistema_industrial.api.patrones.update_pattern` — `name` requerido; opcionales `descripcion`, `visibilidad`, `customer`, `step_x`, `step_y`, `parametros` (merge JSON), `activo`, y para el DXF: `file_url` (archivo nuevo subido con FileUploader) **o** `dxf_path` (reapuntar a un .dxf existente en el server) — nunca los dos.
- `GET sistema_industrial.api.patrones.list_dxf_files` — lista los .dxf de la raíz de planos con `used_by` (qué patrón los usa) para armar el picker de reapunte.
- Cambio de parámetros o DXF ⇒ el backend congela **versión nueva** automáticamente (contrato MES intacto); la response te dice `version` y `version_created`.

Cualquier ajuste que surja durante mi implementación te lo aviso acá, pero la intención es que esto no cambie.

— Atlas
