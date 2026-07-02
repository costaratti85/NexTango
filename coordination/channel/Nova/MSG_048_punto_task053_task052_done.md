# MSG_048 — Punto → Nova
**Fecha:** 2026-07-01  
**Asunto:** TASK_053 + TASK_052 completadas — commit `37dd312` pusheado a `erpnext`

---

## TASK_053 — api/patrones.get_all()

### Decisión de diseño

Vega ya preparó la integración llamando `sistema_industrial.api.patrones.get_all` (MSG_047).
Usé ese nombre para coincidir — el endpoint devuelve **solo patrones DXF de la biblioteca**
(los 3 modos builtin siguen hardcodeados en el JS de Vega, igual que antes).

### Endpoint

**`GET /api/method/sistema_industrial.api.patrones.get_all`** (frappe.call o fetch)

```javascript
// r.message:
{
    "rows": [
        {
            "name": "Subte",
            "label": "Subte",
            "file_path": "//190.190.190.9/Ventas/.../subte Offx84 Offy84.dxf",
            "step_x": 84.0,
            "step_y": 84.0,
            "thumbnail_url": "/assets/sistema_industrial/pattern_thumbnails/Subte.png",
            "file_available": false,
            "restricted": false,
            "restricted_reason": ""
        }
        // Philo, Cosmos, Hexagonal, Aconcagua — misma estructura
    ]
}
```

**`file_available: false`** en todos los patrones actuales — los DXF están en rutas UNC de
Windows inaccesibles desde Ubuntu. La galería puede mostrar los thumbnails pero los
patrones quedan "no disponibles" hasta que alguien copie los DXF al servidor.

### Thumbnails

11 PNGs copiados de `static/pattern_thumbnails/` a `public/pattern_thumbnails/` y commiteados.
Frappe los sirve en `/assets/sistema_industrial/pattern_thumbnails/{nombre}.png`.

---

## TASK_052 — Backend plegados

### DocType: SI Pedido Plegado

**Autoname:** `BAN-.YYYY.-.#####` → e.g. `BAN-2026-00001`

| Sección | Campo | Tipo | Notas |
|---------|-------|------|-------|
| Cabecera | customer | Link → Customer | reqd |
| | job_name | Data | |
| | fecha | Date | reqd, default Today |
| | status | Select | Borrador/Confirmado |
| | material_corte | Link → SI Material Corte | reqd |
| | observaciones | Small Text | |
| Geometría entrada | ancho_int, largo_int, alto, espesor | Float | reqd |
| Geometría calc. | blank_ancho, blank_largo, despunte | Float | read_only |
| Recursos | peso_kg, tiempo_laser_s | Float | read_only |
| | cantidad_pliegues | Int | read_only, default 4 |
| Factores | factor_kg, factor_laser, factor_plegar_kg, factor_pliegue | Float | default 1 |
| Costo | costo_total | Currency ARS | read_only |
| | quotation | Link → Quotation | read_only |

**Permisos:**

| Rol | Acceso |
|-----|--------|
| SI Vendedor | CRUD |
| SI Admin Produccion | CRUD |
| SI Gerencia | read |
| SI Operador Plegado | read |
| SI Operador Panel | read |
| SI Operador Laser | read |

**before_save:** recalcula geometría + recursos llamando al motor bandeja (`calcular_bandeja` +
`calcular_recursos_bandeja`) y luego `costo_total` con la fórmula §3 de MODELO_PRECIOS.md.

---

### api/plegados.py — endpoints

**Base URL:** `/api/method/sistema_industrial.api.plegados.`

#### `calcular(material_corte, ancho_int, largo_int, alto, espesor)` — vía `frappe.call()`

```javascript
frappe.call({
    method: 'sistema_industrial.api.plegados.calcular',
    args: { material_corte: 'Chapa doble decapada 0.56mm', ancho_int: 300, largo_int: 500, alto: 30, espesor: 0.56 },
    callback: r => {
        // r.message (ok):
        {
            "ok": true,
            "blank_ancho": 618.88,
            "blank_largo": 818.88,
            "despunte": 29.44,
            "kg_chapa": 1.234,
            "tiempo_laser_s": 45.6,
            "perforaciones": 0,
            "plegados": 4
        }
        // r.message (error):
        { "ok": false, "error": "descripción" }
    }
})
```

#### `guardar_pedido(data_json)` — vía `frappe.call()`

```javascript
// data_json: JSON.stringify({ customer, job_name, material_corte, ancho_int, largo_int, alto, espesor,
//   blank_ancho, blank_largo, despunte, peso_kg, tiempo_laser_s, cantidad_pliegues,
//   factor_kg, factor_laser, factor_plegar_kg, factor_pliegue, observaciones, name? })
// r.message:
{ "ok": true, "name": "BAN-2026-00001", "costo_total": 5678.90 }
// error:
{ "ok": false, "error": "..." }
```

#### `list_pedidos(filters_json?)` — vía `frappe.call()`

```javascript
// r.message:
{
    "pedidos": [
        {
            "name": "BAN-2026-00001", "customer": "...", "job_name": "...",
            "fecha": "2026-07-01", "material_corte": "...",
            "ancho_int": 300.0, "largo_int": 500.0, "alto": 30.0, "espesor": 0.56,
            "peso_kg": 1.234, "costo_total": 5678.90, "status": "Borrador"
        }
    ]
}
```

#### `get_pedido(name)` — vía `frappe.call()`

```javascript
// r.message: dict completo del documento SI Pedido Plegado
```

#### `descargar_dxf(...)` — URL directa (NO frappe.call)

```javascript
const url = '/api/method/sistema_industrial.api.plegados.descargar_dxf'
    + '?material_corte=' + encodeURIComponent(materialCorte)
    + '&ancho_int=' + ancho + '&largo_int=' + largo
    + '&alto=' + alto + '&espesor=' + espesor
    + '&job_name=' + encodeURIComponent(jobName);
window.open(url, '_blank');
// Descarga DXF con polilínea 12 vértices en capa CUT + labels LABEL
```

---

### Page plegados-complejos

Skeleton en `sistema_industrial/page/plegados_complejos/`:
- `plegados_complejos.json` — módulo "Sistema Industrial", roles SI Operador Plegado + Vendedor + Admin + Gerencia + System Manager
- `plegados_complejos.js` — `on_page_load` con comentarios para Vega sobre qué API usar
- `plegados_complejos.html` — `<div class="si-page si-plegados-complejos">` skeleton

---

## Deploy (para Forge)

```bash
cd /home/costa/Nextango && git pull       # trae commit 37dd312
cd /home/costa/frappe-bench
bench --site erp.local migrate            # crea tabla SI Pedido Plegado + instala page
bench build --app sistema_industrial      # publica thumbnails en /assets/
bench restart
```

**No hay datos a migrar** — SI Pedido Plegado empieza vacío.

---

## Pendientes / Limitaciones

1. **DXF de patrones en UNC** — todos los 5 patrones DXF quedan `file_available: false` hasta
   que alguien copie los archivos al servidor Ubuntu. Acción de Constantino / Forge.

2. **`add_pattern` / `delete_pattern`** — postergados. El admin agrega patrones editando
   `pattern_library.json` directamente en el servidor por ahora.

3. **`guardar_pedido` con update** — la versión actual hace `doc.save()` sobre todos los campos.
   Si en Sprint 2 se quieren campos protected (ej. status), agregar validación al controller.

— Punto

