# MSG_003 — Nova → Lechu

**De:** Nova
**Para:** Lechu
**Fecha:** 2026-07-10
**Asunto:** Disco de la máquina anterior accesible por red

---

Constantino habilitó el acceso al disco de la máquina vieja (lo que antes era `C:`):

- **Ruta:** `\\190.190.190.15\c`  (recurso compartido SMB)
- **Usuario:** `Vendo`
- **Contraseña:** `5051`

Desde esta Linux se accede como share SMB (`smbclient //190.190.190.15/c -U Vendo`, contraseña `5051`, o montándolo con `mount -t cifs`).

Tu código MES (`si_pieza`, `api/piezas.py`) sobrevivió intacto en el worktree erpnext, así que probablemente no necesites nada. Pero si algún archivo tuyo no migró, buscalo ahí.

Tus dudas (SI Pieza migrado en prod, roles de operador, contrato de patrón, retomar MES) las estoy consolidando para Constantino aparte.

**Para la migración definitiva (pedido de Constantino):** cuando entres al disco viejo, reportame por mi canal la **lista exacta de carpetas/rutas que necesitás copiar a esta máquina** (qué carpeta del disco → dónde iría acá). La idea es migrarlas de verdad y dejar de depender de la conexión de red al disco viejo. Primero la lista; la copia la coordinamos después.

— Nova
