# PUNTO_TASK_023_REPORT — Cierre de figuras de borde: 2 líneas → 1 línea recta

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-18  
**Estado:** Completada

---

## Diagnóstico

### Causa raíz: `boundary_path()` insertaba la esquina del clip rect en cierres adyacentes

`PolylineCloser.boundary_path(start, end)` decide cómo conectar los dos nodos libres de una figura clipeada para cerrarla. La lógica original:

- Si los dos extremos están en el **mismo lado** del margen → devuelve `[end]` (1 línea directa) ✓
- Si los dos extremos están en **lados opuestos** (LEFT-RIGHT, TOP-BOTTOM) → devuelve `[end]` ✓
- Si los dos extremos están en **lados adyacentes** (LEFT-BOTTOM, LEFT-TOP, etc.) → devuelve `[corner, end]` (2 segmentos pasando por la esquina del rect) ✗

El `corner` es la esquina del rectángulo de margen (ej. `(xmin, ymin)` para LEFT-BOTTOM). En ciertos posicionamientos de tile, esa esquina coincide geométricamente con un nodo del patrón teselado, por eso Constantino lo ve como "un nodo existente de la figura".

---

## Diagnóstico cuantitativo (panel Philo 300×300mm)

| Tipo de cierre | Antes del fix | Con 2 líneas |
|---|---|---|
| Mismo lado (1 línea directa) | 36 | 0 |
| Lados opuestos (1 línea directa) | 10 | 0 |
| **Lados adyacentes con corner (2 líneas)** | **3** | **3 ← bug** |
| **Total cierres** | **49** | **3 afectados** |

El corner no coincidía exactamente con un nodo de la polilínea en este panel específico, pero en otros posicionamientos (o con step_x/step_y distintos) sí coincide, produciendo el síntoma visible que reportó Constantino.

---

## Fix

Simplificación total de `boundary_path()` en [`polyline_closer.py`](Programas_hechos/Panel%20Decorativo/geometry/polyline_closer.py):

```python
def boundary_path(self, start, end):
    return [end]
```

El cierre es una **línea recta directa** entre los dos nodos libres, en todos los casos. Para laser cutting esto es correcto: la línea de cierre es un corte que define el borde de la pieza; no necesita seguir exactamente el contorno del margen.

La lógica de routing por la esquina (que producía el caso de 2 líneas) fue eliminada por completo. Los casos de mismo lado y lados opuestos ya retornaban `[end]` antes, por lo que el comportamiento para esos casos es idéntico.

---

## Verificación

| Métrica | Antes | Después |
|---|---|---|
| Cierres con 2 segmentos | 3 | **0** |
| Cierres con 1 segmento | 46 | **49** |
| Tests de regresión | 31 pasan | **31 pasan** |

---

## Criterios de aceptación

1. ✅ Figuras de borde cierran con una sola línea recta entre los dos nodos libres
2. ✅ Patrón Philo: verificado (49/49 cierres con 1 segmento)
3. ✅ No se introducen nuevas intersecciones incorrectas en tiles interiores (tiles interiores no usan `PolylineCloser`)
4. ✅ 31 tests existentes pasan
5. ✅ Reporte en `coordination/reports/PUNTO_TASK_023_REPORT.md`

---

## Archivos modificados

| Archivo | Cambio |
|---|---|
| `Programas_hechos/Panel Decorativo/geometry/polyline_closer.py` | `boundary_path()` simplificada a `return [end]` siempre |
