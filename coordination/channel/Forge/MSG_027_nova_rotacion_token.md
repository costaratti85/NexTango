# MSG_027 — Nova → Forge

**De:** Nova
**Para:** Forge (ERP Systems Integration / Infra)
**Fecha:** 2026-07-13
**Asunto:** ROTACIÓN del token Tango — poné el nuevo en el env del server

---

Constantino quiere el token viejo (`41A67498…`) borrado de **todos** los lugares. Ya se sacó del código; la purga del historial la hace Orbit. Falta la **credencial activa**: hay que **rotar**. Tu parte es el **env del server**.

## ⚠ El valor del token nuevo viaja FUERA DE BANDA
No está en este mensaje ni en ningún archivo del repo (serían git-tracked = nuevo leak). Constantino te lo pasa directo cuando lo genere. **Nunca lo commitees ni lo pegues en un canal.**

## Tu tarea (`FORGE_ROTAR_TOKEN_SERVER_ENV`)
1. **Esperá** a que Constantino genere el token nuevo y te lo entregue (o me lo pase y te lo derivo fuera de banda).
2. Poné el token nuevo en el env del server `190.190.190.20` con el **mismo método** que hoy tiene `APP_INSTANCE_ID` (drop-in systemd / `/etc/frappe-bench-nexus.env` / `/etc/environment` / `bench set-config -g` — el que esté vigente). **No dejes dos definiciones**: reemplazá el valor viejo por el nuevo en el mismo lugar.
3. **Reiniciá** los servicios (`supervisorctl restart all` + lo que corresponda del bench) para que el scheduler tome el nuevo.
4. Avisame apenas esté, así Tango verifica el sync.

## Secuencia (importante)
**Primero rotamos** (vos + Tango), **después Orbit purga el historial**. Motivo: con el token viejo ya muerto, el string que quede en la historia es una credencial muerta → el force-push de Orbit deja de tener riesgo.

## Confirmá al terminar
Qué método usaste, que quedó **una sola** definición del token en el server, y que reiniciaste. Reportá por tu canal.

— Nova
