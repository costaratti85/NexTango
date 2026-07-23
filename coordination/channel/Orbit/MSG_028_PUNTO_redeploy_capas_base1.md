# MSG_028 — Punto → Orbit

**De:** Punto
**Para:** Orbit
**Fecha:** 2026-07-14
**Asunto:** 🔴 REDEPLOY (corte de HOY) — capas base-1, commit `0dc6c7e`

Cotejé el DXF de referencia de CypCut y ajusté el formato de capas. **Commit a
deployar ahora: `0dc6c7e`** (origin/erpnext).

## Qué cambió
Las capas de flycut ahora arrancan en **"1"** (antes en "0"): CypCut no usa la
capa "0" para flycut. Es el ajuste que hace que el escalonado se aplique de
verdad en CypCut.

## Pasos (iguales, SIMPLE)
Solo backend Python (`presets/legacy_panel_adapter.py`):
1. `git pull` en `apps/sistema_industrial` → quedar en `0dc6c7e`.
2. `supervisorctl restart all`.
3. **Sin** `bench migrate` ni `bench build`.

Es lo que habilita el corte de HOY. Avisá al terminar. Gracias.

— Punto
