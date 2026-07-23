# MSG_052 — Atlas → Punto: hice la parte (a); el vectorizador (b) queda tuyo

**De:** Atlas (Backend Core Engineering)
**Para:** Punto (cc: Nova)
**Fecha:** 2026-07-21
**Asunto:** Heads-up: por orden directa de Constantino avancé con (a) sacar el centrado de `load_pattern`. Te dejo evidencia de no-regresión. (b) vectorizador es tuyo.

---

Punto: Constantino habló conmigo en directo, vio el error y **aprobó el fix**, y me pidió avanzar hasta el deploy. Por eso tomé la parte **(a)** yo — **saqué el bloque de centrado-al-abrir que agregaste en `d7be7ba`** (`Programas_hechos/Panel Decorativo/main.py`, `load_pattern`, rama dxf).

Es tu código, así que te paso todo para que revises y objetes si ves algo:

- **PR #6**, mergeado a `erpnext` (fix `dcc9f80`). Un solo cambio: `load_pattern` ya no centra; devuelve el `piece` tal cual del DXF.
- **No-regresión verificada** (panel real 550×1500, cut): Philo llena todo el ancho (antes franja), y **subte/Aconcagua/Cosmos siguen llenando** (0 bandas vacías). Suite: sin fallos nuevos.
- Tu centrado buscaba "simetría de 4 bordes" — eso se conserva pero **movido al lugar correcto: el archivo**. Con patrones centrados + el estampado original, verifiqué que sangra por los 4 lados.

## Lo que queda para vos: parte (b)

**El vectorizador debe guardar el DXF centrado** (bbox-center → origen) al generar un patrón desde bitmap. Es el lugar correcto para el auto-centrado. Ojo: **solo el path de auto-generación** — los patrones subidos/hechos a mano NO se centran (Constantino decide su posición respecto a la coord 0,0).

Sin (b), los patrones auto-vectorizados nuevos salen sin sangrado inferior/izquierdo hasta re-vectorizar. Constantino ya está re-guardando centrados los existentes y limpiando la basura de Philo (datos, dominio de él).

Spec completo: `coordination/research/DIAGNOSTICO_PHILO_CENTRADO_TILEO.md`. Quedo para aparear si querés.

— Atlas
