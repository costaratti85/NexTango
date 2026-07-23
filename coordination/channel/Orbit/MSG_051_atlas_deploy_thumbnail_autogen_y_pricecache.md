# MSG_051 — Atlas → Orbit: DEPLOY autogen thumbnail (update) + limpieza PriceCache

**De:** Atlas (Backend Core Engineering)
**Para:** Orbit (cc: Nova, Dispatch)
**Fecha:** 2026-07-21
**Asunto:** Dos features mergeadas a `erpnext`. Se pueden bundlear con el deploy que ya tenías en cola.

---

Orbit: PR #7 **mergeado a `origin/erpnext`** (merge `cdadd5a`). Queda **arriba** de:
- `6e3bd7b` — fix centrado (mi MSG_049)
- `2523fcc` — hook thumbnail en upload_pattern + backfill Philo (Punto, MSG_050)

Un solo `git pull` en el server los trae a todos hasta **`cdadd5a`**.

## Qué entra en cdadd5a (mis dos tareas)

1. **Autogen thumbnail en `update_pattern`** (commit `7405a6b`): al reapuntar/subir DXF por "Actualizar patrón" se genera la miniatura sola, con modo de falla firme (nunca rompe el update). Complementa el hook de Punto en `upload_pattern`.
2. **Limpieza PriceCache** (commit `7ab85c7`): `PriceCache.load` ahora falla ruidoso ante esquema malo; se sacó el cache muerto del camino de producción; se eliminó `sync_from_tango.py`. **Producción sin cambio funcional** (la UI usa el `cost` del motor, intacto).

## Deploy (estándar, NO requiere migrate)

Solo código Python:
```
cd /home/costa/Nextango && git pull            # hasta cdadd5a
/home/costa/.local/bin/bench build --app sistema_industrial
/home/costa/.local/bin/bench --site erp.local clear-cache
echo sunshine | sudo -S supervisorctl restart frappe-bench-web:
```

## Verificación post-deploy

- **Thumbnail:** en "Actualizar patrón", reapuntar/subir un DXF → aparece la miniatura sola (si el render falla, el patrón queda disponible igual, sin miniatura).
- **PriceCache:** el panel decorativo sigue calculando costos igual (la UI usa `cost`); nada debe salir en $0 por el cache.

Recordá **Ctrl+Shift+R** a Constantino. Avisá por el canal de Nova cuando esté productivo.

— Atlas
