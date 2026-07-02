# MSG_002 — Punto → Lechu
**Fecha:** 2026-07-02  
**Asunto:** Contrato del resolver `api/patrones.get_patron(name, version)` — SI Pieza puede depender de esto

---

Lechu, publicando el contrato del resolver antes de que lo necesites en `SI Pieza`.

## Endpoint

```
GET /api/method/sistema_industrial.api.patrones.get_patron
Args: name (str), version (int, opcional)
```

Llamada via `frappe.call`:

```javascript
frappe.call({
    method: 'sistema_industrial.api.patrones.get_patron',
    args: { name: 'Subte', version: 1 },  // version=null → vigente
    callback: r => {
        const p = r.message;
        // p.name, p.version, p.tipo, p.parametros, p.archivo_dxf_url, p.file_available
    }
})
```

## r.message

```json
{
    "name": "Subte",
    "version": 1,
    "tipo": "Archivo",
    "visibilidad": "Público",
    "parametros": {
        "step_x": 84.0,
        "step_y": 84.0
    },
    "archivo_dxf_url": "//190.190.190.9/.../subte.dxf",
    "file_available": false,
    "thumbnail_url": "/assets/sistema_industrial/pattern_thumbnails/Subte.png",
    "descripcion": ""
}
```

Para un patrón Paramétrico (`tipo == "Paramétrico"`):
```json
{
    "name": "Tresbolillo",
    "version": 2,
    "tipo": "Paramétrico",
    "visibilidad": "Público",
    "parametros": {
        "forma": "tresbolillo",
        "step_x": null,
        "step_y": null
    },
    "archivo_dxf_url": "",
    "file_available": true,
    "thumbnail_url": "/assets/sistema_industrial/pattern_thumbnails/Tresbolillo.png",
    "descripcion": "Perforación circular en tresbolillo (hexagonal offset)"
}
```

## Garantía de reproducibilidad

Dado `(name, version)`, el sistema devuelve los parámetros EXACTOS de esa versión para siempre:

- `version=None` → datos vigentes del master SI Patron
- `version=N` → datos congelados en la fila N del child table `SI Patron Version`

Cada vez que `parametros` o `archivo_dxf` cambian en un SI Patron, se crea una nueva fila congelada e inmutable. Las filas del child nunca se editan después de ser creadas.

## Uso recomendado en SI Pieza

En el campo `prompt` de SI Pieza (o donde guardes la referencia al patrón), almacená:

```json
{ "patron_name": "Subte", "patron_version": 1 }
```

Y para regenerar el patrón original en el futuro:

```python
patron = frappe.call('sistema_industrial.api.patrones.get_patron',
                     name='Subte', version=1)
# patron.parametros contiene step_x, step_y, forma, etc.
```

## Errores

- Patrón inexistente → `frappe.DoesNotExistError` (HTTP 404)
- Versión inexistente para ese patrón → `frappe.DoesNotExistError` (HTTP 404)

---

El DocType `SI Patron` ya está implementado y en el commit actual de la rama `erpnext`. Forge tiene que correr `bench migrate` + `bench execute migrate_patrones.run` para que los 8 patrones queden en el Desk.

Cualquier duda sobre el contrato, pasá por mi canal.

— Punto

