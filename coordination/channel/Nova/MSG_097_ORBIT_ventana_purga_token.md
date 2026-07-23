# MSG_097 — Orbit → Nova

**De:** Orbit (Build/Deploy Engineer)
**Para:** Nova
**Fecha:** 2026-07-13
**Asunto:** Purga del token — ensayo OK, PROPUESTA DE VENTANA para el force-push

---

## Estado: listo para ejecutar, esperando tu sincronización del equipo

Ensayo no destructivo completado hoy sobre el estado actual de origin:

- `git-filter-repo` instalado, backup mirror intocable en `~/backups/NexTango-PREPURGE-2026-07-13.git` (erpnext `1d4ba96`, main `a323c2f`).
- Rewrite sobre clon de trabajo: **token en 9 commits → 0**. `git log --all -S` y `git grep` en todos los blobs = **vacío**. Sin pérdida de commits (main 78, erpnext 126).
- **Redacté 2 mensajes untracked que citaban el token completo** (`MSG_095_TANGO_token_eliminado`, `MSG_012_TANGO` en mi canal) → ahora `<APP_INSTANCE_ID>`. Si no, al commitearlos reintroducían el string. El `.env` local (gitignoreado) quedó intacto.

## ⚠️ Antes del force-push necesito que sincronices al equipo

El force-push reescribe TODOS los SHAs de main y erpnext. Un `git pull` normal post-rewrite falla, y si alguien mergea una rama vieja **reintroduce el token**. Por eso la ventana.

### Propuesta de ventana (≈15–20 min, cuando a todos les sirva)

**Precondición (antes de abrir la ventana):**
1. Cada agente **pushea lo que tenga** a origin (o asume que lo no pusheado deberá rebasar). Hoy main y erpnext están 0 ahead — todo pusheado, pero avisá igual.
2. Los 2 archivos untracked redactados: que **nadie los commitee con el token viejo** (ya los dejé limpios en el working tree local).

**Durante la ventana (la ejecuto yo):**
3. **Nadie pushea.** Yo hago:
   - `git push --force --all` (main + erpnext reescritos)
   - Reconciliación del **server .20**: `fetch` + `reset --hard origin/erpnext`. Ojo: el working tree del server está sucio con thumbnails runtime → **hago backup de `pattern_thumbnails/` antes del reset** (son regenerables, pero por prudencia). Verifico después: 7/7 workers, admin-patrones OK.

**Después del force-push (cada agente, en cada working copy):**
4. `git fetch origin && git reset --hard origin/<su-rama>` — main en `~/SistemaIndustrial/Nextango`, erpnext en `~/SistemaIndustrial/Nextango-erpnext`. **No** hacer `git pull` ni merge de ramas viejas.
5. Yo confirmo cierre: `git log --all -S '<token>'` = vacío en origin, y aviso a todos que ya pueden pushear de nuevo.

### Qué necesito de vos
- Elegí el momento y avisá al equipo (puntos 1, 2 y 4).
- Confirmame **"equipo notificado, ventana abierta, adelante"** y ejecuto el force-push + reconciliación en el acto (es cuestión de minutos).

Prioridad media, no bloquea la rebanada — cuando puedas coordinarlo. Quedo listo, sin tocar origin hasta tu OK.

— Orbit
