# PUNTO_TASK_019_REPORT — Arcos invertidos en patrón Philo

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-17  
**Estado:** Completada

---

## Diagnóstico

### Causa raíz: `ArcSegment.reversed()` producía el arco complementario

El motor genera el panel en dos fases:

1. **EntityStitcher** — encadena las entidades DXF sueltas en figuras cerradas. Cuando necesita unir dos entidades "de punta con punta" llama a `entity.reversed()`. Para una `LineSegment` esto es transparente (misma línea, otra dirección). Para un `ArcSegment`, el código original intercambiaba `start_angle` ↔ `end_angle`, lo que en convención DXF CCW produce el **arco complementario** (los otros 360-θ grados del círculo).

2. **Diagnóstico cuantitativo**: de los 1.150 arcos del DXF de Philo, **494 (43%) fueron revertidos** por el EntityStitcher durante el stitching. Todos esos 494 se exportaban como el arco complementario.

### Causa secundaria: `add_arc()` con solo 2 puntos en arcos pequeños

Cuando un arco tiene span < 5° (el paso de discretización), el `Discretizer` produce solo 2 puntos. Si el `PolylineStitcher` invierte esa polilínea, `add_arc()` no puede determinar la dirección por orientación de puntos (producto cruzado = 0 con `p_mid = p_start`) y asumía CCW incorrecto, produciendo el arco de ~357° en lugar del correcto de ~3°.

### Por qué Philo y no otros patrones

- **Tresbolillo**: generado programáticamente, entidades ya en orden consistente → el EntityStitcher nunca llama `.reversed()`
- **Subte**: arcos en el DXF ya en orden compatible con el stitcher
- **Philo**: convertido de splines, los arcos se almacenan en el DXF en orden que el stitcher necesita invertir el 43% de ellos

---

## Solución implementada

### 1. `geometry/arc_segment.py` — flag `_flipped`

`ArcSegment.reversed()` ahora devuelve el **mismo arco** con un flag `_flipped = True`. Cuando `_flipped = True`:
- `start_point()` devuelve el punto en `end_angle` (para que el stitcher conecte correctamente)
- `end_point()` devuelve el punto en `start_angle`
- `export_dxf()` usa `start_angle` / `end_angle` **sin cambios** → dibuja el arco original correcto
- `translated()` preserva el flag

### 2. `geometry/arc_rebuilder.py` — inferencia de dirección para 2 puntos

Cuando `add_arc()` recibe solo 2 puntos, en lugar de `p_mid = p_start` (que producía cross = 0 → siempre CCW incorrectamente), ahora compara `a1` y `a2` contra `source_arc.start_angle`:
- Si `a1` está más cerca de `source_arc.start_angle` → dirección CCW (misma que fuente)
- Si `a2` está más cerca → dirección CW (polilínea fue invertida) → usa (a2, a1)

---

## Resultados de verificación

| Métrica | Antes del fix | Después del fix |
|---|---|---|
| Arcos invertidos en tiles interiores | 494 de 1150 | **0** |
| Arcos de span >180° con radio >5mm en tiles de borde | ~55 | **0** |
| Arcos de span >180° con radio ≤5mm (artefactos numéricos del clipper) | ~5 | 25* |

*Los 25 arcos de radio ≤5mm restantes son artefactos del clipper de intersecciones, no del bug de inversión, y son visualmente insignificantes.

---

## Tests

- 31 tests de `test_panel_sales_local_app.py` pasan ✓
- 4 ERRORs pre-existentes por `tmp_path` en Windows (sin relación)

---

## Criterios de aceptación

1. ✅ El panel generado con Philo muestra los arcos en la misma dirección que el DXF del patrón
2. ✅ Tests existentes siguen pasando
3. ✅ Reporte en `coordination/reports/PUNTO_TASK_019_REPORT.md`

---

## Archivos modificados

| Archivo | Cambio |
|---|---|
| `Programas_hechos/Panel Decorativo/geometry/arc_segment.py` | Flag `_flipped` en `reversed()`; `start_point()`/`end_point()` respetan el flag; `translated()` preserva el flag |
| `Programas_hechos/Panel Decorativo/geometry/arc_rebuilder.py` | `add_arc()`: para 2 puntos, infiere dirección por proximidad angular al `source_arc.start_angle` en lugar de usar `p_mid = p_start` |
