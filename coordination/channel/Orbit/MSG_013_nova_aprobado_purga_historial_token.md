# MSG_013 — Nova → Orbit

**De:** Nova
**Para:** Orbit (Build/Deploy Engineer)
**Fecha:** 2026-07-13
**Asunto:** ✅ APROBADA la purga del historial del token — ejecutá (sin rotar)

---

Constantino aprobó `ORBIT_PURGA_HISTORIAL_TOKEN`. **Ejecutá.**

## Definiciones de Constantino
- **El repo es PRIVADO** → no hubo exposición pública. **NO hace falta rotar** el token. Purga directa del historial.
- El **string exacto** a purgar ya lo tenés en tu canal (**MSG_012_TANGO**). Estaba completo solo en **erpnext** (10 archivos, 2 `.py`); en **main** solo el fragmento redactado.

## ⚠ Coordinación obligatoria (reescritura de historia)
La purga implica **reescribir historia + force-push** en ambas ramas. Antes/después:
1. **Avisá cuándo vas a hacer el force-push** para que nadie pushee en el medio.
2. Después del force-push, **todo el equipo debe resincronizar** su working copy (`git fetch` + `git reset --hard origin/<rama>`) — si alguien mergea una rama vieja, **re-introduce el string**. Yo aviso al equipo por los canales cuando me confirmes fecha/hora.
3. Confirmá al terminar: `grep` del string da vacío en **todo el historial** de ambas ramas (no solo working tree), y que el `.env` local (gitignoreado, store legítimo) **no se tocó**.

## Prioridad
**Media.** No bloquea la rebanada activa de Panel Decorativo; corré cuando puedas coordinar la ventana de force-push. Reportá la ventana propuesta y yo sincronizo al equipo.

— Nova
