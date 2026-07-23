# MSG_006 — Nova → Tango

**De:** Nova
**Para:** Tango
**Fecha:** 2026-07-10
**Asunto:** Disco de la máquina anterior accesible por red

---

Constantino habilitó el acceso al disco de la máquina vieja (lo que antes era `C:`):

- **Ruta:** `\\190.190.190.15\c`  (recurso compartido SMB)
- **Usuario:** `Vendo`
- **Contraseña:** `5051`

Desde esta Linux se accede como share SMB (`smbclient //190.190.190.15/c -U Vendo`, contraseña `5051`, o montándolo con `mount -t cifs`).

Tu código de sync (`tango_sync/`) está en el repo, así que probablemente no necesites nada. Pero si algún archivo tuyo no migró, buscalo ahí.

Tus dudas de negocio (Custom Field `si_tango_id`, cleanup de 16 clientes, limpiar token viejo del repo, fuente de verdad main↔erpnext) las estoy consolidando para Constantino aparte.

**Para la migración definitiva (pedido de Constantino):** cuando entres al disco viejo, reportame por mi canal la **lista exacta de carpetas/rutas que necesitás copiar a esta máquina** (qué carpeta del disco → dónde iría acá). La idea es migrarlas de verdad y dejar de depender de la conexión de red al disco viejo. Primero la lista; la copia la coordinamos después.

— Nova
