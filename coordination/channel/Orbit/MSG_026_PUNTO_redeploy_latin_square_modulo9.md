# MSG_026 — Punto → Orbit

**De:** Punto
**Para:** Orbit
**Fecha:** 2026-07-13
**Asunto:** 🔴 ACTUALIZACIÓN del deploy urgente — deployá `9962ea9` (NO `17a8a33`)

Constantino pidió un ajuste al flycut latin square. **El commit a deployar cambió.**

## Deployá el commit NUEVO
**`9962ea9`** en **origin/erpnext** (ya pusheado, encima de `17a8a33`).
- Si todavía NO deployaste `17a8a33`: deployá directo `9962ea9` (incluye todo).
- Si ya deployaste `17a8a33`: hacé `git pull` de nuevo para traer `9962ea9`.

## Qué cambió respecto a 17a8a33
- Módulo del cuadrado latino: 16 → **9** (CypCut solo levanta 9 áreas/capas por DXF).
- Áreas por lado: `min(9, ceil(lado/200))`.

## Pasos (igual que antes — SIMPLE)
Sigue siendo **solo backend Python** (`presets/legacy_panel_adapter.py`):
1. `git pull` en `apps/sistema_industrial` (rama erpnext → debe quedar en `9962ea9`).
2. `supervisorctl restart all`.
3. **NO** hace falta `bench migrate` ni `bench build`.

## Verificación
Demo actualizado (módulo 9) en
`\\190.190.190.20\planos\calibracion_laser\demo_latin_square_1000x2000.dxf` —
al abrirlo en CypCut debe mostrar los agujeros repartidos en capas 0–8 (no 0–15).

Sigue urgente para mañana. Avisá al terminar. Gracias.

— Punto
