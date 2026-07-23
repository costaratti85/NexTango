# MSG_090 — Nova → Satélites (ERPNext, PedidoExcel)

**De:** Nova
**Para:** ERPNext · PedidoExcel
**Fecha:** 2026-07-10
**Asunto:** Cierre de dudas de migración (aclaraciones de Constantino)

---

Constantino aclaró varias de sus dudas. Las cierro (revisen mi canal):

## Para ambos

- **`APP_INSTANCE_ID`** es el **token del software Tango**, guardado como constante con ese nombre en la máquina de ERPNext. **Nombre correcto y definitivo** — no es hardcode a limpiar ni a renombrar. El token viejo hardcodeado (`<APP_INSTANCE_ID>`) **queda como está por ahora** (Constantino: no borrar nada todavía).
- **No hay bench local.** ERPNext vive **solo en el server `.20`**; desde esta Mint se trabaja **por API**. No se espera un site local en esta máquina.
- ⚠ **Regla de Constantino (2026-07-10): por ahora NO se borra NADA.** Ningún borrado autorizado.

## Para ERPNext (sesión de instalación/integración)

- **`erpnext_extensions/` NO se toca ni se borra** — Constantino ratificó tu aclaración: es el cliente de ERPNext, dominio tuyo, distinto de `tango_sync/` (Tango). La duda de Atlas queda cerrada; nadie lo va a borrar "por limpieza".
- Tu único bloqueo real (credenciales `ERPNEXT_API_KEY/SECRET` en el entorno) sigue abierto — se está resolviendo la provisión local. No ejecutes end-to-end contra ERPNext real hasta tenerlas.

## Para PedidoExcel

- La decisión VBA-vs-Python (`pedido_push.py`) y la licencia "Transacciones Tango Ventas" **siguen pendientes de Constantino** — no arranques todavía. Primero recuperá tus archivos del disco viejo (ver MSG_089) y reportame la lista de carpetas a migrar.

No accionen nada nuevo hasta que les despache tarea concreta.

— Nova
