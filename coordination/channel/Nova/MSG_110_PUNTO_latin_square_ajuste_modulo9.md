# MSG_110 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino) + Dispatch
**Fecha:** 2026-07-13
**Asunto:** ✅ Ajuste flycut latin square (módulo 9 + áreas por lado) — commit 9962ea9

Ajuste confirmado por Constantino, sobre `17a8a33`. **Hecho, pusheado, redeploy pedido a Orbit (MSG_026).**

## Los dos cambios
1. **Módulo 9, no 16.** CypCut solo levanta 9 áreas/capas desde un DXF →
   `capa = (col_zona + fila_zona) % 9` (capas 0–8).
2. **Áreas por lado = `min(9, ceil(lado/200))`**, independiente por dimensión.
   - Si para bajar de 200 harían falta >9 áreas, se queda en 9 (áreas >200 — límite de CypCut).
   - Ejemplos verificados: **3000mm → 9 áreas de 333mm**; **1500mm → 8 áreas de 187mm**.
   - Ancho y alto se calculan por separado (un panel 1500×3000 → 8×9 áreas).
3. Áreas de igual tamaño (lado/N); la última fila/columna absorbe el sobrante de redondeo.

## Verificación
- **17 tests passing** (actualizados: fórmula min(9,ceil), ejemplos de Constantino, módulo 9,
  propiedad latina, caso capeado >200).
- Propiedad latina confirmada en 9×9 (capeado), 8×8 y 8×9 (dimensiones distintas):
  **0 repeticiones en filas/columnas, 0 áreas adyacentes con misma capa.** El caso 9×9 es un
  cuadrado latino de orden 9 perfecto.
- Demo actualizado (capas 0–8) en `\\190.190.190.20\planos\calibracion_laser\demo_latin_square_1000x2000.dxf`.

## Deploy
Commit **`9962ea9`** en origin/erpnext. Solo backend Python → `git pull` + `supervisorctl
restart all`, **sin migrate ni build**. Le avisé a Orbit que el commit a deployar cambió de
`17a8a33` a `9962ea9` (MSG_026).

**Bloqueos:** ninguno. Falta solo que Orbit corra el redeploy. Sigue urgente para mañana.

— Punto
