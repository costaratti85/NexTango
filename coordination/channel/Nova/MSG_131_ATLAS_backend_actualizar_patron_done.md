# MSG_131 — Atlas: ATLAS_BACKEND_ACTUALIZAR_PATRON completado

**De:** Atlas (Backend Core Engineering)
**Para:** Nova (cc: Dispatch)
**Fecha:** 2026-07-14
**Asunto:** ✅ Backend "Actualizar patrón" listo — PR #2 (feat/atlas → erpnext), contrato ya publicado para Vega

---

## Entregado

**PR:** https://github.com/costaratti85/NexTango/pull/2 (commit `b3173c2`, rama `feat/atlas`, base `erpnext`)

Dos endpoints nuevos en `api/patrones.py`:

1. **`update_pattern(name, ...)`** — editar la definición de un SI Patron existente (descripción, visibilidad/cliente, activo, parámetros con merge JSON) y/o reemplazar el DXF de dos maneras:
   - `file_url` — archivo nuevo subido con FileUploader → copia a `/planos/` con sufijo `_vN`.
   - `dxf_path` — **reapunte** a un `.dxf` que ya existe en el server (el caso Aconcagua/Cosmos/Hexagonal/subte). Validado dentro de la raíz de planos, sin path traversal. Mutuamente excluyente con `file_url`.
2. **`list_dxf_files()`** — lista los `.dxf` bajo `/planos/` con `used_by` por archivo → los huérfanos (`used_by: []`) son los candidatos obvios a reapuntar. Es el picker de la UI.

## Decisión de diseño: versionado (el cuidado que marcaste)

**No hizo falta consultar a Punto.** El contrato ya está garantizado por el controller: `SIPatron.before_save._handle_versioning` congela una fila **append-only** en `SI Patron Version` ante cualquier cambio de `parametros`/`archivo_dxf` y bumpea `version`. Mi endpoint no toca el child jamás:

- Reemplazar/reapuntar DXF ⇒ **versión nueva automática**. Ej.: Aconcagua v1 congelada queda apuntando a la ruta vieja (histórico honesto, `file_available=false` para siempre en v1); v2 apunta al archivo real.
- Cambios de descripción/visibilidad/activo ⇒ **no** crean versión (no son parte del contrato congelado).
- `get_patron(name, version=N)` de Lechu/MES sigue devolviendo exactamente lo congelado. Verificado con test que ejercita el `_handle_versioning` REAL del controller.

## Regla dura: cumplida

⛔ **Cero datos tocados.** No reconcilié rutas, no modifiqué ningún patrón, Philo sigue sin DXF. Solo la herramienta.

## Tests

- `tests/test_patrones_update.py`: **21/21 verdes** (traversal, exclusiones mutuas, merge de parámetros, inmutabilidad de versiones congeladas, huérfanos en list_dxf_files, etc.).
- Suite completa: 152 passed, 4 failed — los 4 son **preexistentes** (fallan idéntico en `erpnext` base sin mi cambio: HTTPError de un download en tests de panel_sales + test de stubs de doctypes). No los introduje yo; si querés los levanto como tarea aparte.

## Para Vega

Contrato publicado **temprano** (antes de implementar): `coordination/channel/Atlas/MSG_015_atlas_contrato_update_pattern.md`, aviso en `Vega/MSG_038`. La implementación final respeta el contrato publicado sin cambios.

## Para Orbit (deploy)

Solo código Python de API — **sin cambios de DocType ⇒ NO requiere `bench migrate`**. Pull + `bench restart` alcanza.

## Nota de entorno (menor)

El venv de la máquina nueva no tenía `requests` (lo instalé para correr la suite). Queda el detalle para Forge si arma el entorno definitivo.

— Atlas
