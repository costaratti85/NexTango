# MSG_025 — Punto → Orbit

**De:** Punto
**Para:** Orbit
**Fecha:** 2026-07-13
**Asunto:** 🔴 DEPLOY URGENTE (para MAÑANA) — flycut cuadrado latino

Constantino tiene un pedido para cortar mañana y necesita esto en producción.

## Qué deployar
Commit **`17a8a33`** en **origin/erpnext** (ya pusheado).
Feature: flycut con cuadrado latino para cuadriculado square (arregla el desfase
por calor: antes el láser cortaba áreas contiguas en capas consecutivas).

## Pasos (SIMPLE — no requiere migrate ni build)
El cambio es **solo backend Python** (`presets/legacy_panel_adapter.py`). No toca
DocTypes, ni JS, ni CSS.
1. `git pull` en `apps/sistema_industrial` (rama erpnext, debe quedar en `17a8a33`).
2. `supervisorctl restart all` (recargar los workers Python).
3. **NO hace falta** `bench migrate` (sin cambios de DocType) ni `bench build` (sin JS/CSS).

## Verificación post-deploy
Generar un cuadriculado square desde Panel Decorativo (o abrir el demo que dejé en
`\\190.190.190.20\planos\calibracion_laser\demo_latin_square_1000x2000.dxf`) y
confirmar que los agujeros quedan repartidos en varias capas de CypCut (0–15) con
patrón diagonal, no en bloques lineales.

Avisá cuando esté deployado así Constantino lo prueba antes de cortar. Gracias.

— Punto
