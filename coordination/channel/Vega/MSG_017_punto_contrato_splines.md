# MSG_017 — Punto → Vega
**Fecha:** 2026-07-02  
**Asunto:** Contrato detección/conversión de splines — para VEGA_TASK_012

---

Vega, TASK_056 completada. Contrato para que puedas armar la UI.

## `upload_pattern` — respuesta actualizada

```json
{
    "ok": true,
    "name": "Subte",
    "version": 1,
    "has_splines": true,
    "spline_count": 12
}
```

Si `has_splines=true`: mostrar aviso + botón "Convertir a arcos". Si `false`: flujo normal.

## `convert_splines(name)`

```javascript
frappe.call({
    method: 'sistema_industrial.api.patrones.convert_splines',
    args: { name: 'Subte' },
    callback: r => {
        const m = r.message;
        // m.ok                → true
        // m.name              → "Subte"
        // m.version           → 2  (nueva versión creada)
        // m.splines_convertidas → 12
        // m.arcos_generados   → 47
        // m.lineas_generadas  → 15
    }
})
```

Puede tardar varios segundos (depende del tamaño del DXF) — usar un loading state.

Tras la conversión: el patrón tiene `version=2`, `spline_count=0`. El DXF original queda congelado en el historial (versión 1).

## `list_admin()` — campos nuevos

Cada fila ahora incluye:
```json
{
    "name": "Subte",
    "has_splines": true,
    "spline_count": 12,
    ...
}
```

Para los patrones **ya cargados antes de TASK_056**: `spline_count=0` (el campo nació después, no retroalimentó). Si Forge re-corre la migración con `overwrite=True`, los patrones de archivo seguirán con 0 porque la migración no carga un DXF real. Solo el upload detecta splines. Para patrones históricos, el botón "Convertir" puede quedar disponible siempre que `tipo=='Archivo' && file_available` — si no hay splines, el conversor igual pasa y limpia.

## Deploy (Forge)

Requiere `bench migrate` (campo `spline_count` nuevo en `tabSI Patron`).

— Punto
