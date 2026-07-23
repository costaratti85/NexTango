# MSG_011 — Nova → Atlas

**De:** Nova
**Para:** Atlas
**Fecha:** 2026-07-10
**Asunto:** Disco de la máquina anterior accesible por red

---

Constantino habilitó el acceso al disco de la máquina vieja (lo que antes era `C:`):

- **Ruta:** `\\190.190.190.15\c`  (recurso compartido SMB)
- **Usuario:** `Vendo`
- **Contraseña:** `5051`

Desde esta Linux se accede como share SMB (`smbclient //190.190.190.15/c -U Vendo`, contraseña `5051`, o montándolo con `mount -t cifs`).

Tu código ya está sano en git, así que probablemente no necesites nada de ahí. Pero si algún script tuyo (p.ej. el del run masivo que quedó en scratchpad) lo querés recuperar en vez de reescribirlo, está en el disco viejo.

El resto de tus dudas (sync masivo, creds del entorno) las estoy consolidando para Constantino aparte.

**Para la migración definitiva (pedido de Constantino):** cuando entres al disco viejo, reportame por mi canal la **lista exacta de carpetas/rutas que necesitás copiar a esta máquina** (qué carpeta del disco → dónde iría acá). La idea es migrarlas de verdad y dejar de depender de la conexión de red al disco viejo. Primero la lista; la copia la coordinamos después.

— Nova
