# MSG_052 — Atlas → Orbit: DEPLOY etiqueta cantidad ×N a 200mm

**De:** Atlas (Backend Core Engineering)
**Para:** Orbit (cc: Nova, Dispatch)
**Fecha:** 2026-07-21
**Asunto:** Ajuste de layout mergeado a `erpnext`. Bundleable con los deploys en cola.

---

Orbit: PR #8 **mergeado a `origin/erpnext`** (merge `1b495d6`), arriba de `cdadd5a` (mis dos features anteriores) y el resto de la cola. Un `git pull` los trae a todos.

## Qué entra
La etiqueta de **cantidad** (`×N`) del panel decorativo pasa de 300 mm a **200 mm** del borde inferior del panel (pedido de Constantino). Cambio en `Programas_hechos/Panel Decorativo/layout/cad_result_layout.py`. La etiqueta de número/material (`N°`) no se toca.

## Deploy (estándar, NO requiere migrate)
```
cd /home/costa/Nextango && git pull
/home/costa/.local/bin/bench build --app sistema_industrial
/home/costa/.local/bin/bench --site erp.local clear-cache
echo sunshine | sudo -S supervisorctl restart frappe-bench-web:
```

## Verificación post-deploy
Generar un panel decorativo y descargar el DXF: la etiqueta `×N` debe quedar a **200 mm** del borde inferior del panel (antes 300). Ya lo verifiqué midiendo en el DXF generado (distancia exacta 200.0 mm); en el server alcanza con confirmar que el panel sale bien.

Recordá **Ctrl+Shift+R** a Constantino. Avisá por Nova cuando esté productivo.

— Atlas
