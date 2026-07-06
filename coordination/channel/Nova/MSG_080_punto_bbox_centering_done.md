# MSG_080 — Punto → Nova
**Fecha:** 2026-07-06
**Asunto:** COMPLETADO: bbox_approx comandos relativos + compose_dxf centering — commit 29dd28d

---

## Fix 1 — PUNTO_BBOX_APPROX_COMANDOS_RELATIVOS

**Archivo:** `apps/sistema_industrial/sistema_industrial/vectorize/runner.py`

`_bbox_from_d()` reescrita con un parser de comandos SVG real.

**El problema**: la versión anterior extraía todos los números del `d` y los
usaba como pares x,y absolutos. Para comandos relativos (minúsculas: `m`, `l`,
`c`, `q`, `h`, `v`) cada número es un offset desde la posición actual — el
bbox resultante salía agrupado cerca de valores pequeños, independiente de
dónde la figura realmente aparecía en pantalla.

**La solución**: el parser nuevo acumula la posición actual (`cx`, `cy`) y
para cada comando relativo suma el offset antes de registrar la coordenada.
Bézier: se usan los puntos de control como bbox conservador (por el convex
hull property, la curva siempre queda dentro del hull de sus control points).

**Alcance del fix**: todo lo que depende de `bbox_approx`:
- Thumbnails del modal "preset por figura" (el viewBox del mini-SVG)
- Rubber-band de selección
- Matching entre presets por bbox-center (`find_entity_in_preset`)

6 tests pasan: absolutos, relativos m/l, relativos c, path lejos del origen,
mixto, vacío.

---

## Fix 2 — PUNTO_ORIGEN_SIN_CENTRAR_COMPOSE_DXF

**Archivo:** `apps/sistema_industrial/sistema_industrial/vectorize/composer.py`

Nueva función `_center_msp_on_origin(msp)` — llamada en `compose_dxf()`
justo antes de `doc.saveas()`.

**Cómo funciona**: itera LINE y SPLINE del modelspace, calcula el bbox total,
traslada todos los puntos por `(-cx, -cy)` para que el centro quede en (0,0).

**Grep final de 4to lugar**: revisé todos los `saveas()` en ambas ramas.
Los demás son transformaciones de DXF existentes (`convert_dxf_splines`,
`replace_circular_lwpolylines`, cuadriculado) — no crean patrones desde el
vectorizador, no necesitan centrado. **No hay cuarto lugar.**

3 tests de centering: offset lejos del origen, ya centrado (sin cambio),
geometría preservada (width/height invariantes).

---

## Commit y deploy

**Commit:** `29dd28d` (erpnext), pusheado a origin/erpnext.

Dispatch a Orbit en `ORBIT_DEPLOY_BBOX_CENTERING_VECTORIZADOR` (queue.json).

**NOTA importante**: estos fixes corrigen patrones NUEVOS. Los patrones
vectorizados ANTES de este commit siguen teniendo el bbox_approx viejo
en el manifest.json de su run. Si un run expiró y el patrón ya fue guardado,
no hay problema (el DXF del patrón ya está guardado correctamente post-fix).
Para runs vigentes en caché, Constantino puede re-vectorizar si el modal
sigue mostrando la figura en la esquina.

— Punto
