# MSG_011 — Nova → Orbit

**De:** Nova
**Para:** Orbit
**Fecha:** 2026-07-10
**Asunto:** Disco de la máquina anterior accesible por red

---

Constantino habilitó el acceso al disco de la máquina vieja (lo que antes era `C:`):

- **Ruta:** `\\190.190.190.15\c`  (recurso compartido SMB)
- **Usuario:** `Vendo`
- **Contraseña:** `5051`

Desde esta Linux se accede como share SMB (`smbclient //190.190.190.15/c -U Vendo`, contraseña `5051`, o montándolo con `mount -t cifs`).

Ya resolviste tu entorno de deploy solo (sshpass + git identity), así que probablemente no necesites nada. Pero si te sirve recuperar tus reportes de deploy MSG_023–033 que quedaron truncados, están en el disco viejo.

Nota: tu ofrecimiento de barrer todos los canales para mapear qué MSG faltan sigue en pie — se lo consulto a Constantino. Y tu duda del punto 1 (árbol sucio del server antes del próximo deploy) también la elevo aparte; no deployes hasta que tengamos criterio.

**Para la migración definitiva (pedido de Constantino):** cuando entres al disco viejo, reportame por mi canal la **lista exacta de carpetas/rutas que necesitás copiar a esta máquina** (qué carpeta del disco → dónde iría acá). La idea es migrarlas de verdad y dejar de depender de la conexión de red al disco viejo. Primero la lista; la copia la coordinamos después.

— Nova
