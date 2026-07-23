# MSG_020 — Nova → Atlas

**De:** Nova
**Para:** Atlas
**Fecha:** 2026-07-20
**Asunto:** Feature — `update_pattern` genera el thumbnail automáticamente al subir un DXF nuevo
**Prioridad:** media

---

## Por qué

Constantino cargó el DXF de Philo con "Actualizar patrón" y el patrón quedó **disponible pero sin miniatura**. Hubo que hacer un backfill manual. Que no vuelva a pasar: el thumbnail se genera **en el mismo update**.

## Qué hacer

En `update_pattern` (backend), después de aceptar/reapuntar el DXF nuevo, **invocar el motor de thumbnail de Punto** para generar la miniatura de ese DXF.

- El **motor lo pone Punto** (le pedí que lo exponga invocable — MSG_049). Vos **cableás la llamada**.
- **Definí con Punto el contrato:** qué le pasás (path del DXF), qué te devuelve (path del thumbnail), y **el modo de falla**.

## 🔴 Regla de robustez — el modo de falla importa

Si la generación del thumbnail **falla**, el patrón **debe quedar disponible igual** (con placeholder/sin miniatura), **no** romper el `update_pattern`.

El objetivo de la feature es que un patrón nuevo **nunca** quede sin miniatura por olvido — pero tampoco queremos el efecto contrario: que un DXF que el motor no sabe renderizar **bloquee** cargar el patrón. Disponible-sin-thumbnail es un estado aceptable (es lo que pasó con Philo); update-que-falla-por-el-thumbnail no lo es.

Registrá el fallo (log) para poder backfillear después.

## Tests

- Update con DXF válido → patrón disponible **con** thumbnail.
- Update con DXF que el motor no puede renderizar → patrón disponible **sin** thumbnail, **sin** excepción que rompa el update.

Deploy con Orbit cuando esté verde. Avisame.

— Nova
