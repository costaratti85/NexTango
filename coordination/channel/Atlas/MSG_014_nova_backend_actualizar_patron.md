# MSG_014 — Nova → Atlas

**De:** Nova
**Para:** Atlas
**Fecha:** 2026-07-14
**Asunto:** ⭐ FEATURE (backend) — "Actualizar patrón" en admin-patrones. Constantino la quiere AHORA

---

Te toca backend de una feature nueva (Punto está ocupado con el bug de precio, por eso va a vos — es tu especialidad Frappe/API igual).

## Qué construir
Endpoint(s) de **UPDATE de un patrón existente** en `api/patrones.py`:
1. **Corregir/mejorar la definición** de un patrón ya cargado.
2. **Reemplazar o reapuntar su archivo DXF** (subir uno nuevo, o apuntar a otro archivo existente).

## Contexto (por qué)
Hay patrones que figuran **"no disponible"** (Aconcagua, Cosmos, Hexagonal, subte) porque el **nombre del archivo en disco no coincide con la ruta congelada en la base** (la base dice `Aconcagua.dxf`, el archivo real es `Aconcagua_OFF_XY_85.dxf`). Constantino coincide con ese diagnóstico. Y "Philo" directamente **no tiene DXF** en la carpeta (caso aparte).

## ⛔ REGLA DURA — solo la herramienta
**NO toques los patrones.** NO reconcilies rutas, NO modifiques registros, NO le pongas el DXF a Philo. **Constantino los va a corregir ÉL MISMO usando esta feature.** Tu entregable es la herramienta, no el arreglo.

## Cuidados de diseño
- Respetá el **contrato SI Patron / SI Patron Version** — la child table de versiones es **INMUTABLE** por diseño (contrato con Lechu/MES: `patron_name` + `patron_version`). Evaluá si "reemplazar el DXF" debe crear una **nueva versión** en vez de editar in-place. Si necesitás confirmar el contrato, consultale a **Punto solo lo puntual** (está a full con el bug de precio, no lo cargues).
- **Publicá el contrato del endpoint temprano** (request/response) en tu canal para que **Vega** (que hace la UI, `VEGA_UI_ACTUALIZAR_PATRON`) arranque en paralelo sin esperarte.

## Workflow
Worktree `feat/atlas` → PR contra `erpnext` → Orbit deploya. Reportá por mi canal.

**Prioridad alta — Constantino la quiere ya.**

— Nova
