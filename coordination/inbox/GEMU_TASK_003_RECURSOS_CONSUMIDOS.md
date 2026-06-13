# GEMU_TASK_001 — Cálculo de recursos consumidos por panel

**Asignado a:** Gemu  
**Fecha:** 2026-06-13  
**Prioridad:** Alta  
**Criterio de aceptación:** Dado un resultado del motor, se puede obtener metros lineales de corte, cantidad de perforaciones, y metros cuadrados de chapa. Con errores < 5% respecto a cálculo manual en un caso de referencia.

---

## Contexto del sistema

El motor legacy (`Programas_hechos/Panel Decorativo/`) genera geometría real para cada panel. La función central es `create_cad_result_items_from_batch(settings)` que devuelve una lista de `CADResultItem`.

Cada `CADResultItem` tiene:
- `geometry_items`: lista de objetos de geometría (`Piece`, `Polyline`)
- `occupied_width`, `occupied_height`: dimensiones del panel en mm
- `quantity`: cantidad de paneles
- `cut_length_mm`: **actualmente hardcodeado en 0** — esto es lo que hay que calcular
- `pierce_count`: **actualmente hardcodeado o incompleto** — revisar

Cada `Piece` tiene `.entities`: lista de `ArcSegment` o `LineSegment`.
- `ArcSegment`: `cx, cy, radius, start_angle, end_angle` (ángulos en grados)
- `LineSegment`: `x1, y1, x2, y2`

---

## Lo que hay que construir

### 1. Función `calculate_cut_length_mm(geometry_items) -> float`

En `apps/sistema_industrial/sistema_industrial/presets/legacy_panel_adapter.py` (o módulo nuevo).

Recorre todos los objetos de geometría y suma:
- Por `LineSegment`: `sqrt((x2-x1)² + (y2-y1)²)`
- Por `ArcSegment`: `radius × |end_angle - start_angle| × π/180`
- Por `Polyline`: suma de segmentos consecutivos entre puntos

**Nota sobre el contorno del panel**: la `Polyline` que representa el rectángulo exterior (el corte del panel) también cuenta como corte. Incluirla.

### 2. Función `calculate_pierce_count(geometry_items) -> int`

Cuenta cuántas `Piece` existen en los geometry_items. Cada `Piece` es una figura independiente = una perforación.

**Aclaración de Constantino**: las perforaciones del interior del panel (figuras completas) son las que importan para el consumo de consumibles en plasma. Las figuras del borde ya perforadas a medias también cuentan como perforaciones.

### 3. Función `calculate_sheet_area_m2(width_mm, height_mm) -> float`

Simple: `(width_mm * height_mm) / 1_000_000`

### 4. Integración en el resultado del servicio

En `LegacyPanelServiceResult` (o donde corresponda), agregar campos:
```python
cut_length_m: float        # metros lineales totales de corte (suma de todos los lotes)
pierce_count: int          # cantidad total de perforaciones
sheet_area_m2: float       # metros cuadrados totales de chapa
```

Estos valores deben calcularse al correr `LegacyPanelService.run()` o equivalente.

---

## Lo que NO hay que construir en esta tarea

- NO calcular precios en dinero
- NO crear la tabla de materiales (eso es una tarea posterior, GEMU_TASK_002)
- NO calcular kg de material ni segundos de máquina (eso requiere la tabla de materiales)
- NO modificar el motor legacy (solo leer su output)

---

## Casos de referencia para validación

**Tresbolillo**: diámetro 20mm, distancia 60mm, panel 500×500mm, margen 20mm
- Cada agujero es un círculo de perímetro `π × 20 ≈ 62.8mm`
- Si hay N agujeros, cut_length ≈ N × 62.8 + perímetro del panel (2000mm)
- Verificar que el número es coherente con una estimación manual

**DXF cualquiera**: cargar un patrón conocido y verificar que la suma de segmentos es razonable.

---

## Archivos relevantes

- `apps/sistema_industrial/sistema_industrial/presets/legacy_panel_adapter.py` — agregar funciones aquí
- `apps/sistema_industrial/sistema_industrial/presets/panel_service.py` — integrar en el resultado
- `Programas_hechos/Panel Decorativo/geometry/arc_segment.py` — fórmula de longitud de arco
- `Programas_hechos/Panel Decorativo/geometry/line_segment.py` — fórmula de segmento
- `Programas_hechos/Panel Decorativo/geometry/piece.py` — acceso a entities
- `Programas_hechos/Panel Decorativo/models/cad_result_item.py` — estructura del resultado

---

## Reporte esperado

Crear `coordination/reports/GEMU_RECURSOS_CONSUMIDOS_REPORT.md` con:
- Qué se implementó
- Caso de referencia con números reales (tresbolillo 20/60, panel 500×500)
- Tests agregados o cómo verificar
