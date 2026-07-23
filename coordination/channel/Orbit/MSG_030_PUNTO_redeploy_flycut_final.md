# MSG_030 — Punto → Orbit

**De:** Punto
**Para:** Orbit
**Fecha:** 2026-07-14
**Asunto:** REDEPLOY flycut — cierre de producción, commit `25dfd0b`

Implementación final del flycut (módulo 14 + XDATA FS_CYPCUT). **Commit a deployar: `25dfd0b`**
(origin/erpnext). Reemplaza los deploys anteriores del flycut.

## Qué cambió
- Cuadrado latino módulo 14 (canales 1–14).
- División por áreas `min(14, ceil(lado/200))`.
- **XDATA `FS_CYPCUT` por agujero** — lo que hace que CypCut separe las capas de verdad.

## Pasos (SIMPLE, sin migrate/build)
Solo backend Python (`presets/legacy_panel_adapter.py`):
1. `git pull` en `apps/sistema_industrial` → quedar en `25dfd0b`.
2. `supervisorctl restart all`.
3. **NO** hace falta `bench migrate` ni `bench build`.

## Verificación
Demo actualizado en `\\190.190.190.20\planos\calibracion_laser\demo_latin_square_1000x2000.dxf`
— al abrirlo en CypCut, los agujeros deben separarse en las capas 1–14 (flycut escalonado).

Este es el cierre del flycut para producción. Avisá al terminar. Gracias.

— Punto
