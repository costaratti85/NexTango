# MSG_015 — Atlas: CONTRATO endpoint "Actualizar patrón" (para Vega)

**De:** Atlas (Backend Core Engineering)
**Para:** Vega (cc: Nova)
**Fecha:** 2026-07-14
**Asunto:** Contrato request/response de `update_pattern` + `list_dxf_files` — publicado temprano para que la UI arranque en paralelo

---

Vega: este es el contrato **estable** de los endpoints backend de `ATLAS_BACKEND_ACTUALIZAR_PATRON`. Podés cablear la UI contra esto ya; si algo cambia durante la implementación te aviso por tu canal, pero la intención es NO cambiarlo.

Base URL: `/api/method/sistema_industrial.api.patrones.`

---

## 1. `update_pattern` — editar definición y/o reemplazar/reapuntar DXF

`POST sistema_industrial.api.patrones.update_pattern`

### Request (todos los campos opcionales salvo `name`; lo que no mandás, no se toca)

| Campo | Tipo | Notas |
|---|---|---|
| `name` | str **requerido** | Nombre del SI Patron existente. |
| `descripcion` | str | Reemplaza la descripción. |
| `visibilidad` | `"Público"` \| `"Exclusivo"` | Si queda `Exclusivo`, hace falta `customer` (nuevo o ya seteado en el doc). |
| `customer` | str | Customer ERPNext. Se limpia solo si visibilidad pasa a `Público`. |
| `step_x` | float \| `""` | `""` limpia el valor (null). |
| `step_y` | float \| `""` | Ídem. |
| `offset_x` | float \| `""` | **ALIAS de `step_x`** (pedido de Constantino 2026-07-14): el "offset X" del patrón ES el paso de tileado — es lo que está encodeado en los nombres de archivo (`subte_Offx84_Offy84.dxf` ↔ `step_x: 84`). Se guarda canónico como `step_x` en `parametros`. ⚠️ No mandar `offset_x` y `step_x` juntos (error). |
| `offset_y` | float \| `""` | Ídem, alias de `step_y`. |
| `parametros` | str JSON | **Merge** de claves sobre el JSON existente (para paramétricos: `forma`, `hole_shape`, `hole_size`, etc.). `step_x`/`step_y` explícitos pisan lo que venga acá. |
| `file_url` | str | **Reemplazar con archivo nuevo**: URL de File Frappe ya subido vía `frappe.ui.FileUploader` (ej. `/private/files/aconcagua.dxf`). El backend lo copia a `/planos/` con sufijo de versión. |
| `dxf_path` | str | **Reapuntar a archivo existente**: path de un `.dxf` que YA está bajo la raíz de planos del servidor (absoluto o relativo a la raíz). No copia nada, solo reapunta. **Mutuamente excluyente con `file_url`.** Usá `list_dxf_files` para el picker. |
| `activo` | 0 \| 1 | Reactivar / baja lógica. |

### Semántica de versionado (contrato con Lechu/MES — INTACTO)

- Si cambia `parametros` o el archivo DXF → el sistema **congela automáticamente una nueva versión** (fila append-only en `SI Patron Version`) y `version` del patrón sube. Las versiones viejas **nunca se modifican**: `get_patron(name, version=N)` sigue devolviendo exactamente lo congelado en N.
- Si solo cambian `descripcion` / `visibilidad` / `customer` / `activo` → **no** se crea versión nueva (esos campos no son parte del contrato congelado).
- Reapuntar el DXF de "Aconcagua" crea v2 apuntando al archivo real; la v1 congelada queda apuntando a la ruta vieja (histórico honesto).

### Response (`r.message`)

```json
{
  "ok": true,
  "name": "Aconcagua",
  "version": 2,
  "previous_version": 1,
  "version_created": true,
  "tipo": "Archivo",
  "visibilidad": "Público",
  "cliente": "",
  "descripcion": "…",
  "activo": 1,
  "parametros": {"step_x": 85.0, "step_y": 85.0},
  "offset_x": 85.0,
  "offset_y": 85.0,
  "archivo_dxf": "/…/planos/generico/patrones/Aconcagua_OFF_XY_85.dxf",
  "file_available": true,
  "spline_count": 0,
  "has_splines": false,
  "thumbnail_url": "/assets/sistema_industrial/pattern_thumbnails/Aconcagua.png"
}
```

- `version_created`: `true` si este update congeló una versión nueva.
- `spline_count`/`has_splines` se recalculan si cambió el DXF.
- El thumbnail se regenera best-effort si cambió el DXF o los steps; si falla, `thumbnail_url` puede venir `null` o viejo (no rompe el update).

### Errores (`frappe.throw` — mensaje en `exc`/`_server_messages`)

| Caso | Error |
|---|---|
| Patrón no existe | `DoesNotExistError` "Patrón 'X' no encontrado" |
| `file_url` y `dxf_path` juntos | ValidationError |
| `dxf_path` inexistente / no `.dxf` / fuera de la raíz de planos | ValidationError |
| Visibilidad `Exclusivo` sin customer | ValidationError |
| `offset_x`+`step_x` juntos (o `offset_y`+`step_y`) | ValidationError "misma propiedad" |
| `file_url`/`dxf_path` sobre patrón tipo `Paramétrico` | ValidationError |
| `parametros` que no parsea como JSON | ValidationError |

---

## 2. `list_dxf_files` — picker para "reapuntar"

`GET sistema_industrial.api.patrones.list_dxf_files`

Sin argumentos. Lista todos los `.dxf` bajo la raíz de planos del servidor.

### Response (`r.message`)

```json
{
  "root": "/…/planos",
  "files": [
    {
      "path": "/…/planos/generico/patrones/Aconcagua_OFF_XY_85.dxf",
      "relpath": "generico/patrones/Aconcagua_OFF_XY_85.dxf",
      "size_kb": 34.2,
      "modified": "2026-07-01 10:22:33",
      "used_by": ["Aconcagua"]
    }
  ]
}
```

- `used_by`: patrones cuyo `archivo_dxf` **vigente** apunta a ese archivo. `[]` = archivo huérfano (candidato típico para reapuntar).
- Ordenado por `relpath` asc.
- Para `update_pattern.dxf_path` podés mandar `path` o `relpath`, ambos valen.

---

## Notas para la UI

- **AGREGADO 2026-07-14 (Constantino):** la pantalla debe permitir en un solo update los TRES campos: **archivo DXF + offset X + offset Y**. Un solo `update_pattern(name, dxf_path=…, offset_x=…, offset_y=…)` congela todo junto en UNA versión nueva. Poné los campos "Offset X (mm)" / "Offset Y (mm)" en el form de edición.
- Flujo "corregir Aconcagua": `list_dxf_files` → usuario elige `Aconcagua_OFF_XY_85.dxf` → `update_pattern(name="Aconcagua", dxf_path=…, offset_x=85, offset_y=85)` → refrescar grilla con `list_admin` (el `file_available` pasa a `true`).
- Flujo "Philo" (sin DXF): subir archivo con `frappe.ui.FileUploader` → `update_pattern(name="Philo", file_url=…)`.
- ⛔ Recordatorio de la regla dura de Nova: la UI NO precarga ni auto-corrige nada — Constantino corrige los patrones él mismo.

— Atlas
