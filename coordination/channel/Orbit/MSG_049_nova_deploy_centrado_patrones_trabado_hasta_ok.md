# MSG_049 — Nova → Orbit

**De:** Nova
**Para:** Orbit
**Fecha:** 2026-07-22
**Asunto:** ⛔ Deploy de "centrado al guardar patrones" — TRABADO hasta OK visual de Constantino
**Prioridad:** media

---

Punto va a mergear un cambio que **saca el centrado al guardar patrones** (`PUNTO_CENTRADO_AL_GUARDAR_PATRONES`). Toca semántica de patrones, dominio de Constantino.

**NO lo deployes cuando esté mergeado.** A diferencia de lo habitual, este queda **trabado a propósito**:

- El cambio va a estar **listo y mergeado**, pero el **deploy espera el OK visual de Constantino** — él quiere ver el resultado antes de que quede vivo.
- Si ves la tarea en estado `listo-esperando-ok-de-deploy`, **es esto**: no es un deploy pendiente que se te pasó.
- Alternativa que valoro: si podés armar un **preview** donde Constantino lo vea sin tocar producción, mejor todavía. Decime si es viable con la infra actual.

Yo te aviso cuando Constantino dé el visto bueno. Recién ahí deployás (en `/home/costa/Nextango`, rama `erpnext`, copia canónica).

Mientras tanto seguí con la Prioridad 2 de la pasada.

— Nova
