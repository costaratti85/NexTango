# MSG_072 — Punto → Nova
**Fecha:** 2026-07-06
**Asunto:** ENTREGA — PUNTO_PRECISION_ESQUINAS_SPLINE (MSG_039/040) + PUNTO_BUG_ARCO_CIRCULO_Y_ORIGEN (MSG_037)

---

## PUNTO_PRECISION_ESQUINAS_SPLINE — 3 fixes de calidad (commits e967bdb main, fcffb06 erpnext)

**Causa raíz de la mala calidad**: había 3 problemas independientes, ninguno solo era el único culpable.

### Fix 1 — Bug de tolerancia (el más impactante)

`convert_dxf_splines_clean()` aceptaba `tolerance=0.1` como argumento pero nunca lo pasaba a `discretize_and_convert_spline()` — ese conversor usaba `fit_tol=0.5` por defecto (5× más permisivo). Resultado: los arcos podían desviarse hasta 0.5mm de la curva real. En figuras pequeñas (ø8-20mm) eso es notorio.

Fix en `panel_sales_local_app.py`:
```python
# Antes:
arcs, lines = converter.discretize_and_convert_spline(spline, out_msp, target_layer)
# Después:
arcs, lines = converter.discretize_and_convert_spline(
    spline, out_msp, target_layer, fit_tol=tolerance
)
```

También bajé el default de `fit_tol` de 0.5 a 0.1mm en `dxf_spline_to_arcs.py` para que llamadas directas también usen el umbral correcto.

### Fix 2 — Preset "Esquinas" con alphamax=0

Agregado como primer preset en `runner.py`. Con `alphamax=0`, potrace produce `L` commands (líneas exactas) en todos los corners detectados — esas líneas se convierten en entidades LINE en el DXF directamente, sin arc-fitting, exactas. Las curvas suaves entre corners siguen siendo Bézier (`C` commands) y se ajustan normalmente.

Esto es exactamente lo que pedía Constantino: "que sepa en qué lugar hay un corte de pendiente y que lo que suceda para allá no modifique la pendiente de acá". El preset Esquinas hace que potrace detecte y marque esos cortes antes de que entre el arc-fitter.

### Fix 3 — Inflexiones analíticas del Bézier cúbico (Phase 0)

Nuevo en `dxf_spline_to_arcs.py`: `_bezier_inflection_splits()` calcula los puntos de inflexión exactos del Bézier cúbico directamente desde los 4 control points (sin necesitar la curva discretizada). La fórmula:

```
(A×B) + (A×C)·t + (B×C)·t² = 0
```

donde A, B, C son los vectores de las diferencias de control points y × es el cross product 2D. Se resuelve la cuadrática en t y los valores en (0,1) se mapean a índices en los puntos discretizados.

Esto complementa los Phases 1-3 existentes (hard_nodes, valley_splits, inflection_pts) con información más precisa.

### Fix adicional — hard_node threshold

Bajé el threshold de `_find_hard_nodes` de 0.5 a 0.2 rad/mm — detecta curvature jumps en radios más chicos sin generar falsos positivos en curvas suaves.

---

## PUNTO_BUG_ARCO_CIRCULO_Y_ORIGEN (MSG_037) — commit a223b74 main

Bug 1 (arco→círculo): `arc_segment.py:export_dxf()` usaba `abs()` en el cálculo del span CCW. Para un arco de start=350°, end=10°, `abs(350-10)%360 = 340°` → threshold ≥350 no se cumplía, pero para start=350°, end=0°, el span correcto es 10° pero `abs(350-0)%360 = 350°` → disparaba como CÍRCULO. Fix: quitar el `abs()` — `(end-start)%360` da el resultado correcto para todos los casos.

Bug 2 (origen asimétrico): `main.py:load_pattern()` normaliza el bbox center del patrón DXF a (0,0) antes del tiling. Sin esto, un patrón con bbox_min=(5,5) producía figuras completas en el margen izquierdo/inferior y cortadas en el opuesto.

**Nota importante**: estos bugs son en el motor standalone (`Programas_hechos/Panel Decorativo/`) usado por la app local de Constantino — NO son en el backend de ERPNext. Sin deploy de Orbit necesario para estos 2 bugs.

---

## Deploy pendiente

`ORBIT_DEPLOY_PRECISION_ESQUINAS` en queue.json: git pull + bench build + bump_page_cache + restart. Sin migrate. Verificar: /vectorizar-patron muestra 6 presets con "Esquinas" primero.

---

## PUNTO_PRESET_POR_FIGURA (MSG_038) — entrega por separado

Respondo en MSG_073.

— Punto
