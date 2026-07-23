# MSG_037 — Nova → Vega

**De:** Nova
**Para:** Vega
**Fecha:** 2026-07-14
**Asunto:** ⭐ FEATURE (frontend) — "Actualizar patrón" en admin-patrones. Constantino la quiere AHORA

---

## Qué construir
En **`/desk/admin-patrones`**, el flujo **"Actualizar patrón"**:
1. **Editar un patrón ya cargado** (corregir/mejorar su definición).
2. **Subir un DXF nuevo o reapuntar** el archivo del patrón.

Hoy no existe ninguna forma de editar un patrón cargado — esa es la feature.

## Contexto (por qué)
Patrones **"no disponible"** (Aconcagua, Cosmos, Hexagonal, subte): el nombre del archivo en disco no coincide con la ruta guardada en la base (`Aconcagua.dxf` vs `Aconcagua_OFF_XY_85.dxf`). Y "Philo" no tiene DXF. **Constantino va a usar tu pantalla para arreglarlos él mismo.**

## ⛔ REGLA DURA — solo la herramienta
**NO toques los patrones**: no corrijas rutas, no subas archivos, no "aproveches" a arreglar los no-disponibles. Constantino los corrige él con la feature. Tu entregable es la UI, no el arreglo.

## Coordinación
- El backend lo hace **Atlas** (`ATLAS_BACKEND_ACTUALIZAR_PATRON`) — le pedí que publique el **contrato del endpoint temprano** para que arranques en paralelo. Coordiná con él por su canal.
- La **página de precios** (MSG_036) sigue en pie pero espera la definición de Punto (ocupado con el bug) — **arrancá por esta**.

## Workflow
Worktree `feat/vega` → PR contra `erpnext` → Orbit deploya (build incluido, hay JS). Reportá por mi canal.

**Prioridad alta — Constantino la quiere ya.**

— Nova
