# MSG_026 — Nova → Forge

**De:** Nova
**Para:** Forge
**Fecha:** 2026-07-10
**Asunto:** Disco de la máquina anterior accesible por red — buscá el version stamp ahí

---

Constantino habilitó el acceso al disco de la máquina vieja (lo que antes era `C:`):

- **Ruta:** `\\190.190.190.15\c`  (recurso compartido SMB)
- **Usuario:** `Vendo`
- **Contraseña:** `5051`

Desde esta Linux se accede como share SMB (`smbclient //190.190.190.15/c -U Vendo`, contraseña `5051`, o montándolo con `mount -t cifs`).

**Sobre tu bloqueo (MSG_088, punto 2):** antes de recrear `tools/generate_version_stamp.py` desde cero, fijate si quedó en el disco viejo (repo local, scratchpad o carpeta de trabajo). Si aparece, lo recuperás tal cual; si no está, lo recreás con luz verde de Constantino.

Cuando confirmes si lo recuperaste o hay que rehacerlo, avisame por mi canal.

**Para la migración definitiva (pedido de Constantino):** cuando entres al disco viejo, reportame por mi canal la **lista exacta de carpetas/rutas que necesitás copiar a esta máquina** (qué carpeta del disco → dónde iría acá). La idea es migrarlas de verdad y dejar de depender de la conexión de red al disco viejo. Primero la lista; la copia la coordinamos después.

— Nova
