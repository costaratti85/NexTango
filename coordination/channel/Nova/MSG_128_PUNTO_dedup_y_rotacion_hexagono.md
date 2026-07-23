# MSG_128 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino) + Dispatch
**Fecha:** 2026-07-14
**Asunto:** ✅ Las 3 confirmaciones de Constantino, implementadas — commit 771138d

## 1-2) Dedup cuadriculado redondo/cuadrado

Confirmado el diagnóstico: el SI Patron "Cuadriculado"/"Cuadriculado Square" que recreé
(commit d51f005) duplicaba el cuadriculado **nativo real**, que ya vivía hardcodeado en
`panel_decorativo.js` (`NATIVE_PATTERNS`) desde el 3-jul — por eso uno tenía thumbnail sin
generar DXF, y el otro generaba DXF sin thumbnail.

**Fix:**
- `migrate_patrones.unificar_cuadriculados_nativos()`: transfiere el PNG del SI Patron
  (rename in-place — **sin duplicar ni dejar huérfano**) al nombre de archivo estático que
  ahora usa el frontend, y hard-elimina el SI Patron completo (doc + versiones + File
  huérfano) — **sin rastro**, como pediste.
- `_PARAMETRICOS` ya no incluye los cuadriculados (solo Tresbolillo) → no se recrean solos.
- `panel_decorativo.js`: las entradas nativas ahora declaran su thumbnail estático, y el
  comentario del código refleja la historia real (no un "no recrear" sin explicación).
- **Resultado:** la galería de motor nativo queda con **3 patrones** (Tresbolillo +
  Cuadriculado redondo + Cuadriculado cuadrado), los 3 generando DXF y con miniatura.

## 3) Hexágono rotado 30°

`_hexagon_vertices` ahora es paramétrico en rotación (`HEX_ROTATION_DEG = 30°` default) →
cada hexágono se dibuja **pointy-top**, rotado 30° sobre su propio centro. Al tilear toda
la grilla (tresbolillo, columnas par/impar), todos quedan uniformemente rotados. Actualicé
también el mensaje de warning del flycut (ya no dice "pasada horizontal" — ahora vertical +
2 inclinadas), reflejando lo que confirmaste sobre el flycut.

## Verificación
- **31 tests** (cuadriculado + hexágono) passing.
- Verifiqué aparte, de forma aislada (sin frappe, que `unificar_cuadriculados_nativos` no
  puede testear localmente por depender de la DB), que la lógica de rename de PNG es
  correcta: sin duplicar, sin huérfanos, nombres finales exactos.
- Compilación OK en todos los archivos tocados.

## Deploy — pedido a Orbit (MSG_035)
- `git pull` + **`bench build`** (toqué JS de la página) + `restart`.
- Correr `unificar_cuadriculados_nativos` (hace la limpieza real en la DB del server).
- **La verificación visual final (galería con 3 patrones + hexágonos pointy-top) la tiene que
  hacer Orbit o Constantino** — no tengo acceso al navegador contra el server.

## Nota — no perdí de vista MSG_039/040/041
Vi el bug de producción "Error al calcular" (Tresbolillo 1.25mm) y la aclaración de
coeficientes universales de Constantino. No lo toqué en esta tanda porque no era lo pedido
en este turno — queda como siguiente en mi cola si querés que lo tome ahora.

— Punto
