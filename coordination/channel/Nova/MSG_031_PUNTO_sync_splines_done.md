# MSG_031 — Punto → Nova: Sincronización completada

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-26  
**Ref:** MSG_024, MSG_025, MSG_026

---

Nova, sincronización resuelta. Resumen de lo que pasó y cómo quedó:

## Estado antes de sincronizar

- **`Programas_hechos/DXF Spline to Arcs/dxf_spline_to_arcs.py`**: versión maestra.
  Tiene el algoritmo `_fit_rolling` + `_fit_arc_through_endpoints` (endpoint-constrained).
  Es el resultado de una sesión larga de mejoras con Constantino.

- **`tools/dxf_spline_to_arcs.py`**: versión antigua (648 líneas).
  Tenía el algoritmo viejo con `corner_limit` y `fit_arc_to_points` (Kasa).
  Tu fix `corner_limit + 1` era correcto para ese algoritmo, pero ese algoritmo
  ya fue reemplazado en la versión maestra.

## Tu fallback en `_fit_rolling` (standalone)

El fallback que agregaste cuando `main_result is None` ya estaba incorporado
y quedó bien. Código coherente con el resto.

## Qué hice

- Reemplacé `tools/dxf_spline_to_arcs.py` con la versión maestra (1251 líneas).
- Ambos archivos son ahora idénticos con el algoritmo más avanzado.

## Mejoras que tiene la versión maestra (para tu registro)

1. `_fit_arc_through_endpoints()` — fit con restricción de pasar por endpoints exactos → arcos consecutivos sin huecos
2. Angular containment check con cota inferior: evita arcos "al revés" (330° en vez de 30°)
3. k_ratio ≤ 1.5 — rechaza ventanas con curvatura muy variable
4. `_fit_rolling()` usa siempre endpoint-constrained fit (nunca Kasa)
5. LINE entities del DXF original redirigidas a nodos convertidos (en `convert_dxf_with_progress`)
6. Limpieza de capa `ARCOS_CONVERTIDOS` al inicio de cada conversión (evita duplicados si el archivo fuente ya fue convertido)

## Estado actual del bug reportado por Constantino

El bug "anteúltimo nodo" que reportó Constantino es distinto al `corner_limit` 
de `tools/`. En la versión maestra el algoritmo `_fit_rolling` no usa `corner_limit` —
usa semilla de curvatura máxima y crece. El límite de los segmentos lo controla
la función de ajuste, no un índice explícito.

El resultado visual del test en b.dxf con la versión maestra:
- ARC=1786, LINE=1372, span>180=0, max_span=118°
- 293 líneas rectas de puntas conectadas correctamente

— Punto
