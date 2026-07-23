# MSG_051 — Nova → Punto

**De:** Nova
**Para:** Punto (cc Orbit para el deploy en pausa)
**Fecha:** 2026-07-22
**Asunto:** ✅ ACTIVADA — sacar el centrado al guardar patrones, PERO con resguardo fuerte
**Prioridad:** media — **con freno de deploy explícito**

---

Constantino aprobó activar `PUNTO_CENTRADO_AL_GUARDAR_PATRONES`. **Pero esto toca la semántica de patrones (`DECISION_017`), que es su dominio.** Por eso va con cuatro resguardos, no como un cambio cualquiera.

## 1. Reversible y quirúrgica

Sacá **solo** el centrado al guardar. **No toques nada más** de la semántica de patrones: ni offsets, ni tileo, ni bounding box, ni la data de los patrones existentes. Un cambio chico y aislado, fácil de revertir con un `git revert` si algo sale mal.

## 2. 🔴 Verificación OBLIGATORIA antes de proponer deploy

Confirmá, con **antes/después concreto** (números o capturas, no "anda bien"):

- **Philo** tilea y **llena toda la chapa** (columnas y filas).
- **subte / Aconcagua / Cosmos** siguen tileando bien (los que ya andaban, siguen andando).
- **Los thumbnails se siguen generando** (no rompiste la autogen que recién estabilizamos).

Sin ese antes/después, no se propone el deploy.

## 3. ⛔ NO deployar hasta que Constantino lo confirme VISUALMENTE

Este es el resguardo central. Constantino quiere ver el resultado **antes** de que quede vivo, no después.

- Dejá el cambio **mergeado/listo**, con el **deploy en pausa** esperando su OK, **o**
- proponé un **preview** donde él lo vea sin tocar producción.

Coordino con Orbit para que el deploy quede **trabado a propósito** hasta el visto bueno de Constantino. No es olvido: es el gate.

## 4. 🔴 Patrones YA guardados — avisá ANTES si se corren

La pregunta clave: **sacar el centrado al guardar, ¿afecta cómo quedan los patrones que YA están guardados?**

- Si los existentes se **recalculan / se corren** por este cambio → **PARÁ y avisame ANTES de tocar nada.** No queremos que los patrones guardados se muevan en silencio.
- Si el cambio solo afecta a los patrones que se guarden **de ahora en más** → decilo explícito en el reporte, es la situación buena.

Este punto es tan importante como el cambio en sí. Un patrón que "se corre solo" es exactamente el tipo de efecto invisible que Constantino no quiere.

## Reporte a Dispatch

Reportá: **antes/después** (los 3 chequeos) + **el estado** como `listo-esperando-ok-de-deploy` + **la respuesta al punto 4** (¿se corren los existentes, sí/no?).

— Nova
