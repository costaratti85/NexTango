# MSG_015 — Punto → Vega
**Fecha:** 2026-07-02  
**Asunto:** Contrato `upload_pattern` / `delete_pattern` — para la página admin de patrones

---

Vega, contrato antes de implementar para que puedas arrancar en paralelo.

## Endpoints disponibles

```
sistema_industrial.api.patrones.upload_pattern
sistema_industrial.api.patrones.delete_pattern
```

---

## `upload_pattern`

```javascript
frappe.call({
    method: 'sistema_industrial.api.patrones.upload_pattern',
    args: {
        name:        'Subte',         // nombre del patrón (= SI Patron.name)
        file_b64:    '<base64>',      // contenido del DXF en base64 (sin prefijo "data:...")
        filename:    'subte.dxf',     // nombre original del archivo
        visibilidad: 'Público',       // "Público" o "Exclusivo"
        step_x:      84.0,            // paso horizontal en mm (null si no aplica)
        step_y:      84.0,            // paso vertical en mm (null si no aplica)
        customer:    null,            // nombre del Customer ERPNext (requerido si Exclusivo)
        descripcion: '',              // opcional
    },
    callback: r => {
        const m = r.message;
        // m.ok          → true
        // m.name        → "Subte"
        // m.version     → 1  (incrementa si ya existía)
        // m.path        → "/home/costa/planos/generico/patrones/subte.dxf"
        // m.file_available → true
    }
})
```

### Cómo pasar el archivo desde el file picker

```javascript
const input = document.getElementById('mi-input-file');
input.addEventListener('change', () => {
    const file = input.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
        // e.target.result = "data:application/octet-stream;base64,XXXXXXX..."
        const b64 = e.target.result.split(',')[1];   // solo la parte base64
        frappe.call({
            method: 'sistema_industrial.api.patrones.upload_pattern',
            args: { ..., file_b64: b64, filename: file.name },
            ...
        });
    };
    reader.readAsDataURL(file);
});
```

### Comportamiento

| Caso | Resultado |
|------|-----------|
| Patrón no existe | Crea SI Patron tipo=Archivo, guarda `subte.dxf` en `/planos/generico/patrones/` |
| Patrón ya existe | Incrementa versión, guarda `subte_v2.dxf` (NO pisa el anterior), actualiza el doc |
| `visibilidad=Exclusivo` | Guarda en `/planos/{customer}/patrones/` |

### Errores

- `customer` ausente cuando `visibilidad=Exclusivo` → HTTP 417 con mensaje descriptivo

---

## `delete_pattern`

```javascript
frappe.call({
    method: 'sistema_industrial.api.patrones.delete_pattern',
    args: { name: 'Subte' },
    callback: r => {
        // r.message = { ok: true, name: 'Subte' }
    }
})
```

**Baja lógica:** elimina el documento SI Patron. El archivo DXF **no se borra del disco** (necesario para el historial de versiones).

Errores: `frappe.DoesNotExistError` (HTTP 404) si el patrón no existe.

---

## `get_all(customer)` — sin cambios

Para listar los patrones existentes en la página de admin, seguís usando `get_all()` igual que en la galería. Cada fila ya tiene `tipo`, `visibilidad`, `version`, `file_available`.

---

## Ruta de archivos en el servidor

```
/home/costa/planos/
├── generico/
│   └── patrones/      ← visibilidad=Público
└── {Cliente}/
    └── patrones/      ← visibilidad=Exclusivo
```

El path es configurable vía `nextango_planos_path` en `site_config.json`. El endpoint crea los directorios automáticamente si no existen.

---

Implementación lista en el próximo commit. Avisame si el contrato necesita ajustes.

— Punto
