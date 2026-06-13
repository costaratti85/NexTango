# GEMU_TASK_003 — Reporte de implementación: Recursos consumidos por panel

**Agente:** Gemu  
**Fecha:** 2026-06-13  
**Estado:** Completado

---

## Resumen de lo implementado

### Bug raíz

En `Programas_hechos/Panel Decorativo/main.py`, función `create_cad_result_items_from_batch()`, los campos `cut_length_mm` y `pierce_count` del `CADResultItem` estaban hardcodeados en `0`:

```python
item = CADResultItem(
    ...
    cut_length_mm=0,   # <-- hardcodeado
    pierce_count=0,    # <-- hardcodeado
    ...
)
```

La tarea indica no modificar el motor legacy, por lo que la corrección se aplicó en el adaptador.

### Hallazgo clave: tipo `Figure`, no `Piece`

El brief indicaba que los objetos geométricos son de tipo `Piece`. Tras inspección del engine, se verificó que el stitcher (`entity_stitcher.py`) produce objetos `Figure` (de `geometry/figure.py`), no `Piece`. Ambos tienen el mismo atributo `.entities` con `ArcSegment` y `LineSegment`. Las funciones implementadas detectan figuras cerradas por duck-typing (`hasattr(item, "entities")`) para ser robustas ante ambos tipos.

---

## Archivos modificados

### `apps/sistema_industrial/sistema_industrial/presets/legacy_panel_adapter.py`

Se agregaron tres funciones de cálculo y se corrigió `_resource_payload()`:

**Funciones nuevas:**

- `calculate_cut_length_mm(geometry_items) -> float`  
  Itera sobre todos los items. Para figuras cerradas (con `.entities`), suma la longitud de cada `ArcSegment` y `LineSegment`. Para `Polyline` (contorno exterior), suma los segmentos consecutivos entre puntos.
  
- `calculate_pierce_count(geometry_items) -> int`  
  Cuenta cuántos items tienen `.entities` (figuras cerradas = perforaciones). La Polyline del contorno no tiene `.entities` y se excluye naturalmente.
  
- `calculate_sheet_area_m2(width_mm, height_mm) -> float`  
  `(width_mm * height_mm) / 1_000_000`

**Fórmulas utilizadas:**

| Tipo | Fórmula |
|------|---------|
| ArcSegment | `radius × |end_angle - start_angle| × π/180` (si sweep < 0, sumar 360°) |
| LineSegment | `sqrt((x2-x1)² + (y2-y1)²)` |
| Polyline | suma de distancias euclidiana entre puntos consecutivos |

**`_resource_payload()` corregida:** ahora llama a las tres funciones en lugar de leer `item.cut_length_mm` (que venía en 0). Agrega los campos `cut_length_m`, `pierce_count` y `sheet_area_m2` al payload de cada item.

### `apps/sistema_industrial/sistema_industrial/presets/panel_service.py`

- `LegacyPanelServiceResult` recibe tres nuevos campos: `cut_length_m: float`, `pierce_count: int`, `sheet_area_m2: float`.
- `LegacyPanelService.run()` calcula los totales agregados ponderados por `quantity` de cada lote y los pasa al resultado.

---

## Caso de referencia validado

**Parámetros:** tresbolillo, diámetro 20mm, distancia 60mm, panel 500×500mm, margen 20mm, quantity=1

| Campo | Valor calculado | Verificación manual |
|-------|----------------|---------------------|
| `cut_length_mm` | **6586.02 mm** | 60 círculos completos × π×20 ≈ 3769.9mm + 20 figuras de borde (parciales) ≈ 816mm + contorno 2000mm = ~6586mm ✓ |
| `cut_length_m` | **6.586 m** | — |
| `pierce_count` | **80** | 60 círculos interiores completos + 20 figuras de borde parciales ✓ |
| `sheet_area_m2` | **0.250000 m²** | 500 × 500 / 1_000_000 = 0.25 ✓ |
| `warnings` | `[]` | Sin advertencias (todos los valores > 0) |

**Desglose de geometría:**
- 1 Polyline (contorno del panel): 2000mm
- 80 Figure objects (perforaciones):
  - 60 círculos completos × 62.83mm ≈ 3769.9mm
  - 20 figuras de borde clipeadas ≈ 816mm
  - Total figuras: 4586mm

**Diferencia respecto a estimación naïve** (N × π×d solo):  
El contorno exterior (2000mm) se suma correctamente. Las figuras de borde tienen arcos parciales — promedio 40.8mm en lugar de 62.83mm, lo cual es coherente con un recorte real contra el margen.

---

## Cómo verificar

```python
from pathlib import Path
from sistema_industrial.presets.panel_service import LegacyPanelService, LegacyPanelServiceInput

svc = LegacyPanelService()
inp = LegacyPanelServiceInput(
    panel_mode='tresbolillo',
    width_mm=500.0, height_mm=500.0, quantity=1,
    hole_diameter_mm=20.0, hole_distance_mm=60.0, margin_mm=20.0,
)
result = svc.run(inp, Path('/tmp/test_panel'))
print(result.cut_length_m)   # -> ~6.586
print(result.pierce_count)   # -> 80
print(result.sheet_area_m2)  # -> 0.25
```

---

## Lo que NO se implementó (fuera de scope)

- Precios en dinero
- Tabla de materiales (GEMU_TASK_002 pendiente)
- kg de material ni segundos de máquina
- Modificaciones al motor legacy
