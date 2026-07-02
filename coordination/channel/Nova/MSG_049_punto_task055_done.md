# MSG_049 — Punto → Nova
**Fecha:** 2026-07-02  
**Asunto:** TASK_055 completada — commit `86adeda` pusheado a `erpnext`

---

## Decisión de versionado

**Opción (a) elegida: child table `SI Patron Version`.**

Cada fila del child es una snapshot inmutable `(version_num, parametros_frozen, archivo_dxf_frozen, fecha_congela)`. El master siempre tiene los datos de la versión vigente. `before_save` compara contra la última fila del child — si `parametros` o `archivo_dxf` cambiaron, congela el nuevo estado como una fila nueva e incrementa `version`.

---

## DocType `SI Patron`

**Autoname:** `prompt` (el usuario nombra el patrón)

| Campo | Tipo | Notas |
|-------|------|-------|
| tipo | Select | Paramétrico / Archivo |
| visibilidad | Select | Público / Exclusivo |
| version | Int, read_only | autoincremental por before_save |
| cliente | Link → Customer | visible/reqd solo si visibilidad=Exclusivo |
| descripcion | Small Text | |
| archivo_dxf | Attach | visible solo si tipo=Archivo |
| parametros | Long Text (JSON) | step_x, step_y, forma, etc. |
| thumbnail | Attach Image | |
| versiones | Table → SI Patron Version | sección colapsable |

**Permisos:** SI Admin Produccion (CRUD), todos los demás SI roles (read).

### `SI Patron Version` (istable)

| Campo | Tipo |
|-------|------|
| version_num | Int, read_only |
| fecha_congela | Datetime, read_only |
| parametros_frozen | Long Text, read_only |
| archivo_dxf_frozen | Data, read_only |

---

## Contrato del resolver `get_patron(name, version=None)`

Ya publicado a Lechu en `coordination/channel/Lechu/MSG_002`.

```javascript
frappe.call({
    method: 'sistema_industrial.api.patrones.get_patron',
    args: { name: 'Subte', version: 1 },  // version=null → vigente
    callback: r => {
        // r.message:
        {
            "name": "Subte",
            "version": 1,
            "tipo": "Archivo",
            "visibilidad": "Público",
            "parametros": { "step_x": 84.0, "step_y": 84.0 },
            "archivo_dxf_url": "//190.190.190.9/.../subte.dxf",
            "file_available": false,
            "thumbnail_url": "/assets/sistema_industrial/pattern_thumbnails/Subte.png",
            "descripcion": ""
        }
    }
})
```

Errores: `frappe.DoesNotExistError` si patrón o versión no existen.

---

## `api/patrones.get_all(customer=None)` actualizado

- Sin customer → solo Públicos
- Con customer → Públicos + Exclusivos de ese cliente
- Fallback a `legacy_json` si SI Patron está vacío (pre-migración)
- Mantiene compatibilidad con el contrato de Vega (MSG_047): mismos campos de siempre + agrega `tipo`, `visibilidad`, `version`, `parametros`
- `source: "frappe"` o `source: "legacy_json"` en la respuesta

---

## Migración

`migrate/migrate_patrones.py`:

```bash
bench --site erp.local execute sistema_industrial.migrate.migrate_patrones.run
# Esperado: {"inserted": 8, "updated": 0, "skipped": 0, "errors": []}

# Para reimportar:
bench --site erp.local execute sistema_industrial.migrate.migrate_patrones.run \
    --kwargs '{"overwrite": true}'
```

**Qué migra:**
| Patrón | Tipo | Notas |
|--------|------|-------|
| Tresbolillo | Paramétrico | forma=tresbolillo |
| Cuadriculado | Paramétrico | forma=cuadriculado |
| Cuadriculado Square | Paramétrico | forma=cuadriculado_square |
| Subte | Archivo | file_path desde pattern_library.json (UNC) |
| Philo | Archivo | file_path desde pattern_library.json (local Windows) |
| Cosmos | Archivo | file_path desde pattern_library.json (UNC) |
| Hexagonal | Archivo | file_path desde pattern_library.json (UNC) |
| Aconcagua | Archivo | file_path desde pattern_library.json (UNC) |

Los 5 Archivo tendrán `file_available=false` hasta que los DXF se copien al servidor.

---

## Deploy para Forge

```bash
cd /home/costa/Nextango && git pull      # trae commit 86adeda
cd /home/costa/frappe-bench
bench --site erp.local migrate           # crea tablas SI Patron + SI Patron Version
bench restart

# Migrar los 8 patrones:
bench --site erp.local execute sistema_industrial.migrate.migrate_patrones.run
```

---

## Pendientes / Limitaciones

1. **`thumbnail` en la migración:** los PNG ya están en `/assets/sistema_industrial/pattern_thumbnails/` pero no se sube via Frappe File — el campo `thumbnail` queda vacío y `get_all()` usa el fallback por filename (`_thumbnail_url()`). Para subirlos: admin adjunta manualmente en el Desk cada SI Patron.

2. **Patrones Paramétricos — `step_x/step_y`:** quedan en `null` en la migración porque el motor los determina en runtime según el tamaño del panel. En Sprint 2, cuando SI Pieza necesite parámetros concretos, agregarlos al JSON de cada patrón.

3. **`add_pattern` / `delete_pattern`:** el admin gestiona SI Patron directamente desde el Desk (create/edit/delete). No necesitan endpoint API.

— Punto

