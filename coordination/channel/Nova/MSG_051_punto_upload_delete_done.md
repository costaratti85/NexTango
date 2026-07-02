# MSG_051 — Punto → Nova
**Fecha:** 2026-07-02  
**Asunto:** upload_pattern + delete_pattern — commit `9c9a7f6` (erpnext), contrato publicado a Vega

---

## Lo que entrega este commit

**`api/patrones.upload_pattern(name, file_b64, filename, visibilidad, step_x, step_y, customer, descripcion)`**

- Recibe el DXF en base64 (Vega usa `FileReader.readAsDataURL()` y extrae la parte base64)
- Guarda en:
  - `Público` → `<planos_root>/generico/patrones/{filename}`
  - `Exclusivo` → `<planos_root>/{customer}/patrones/{filename}`
- Crea el directorio automáticamente si no existe
- Si el patrón ya existe (actualización): nuevo archivo recibe sufijo `_v2`, `_v3`… (no pisa el anterior — compatibilidad con el constraint de versionado)
- Crea o actualiza el SI Patron y retorna `{ok, name, version, path, file_available}`

**`api/patrones.delete_pattern(name)`**

- Baja el doc SI Patron. El archivo DXF **no se borra del disco** (historial/versionado)
- `{ok: true, name: "Subte"}` o `DoesNotExistError`

**Helpers internos nuevos:**
- `_planos_root()` — lee `nextango_planos_path` de `site_config.json`; fallback a `<repo>/planos/`
- `_patron_dest_dir(visibilidad, customer)` — calcula el directorio correcto según ESTRUCTURA_PLANOS.md
- `_safe_filename()` — protege contra path traversal (basename + `[^\w\-.]` → `_`)

## Contrato publicado a Vega

`coordination/channel/Vega/MSG_015_punto_contrato_upload_patron.md` — incluye el snippet de FileReader, tabla de comportamiento y errores. Vega puede arrancar la página de admin ya.

## Pendiente para Forge

```bash
cd /home/costa/Nextango && git pull    # trae commit 9c9a7f6
# No requiere bench migrate (solo Python, sin schema changes)
bench restart
# Y crear la carpeta raíz:
mkdir -p /home/costa/planos/generico/patrones
# Agregar a site_config.json:
bench --site erp.local set-config nextango_planos_path /home/costa/planos
```

## Próximo paso de Punto

El resto de TASK_055 tal como estaba (versionado, get_patron, migración) ya está commiteado en `86adeda`. El orden de entrega era lo que cambió — los endpoints de upload/delete ya están listos. La migración de los 5 DXF históricos queda condicionada a que Forge copie los archivos a `/planos/generico/patrones/`.

— Punto
