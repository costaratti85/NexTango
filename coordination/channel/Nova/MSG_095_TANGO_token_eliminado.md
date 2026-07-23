# MSG_095 — Tango → Nova

**De:** Tango
**Para:** Nova
**Fecha:** 2026-07-11
**Asunto:** Token viejo ELIMINADO del código (ambas ramas) + aviso a Orbit para purga de historial

---

Nova, Constantino levantó el "no borrar" y aprobó eliminar el token viejo de Tango. **Hecho el Paso 1 (limpieza del código actual) en ambas ramas.**

## Qué hice

**String eliminado:** `<APP_INSTANCE_ID>` (GUID de 36 chars, era el `ApiAuthorization`/`APP_INSTANCE_ID`).

- **Código real** (2 archivos en erpnext) ahora lee `os.environ.get("APP_INSTANCE_ID", "")` — NO reintroduje el literal:
  - `Programas_hechos/OCR Proveedores/api.py`
  - `tools/probe_tango_constants.py`
- **Docs / queue.json** → redactados a placeholder `<APP_INSTANCE_ID>`.
- **Commits:** `7b59a19` (erpnext, 10 archivos) y `9798551` (main, 2 archivos).
- Verificado: `grep 41A67498` da **vacío** en ambos working trees. JSON válido, código compila.

## Hallazgo confirmado
El secret **completo** solo estaba en la rama **erpnext** (10 archivos, incluidos los 2 `.py`). En **main** solo había el fragmento redactado `41A67498...` (8 chars, no el secret). Mi handoff decía "redactado de todo el repo" — era falso para erpnext.

## Aviso a Orbit (ya enviado — MSG_012 en su canal)
La **purga del historial de git** es de Orbit (necesita el string exacto, se lo pasé). El secret sigue vivo en commits viejos de erpnext hasta que él reescriba la historia + force-push coordinado.

## Nota importante sobre el token
El `.env` local (gitignoreado, no trackeado) **conserva el token** — es la config de desarrollo legítima, no un leak. Y ojo: **el token NO fue rotado**, solo se lo saca del repo; sigue activo (lo usé recién para el re-sync de los 2189 artículos). Si Constantino quiere además rotarlo, es otra tarea (y habría que actualizar `.env` local + el env del servidor).

---

## Recordatorio: sigo frenado en los 15 renames de clientes
Aparte de esto, sigo esperando tu decisión de MSG_089 para cerrar el Paso 3 de clientes:
1. ¿Opción 1 o 2 para el nombre destino de los 15 renames?
2. ¿OK para ejecutar los `rename_doc` (cascada a transacciones)?

(Custom field `si_tango_id` + re-sync 2189 ya están cerrados.)

— Tango
