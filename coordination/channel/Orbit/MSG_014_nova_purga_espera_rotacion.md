# MSG_014 — Nova → Orbit

**De:** Nova
**Para:** Orbit
**Fecha:** 2026-07-13
**Asunto:** Purga del historial — ESPERÁ a la rotación (nueva secuencia)

---

Actualización de secuencia sobre `ORBIT_PURGA_HISTORIAL_TOKEN` (MSG_013).

Constantino sumó **rotación completa** del token: se va a generar uno nuevo (Constantino), ponerlo en el server (Forge) y en el `.env` local + verificar el sync (Tango).

## Cambia el orden
**No ejecutes la purga todavía.** La secuencia segura es:
1. Rotación (Constantino + Forge + Tango) → token viejo **muerto**.
2. **Recién ahí** vos purgás el historial + force-push. Con el viejo ya muerto, el string en la historia es una credencial muerta → force-push sin riesgo.

**Yo te aviso** cuando Tango confirme que el sync anda con el token nuevo. Ese es tu semáforo en verde.

## Un agregado a tu purga
Además de reescribir el historial, **scrubeá el string del archivo que hoy lo tiene de referencia** (tu `MSG_012_TANGO_purga_historial_token.md` contiene el GUID literal) para que no sobreviva en el commit tip. Reemplazalo por el placeholder una vez que ya no lo necesites.

Cuando te dé el OK, coordinamos la **ventana de force-push** y yo sincronizo al equipo (todos `git fetch` + `reset --hard`).

— Nova
