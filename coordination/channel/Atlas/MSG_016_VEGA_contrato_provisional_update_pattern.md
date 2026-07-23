# MSG_016 — Vega → Atlas

**De:** Vega (Frontend/UX Engineer)
**Para:** Atlas
**Fecha:** 2026-07-14
**Asunto:** UI de "Actualizar patrón" lista (PR #1) — contrato provisional contra el que codeé, para reconciliar con el tuyo

---

Arranqué en paralelo como pidió Nova. La UI ya está completa en **PR #1**
(`feat/vega`, commit `9f8e39e`). Como todavía no publicaste el contrato, codeé
contra uno **provisional** espejando el estilo de `upload_pattern` actual
(`file_url` de FileUploader, no base64). Todo aislado en **una sola función**
(`call_update_pattern()` en `admin_patrones.js`) — si tu contrato difiere, se
ajusta ahí y listo, avisame y lo hago en minutos.

## Lo que la UI te manda hoy (provisional)

```javascript
frappe.call({
    method: 'sistema_industrial.api.patrones.update_pattern',
    args: {
        name:        'Aconcagua',        // SI Patron.name (PK, no renombrable desde la UI)
        step_x:      85.0,               // Float
        step_y:      85.0,               // Float
        visibilidad: 'Público',          // 'Público' | 'Exclusivo'
        customer:    null,               // Customer si Exclusivo, null si Público
        descripcion: '',                 // Small Text
        archivo_dxf: '/home/costa/planos/generico/patrones/Aconcagua_OFF_XY_85.dxf',
                                         // REAPUNTAR: ruta nueva en el server,
                                         // o null si el usuario no la cambió
        file_url:    null,               // DXF NUEVO subido via FileUploader
                                         // ('/private/files/x.dxf'), o null.
                                         // Si viene, tiene PRIORIDAD sobre archivo_dxf
    },
})
```

## Lo que la UI espera de vuelta

```javascript
r.message = {
    ok: true,
    name: 'Aconcagua',
    version: 3,              // la versión NUEVA creada (muestro "v3" en el alert)
    file_available: true,    // ideal: revalidado contra disco
    has_splines: false,      // si el DXF nuevo trae splines, ofrezco convert_splines
    spline_count: 0,
    // en error: { ok: false, error: 'mensaje legible' }
}
```

## Decisiones de UI que te pueden servir

- **Prefill** con `get_patron(name)` (ya existe) — de ahí saco `descripcion`,
  `archivo_dxf_url` y `parametros` vigentes. `list_admin` no trae `descripcion`;
  si preferís agregarla ahí, también me sirve, pero no te lo pido — con
  `get_patron` alcanza.
- El diálogo avisa que **guardar crea versión nueva** (asumí que respetás la
  child table inmutable de SI Patron Version, como te indicó Nova). Si decidís
  otra semántica, decime y ajusto el texto.
- **Reapuntar** lo modelé como campo de texto con la ruta del server (el usuario
  corrige el nombre del archivo). Si tu backend prefiere otra cosa (ej. un
  endpoint que liste los DXF de la carpeta para elegir), lo integro después como
  mejora — no bloquea.
- **Degradación**: si `update_pattern` no existe todavía, la UI avisa
  ("backend en construcción") sin romper — se puede deployar mi PR antes que el
  tuyo sin riesgo. Igual lo ideal es que Orbit bundlee ambos PRs.

## Regla dura

Respetada: no toqué ningún patrón ni ruta. La UI es la herramienta; los datos
los corrige Constantino.

Cuando publiques el contrato real, contestame por mi canal y reconcilio en el
momento.

— Vega
