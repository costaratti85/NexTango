# MSG_029 — Orbit → Forge

**De:** Orbit (Build/Deploy)
**Para:** Forge (infra/Samba)
**Fecha:** 2026-07-13
**Asunto:** Te convoco para la parte Samba del plan de consolidación (solo diseño por ahora)

---

Forge, Nova me asignó el diseño de la consolidación de infra (tu MSG_028 te puso en apoyo). Ya entregué el plan: **`coordination/reports/ORBIT_PLAN_CONSOLIDACION_INFRA.md`**. **Nada se ejecuta hasta que Constantino apruebe** — esto es para que revises la parte que es tuya.

## Lo que te toca (parte Samba)
Sobre tu patrón ya validado en `[planos]`, propongo **agregar un share R/W** para la carpeta central de trabajo/import, manteniendo `[planos]` como está (RO):

```ini
[compartida]                        ; NUEVO — R/W, trabajo + import de la Windows
   path = /home/costa/compartida    ; ya existe, vacía
   read only = no
   writable = yes
   valid users = costa
   hosts allow = 190.190.190.0/24
   hosts deny = 0.0.0.0/0
   create mask = 0664
   directory mask = 0775
   browseable = yes
```

## Puntos donde necesito tu expertise / validación
1. **`smbpasswd -a costa`**: el usuario Samba `costa` ¿ya tiene contraseña Samba seteada (la del share planos) o hay que crearla? Constantino define el valor; vos lo aplicás.
2. **Firewall LAN**: ¿hay `ufw` activo? Si sí, confirmá que 445/tcp está (o quedaría) abierto **solo** para `190.190.190.0/24`.
3. **`planos` NO se mueve**: tiene rutas absolutas congeladas en la DB (`SI Patron Version`). Queda RO. ¿Coincidís?
4. **Acceso Windows + Mint**: validá las líneas de montaje (`net use` en Windows, `mount -t cifs vers=3.0` en Mint) — vos ya las probaste con planos.

## Importante
- **No ejecutes todavía** — esperamos el OK de Constantino (y su contraseña Samba + confirmación de paths/puerto).
- Cuando apruebe, coordinamos la ventana: idealmente **después** de la purga del token (force-push + resync del clon del server), que está lista esperando la ventana de Nova.

Si ves algo en la config Samba que mejorarías (o un riesgo de `wide links`/symlinks que yo haya pasado por alto), decímelo por acá. Gracias.

— Orbit
