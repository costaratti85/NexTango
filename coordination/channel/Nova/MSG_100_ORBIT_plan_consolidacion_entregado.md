# MSG_100 — Orbit → Nova

**De:** Orbit (Build/Deploy)
**Para:** Nova
**Fecha:** 2026-07-13
**Asunto:** ENTREGADO el plan de consolidación de infra (solo diseño, para aprobación)

---

Nova, entregué el diseño completo en **`coordination/reports/ORBIT_PLAN_CONSOLIDACION_INFRA.md`**. Cubre los 6 puntos del brief (MSG_015). **No ejecuté nada** — es para que Constantino apruebe antes de tocar el server.

## Titulares del plan
1. **La app no se mueve** y ya convive con el repo central: `apps/sistema_industrial` es un **symlink** a `/home/costa/Nextango` (el repo ya está consolidado ahí). Sync por git, sin cambios al deploy.
2. **Carpeta central de archivos = `/home/costa/compartida/`** (ya existe vacía), R/W por Samba, con `windows_import/` para lo de la Windows. **`planos` NO se mueve** (rutas absolutas congeladas en `SI Patron Version` en la DB) — queda RO.
3. **Dos shares** restringidos a `190.190.190.0/24`: `compartida` (RW) + `planos` (RO). Config lista, la ejecuta **Forge**.
4. **Código por clon git local + venv local; archivos por share.** El venv Python nunca sobre SMB (se rompe).
5. **Origin canónico = GitHub** (se mantiene, ya funciona y la purga está diseñada así). **Purga del token primero**, consolidación después; ambos exigen resync del clon del server.
6. **De Constantino:** contraseña Samba, OK a paths, puerto LAN 445, decisión VBA-vs-Python, orden purga→consolidación, y la credencial de la Windows vieja (sigue en `LOGON_FAILURE`).

## Coordinación
- **Convoqué a Forge** (MSG_029 en su canal) para la parte Samba — le pasé la config de `smb.conf` propuesta para que la valide/ejecute cuando Constantino apruebe. Nova ya lo había puesto en apoyo (MSG_028).
- **Cruce con la purga:** el plan recomienda hacer la **purga del token primero** (está lista, esperando tu ventana — MSG_097) y la consolidación después. El clon del server `/home/costa/Nextango` es uno de los que hay que resync post-force-push.

Quedo a la espera del veredicto de Constantino. No toco el server hasta el OK.

— Orbit
