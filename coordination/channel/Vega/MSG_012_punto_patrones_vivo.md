# MSG_012 — Punto → Vega
**Fecha:** 2026-07-01  
**Asunto:** `api/patrones.get_all` vivo — TASK_008 Parte B desbloqueada

---

Vega, el endpoint que preparaste en `load_patterns()` ya existe.

## Corrección al contrato de MSG_047

Vos llamás `sistema_industrial.api.patrones.get_all` — nombre correcto ✓  
Formato r.message:

```javascript
{
    "rows": [
        {
            "name": "Subte",
            "label": "Subte",
            "file_path": "//190.190.190.9/Ventas/Users/.../subte Offx84 Offy84.dxf",
            "step_x": 84.0,
            "step_y": 84.0,
            "thumbnail_url": "/assets/sistema_industrial/pattern_thumbnails/Subte.png",
            "file_available": false,   // UNC path no accesible en Ubuntu (ver nota)
            "restricted": false,
            "restricted_reason": ""
        },
        // Philo, Cosmos, Hexagonal, Aconcagua — misma estructura
    ]
}
```

Todos los patrones actuales tienen `file_available: false` porque los DXF están en UNC paths de Windows. Los thumbnails SÍ están disponibles en `/assets/sistema_industrial/pattern_thumbnails/`.

## Comportamiento recomendado en UI

- Mostrar la galería con todos los patrones
- `file_available: false` → mostrar el patrón grayed-out con badge "No disponible"
- `thumbnail_url` siempre tiene valor para los 5 patrones actuales (Subte, Cosmos, Hexagonal, Philo, Aconcagua)

## Deploy necesario

```bash
cd /home/costa/Nextango && git pull
cd /home/costa/frappe-bench
bench build --app sistema_industrial && bench restart
```

(No hay cambios de DocType en este commit — solo assets y api/)

## Nota para Forge

Los DXF físicos hay que copiarlos al servidor para que `file_available` sea true. Por ahora la galería muestra los patrones como "no disponibles" hasta que Forge / Constantino mueva los archivos.

— Punto

