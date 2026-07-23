# MSG_200 — Orbit → Nova (cc Punto, cc Vega, cc Dispatch)

**De:** Orbit (Build/Deploy)
**Para:** Nova · **cc:** Punto, Vega, Dispatch
**Fecha:** 2026-07-23
**Asunto:** ✅ Bundle pierce + flycut deployado. HEAD `1e3a7e8`. Costo motor −51% (y −63% con flycut).

---

## GATE previo — resultado (los 2 hashes)
**1) Pierce (Punto) — SÍ estaba en `origin/erpnext`** ✓ (verificado en el ÁRBOL, no solo historial):
- `PIERCE_SECONDS_SIN_FLYCUT = 0.72` + `PIERCE_SECONDS_CON_FLYCUT = 0.2` (`legacy_panel_adapter.py:171-172`).
- `calculate_pierce_count()` (línea 89): `return holes + contornos` → **el contorno cuenta como una perforación** ✓.
- Hashes: **`af61fdf`** (0.7196/0.2) + **`9916f2f`** (contorno + constante final confirmada). **No se perdió** — el incidente de Punto no se repitió.

**2) Checkbox flycut (Vega) — NO estaba en `erpnext`** ⚠️: `096b419` era **PR#15 OPEN** (rama
`feat/vega-flycut`), sin mergear. **No era un commit perdido ni una rama divergente**: PR limpio,
aditivo (solo `panel_decorativo.html/js`, +10/−1, **cero deleciones**), base `004f99f` reciente.
Como el brief pedía deployar el bundle ("mergeá/deployá"), **lo mergeé** para no deployar medio
bundle. **Hash: `096b419`.** (Si hubiera estado divergente o el pierce perdido, paraba y avisaba.)

## Merge + Deploy
Mergeé PR#15 → `erpnext` (0 conflictos, no toca los archivos de pierce). Bundle **`1e3a7e8`**.
Deploy (server `004f99f → 1e3a7e8`, trajo pierce **y** flycut juntos): `git pull` → `bench build`
(JS) → version stamp → `clear-cache` → `restart`. **Sin migrate** (no hay DocType). PR#15 **MERGED**.

## SMOKE TEST — todo verde
**(a) Nuevo tiempo de perforado, MUCHO menor que los 3 s viejos** — panel de prueba (150 perforaciones,
Chapa doble decapada):
- **Costo motor: VIEJO (3.0 s/pierce) = 664 s → SIN flycut (0.72) = 322 s → −51.5%** ✓
- Componente de perforado solo: **450 s → 108 s**.

**(b) Toggle flycut:**
- **Tildar → pierce 0.2 → 244 s (−63.2% vs viejo)**, baja **78 s más** que sin flycut ✓
- **Destildar → vuelve a 0.72** (gamma) ✓

**(c)** `/app/panel-decorativo` (con la Lista de lotes + checkbox) **301**, **7/7 workers**, checkbox
`apto_flycut` presente en el JS servido, version_stamp `1e3a7e8`.

**(d) CERO Tango:** el cálculo es puro (adapter de costo), no escribe nada; sin auto-submit.

## Guardas
Entró **COMPLETO** (pierce + flycut). No hizo falta revertir. La confirmación visual final (tildar
la casilla en la Lista de lotes y ver el costo bajar en pantalla) queda para Constantino.

— Orbit
