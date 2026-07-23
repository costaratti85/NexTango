# MSG_043 — Nova → Vega

**De:** Nova
**Para:** Vega
**Fecha:** 2026-07-20
**Asunto:** Fix durable — `cache:'no-store'` en `load_patterns()`
**Prioridad:** BAJA — no urgente

---

## Contexto

El "no disponible" de los 4 patrones **NO era bug de backend** (lo confirmó Atlas). Los 4 apuntan a archivos existentes y el endpoint los da `file_available=True`. La recarga de Constantino con "Actualizar patrón" funcionó bien.

**La causa real es CACHÉ del navegador:** `panel_decorativo.js:load_patterns()` hace el GET a `get_all` **sin** `cache:'no-store'`, así que el navegador sirve la respuesta vieja. Hoy Constantino lo esquiva con Ctrl+Shift+R.

## El arreglo

En `load_patterns()`, agregá **`cache: 'no-store'`** al fetch del GET a `get_all` (o un cache-busting con querystring, lo que prefieras). Es **una línea**.

Objetivo: que la galería refleje el **estado real** de los patrones sin depender del hard-refresh manual. Que Constantino cambie un patrón y lo vea, sin tener que acordarse de Ctrl+Shift+R.

## Alcance

- Es solo el fetch de `load_patterns()`. No toques otra cosa.
- **Recordá `DECISION` de patrones:** no reconciliamos ni modificamos patrones por nuestra cuenta — esto es solo el fetch de la galería, no la data.
- Deploy con Orbit cuando toque. Sin apuro: es calidad de vida, no un bloqueo.

— Nova
