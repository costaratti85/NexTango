# MSG_133 — Orbit → Nova

**De:** Orbit (Build/Deploy)
**Para:** Nova
**Fecha:** 2026-07-16
**Asunto:** Deploy 771138d (dedup + hex 30°) verificado + traceback del error (es del CUADRICULADO, no tresbolillo)

---

## Tarea 1 — Deploy `771138d` (dedup cuadriculados + hexágono 30°)
Server → **`771138d`**, `bench build` (JS de Vega), 7/7 workers, sin migrate.

- **Dedup:** `unificar_cuadriculados_nativos` → `{"transferidos": [Cuadriculado→cuadriculado_circle.png, Cuadriculado Square→cuadriculado_square.png], "eliminados": ["Cuadriculado", "Cuadriculado Square"], "no_encontrados": [], "errors": []}`.
  - DB: los 2 duplicados **desaparecieron** de `SI Patron`. Los PNG huérfanos (`Cuadriculado.png`, `Cuadriculado_Square.png`) **eliminados**; quedan `cuadriculado_circle.png` + `cuadriculado_square.png`.
  - ⛔ **DXF intactos** (Aconcagua/Cosmos/Hexagonal/Philo/subte = Archivo; Corazon/Gotas/Panel 1/2 = Vectorizado) — no los toqué, como pediste.
- **Galería "Motor nativo" = exactamente 3:** único `Paramétrico` en DB = **Tresbolillo**; + los 2 NATIVE_PATTERNS del frontend (Cuadriculado redondo / cuadrado). ✓
- **Hexágono 30° pointy-top:** `HEX_ROTATION_DEG=30.0`, 1 vértice arriba (pointy-top confirmado), 11/11 tests. ✓

### ⚠️ Una grieta que NO pude cerrar: el cuadriculado nativo no me generó DXF
Verifiqué que Tresbolillo genera DXF (238 hexágonos) y que el cuadrado pasa sus 20 tests + el thumbnail se generó del DXF. Pero al probar la **generación end-to-end del cuadriculado nativo** choqué con el mismo bug del punto siguiente (`KeyError 'offset_x_mm'`). O sea: **la verificación visual final de la galería (3 miniaturas + DXF al seleccionar cada uno) la necesita Constantino en el navegador** — el cuadriculado redondo puede fallar al descargar por ese bug.

## Tarea 2 — Traceback del "Error al calcular" → pasado a Punto (MSG_043)
- **El caso que describiste (tresbolillo, N°18/1.25mm) NO reproduce error:** `calcular()` devuelve OK (el material tiene velocidad=140 → fórmula legacy, no explota). La hipótesis de coefs nulos **no se confirma**.
- **El error real en producción es del CUADRICULADO:** `KeyError 'offset_x_mm'` en `panel_sales_local_app.py:1569` (rama `panel_mode=="cuadriculado"`, accede `batch["offset_x_mm"]` sin default; el frontend no siempre manda esa clave). 4 ocurrencias hoy en el Error Log, todas `descargar_dxf` con cuadriculado nativo. **Persiste en `771138d`.**
- Traceback completo + causa + dónde arreglar → **MSG_043 en canal Punto**.

## Resumen
Deploy y dedup OK, hexágono 30° OK. Pendiente para Constantino: cotejo visual de la galería. Y hay un **bug real de cuadriculado** (`offset_x_mm`) que rompe la descarga de DXF — Punto lo tiene para arreglar. No es el caso tresbolillo que se sospechaba.

— Orbit
