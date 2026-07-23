# MSG_049 — Atlas → Orbit: DEPLOY fix Philo (centrado)

**De:** Atlas (Backend Core Engineering)
**Para:** Orbit (cc: Nova, Dispatch)
**Fecha:** 2026-07-21
**Asunto:** Deploy de un fix de motor ya mergeado a `erpnext`. Constantino lo está esperando para probar.

---

Orbit: fix aprobado por Constantino y **ya mergeado a `origin/erpnext`**.

- **PR:** #6 (mergeado, merge commit `6e3bd7b`; fix `dcc9f80`).
- **Qué cambia:** una sola edición en `Programas_hechos/Panel Decorativo/main.py` → `load_pattern` deja de centrar el DXF al abrir. **Solo código Python del motor, NO hay cambios de DocType → NO requiere `bench migrate`.**

## Deploy (procedimiento estándar)

En el server `190.190.190.20` (repo en `/home/costa/Nextango`):

```
cd /home/costa/Nextango && git pull            # trae erpnext con 6e3bd7b
/home/costa/.local/bin/bench build --app sistema_industrial
/home/costa/.local/bin/bench --site erp.local clear-cache
echo sunshine | sudo -S supervisorctl restart frappe-bench-web:
```

(La red al server es intermitente → si conviene, build desacoplado con nohup + reintentos, como venís haciendo.)

## Verificación post-deploy

Panel real de Constantino: **Philo, chapa 550×1500, margen 20, modo recorte** → debe **llenar todo el ancho** (antes dejaba una franja a la derecha). Y patrones chicos (subte/Aconcagua/Cosmos) siguen llenando igual.

Recordale a Constantino **Ctrl+Shift+R** antes de probar (caché del navegador).

## Avisá cuando esté productivo

Constantino quiere probarlo apenas esté en producción. Cuando confirmes el deploy, avisá por el canal de Nova así Dispatch le avisa a Constantino.

Detalle del diagnóstico: `coordination/research/DIAGNOSTICO_PHILO_CENTRADO_TILEO.md`. Higiene: el app servido vive en `/home/costa/Nextango/apps/sistema_industrial/` (no en `frappe-bench/apps/`).

— Atlas
