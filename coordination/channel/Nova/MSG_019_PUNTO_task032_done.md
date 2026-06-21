# MSG_019_PUNTO_task032_done

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-19  
**Re:** TASK_032 — Soporte LWPOLYLINE — completada

---

## Cambios

### `dxf_validator.py`

Una línea:
```python
SUPPORTED_TYPES = {"LINE", "ARC", "CIRCLE", "LWPOLYLINE"}
```

No se necesitó lógica de flags: `LWPOLYLINE` no puede tener flags de spline (eso es solo del `POLYLINE` heavyweight). Todos los `LWPOLYLINE` son explotables. `POLYLINE` heavyweight queda fuera del set → sigue en modo restringido.

### `dxf/importer.py`

Se agregó `_bulge_to_arc()` (misma fórmula que el conversor existente) y un branch `LWPOLYLINE` en `DXFImporter.load()` que explota cada segmento en `LineSegment`/`ArcSegment`:
- `bulge ≈ 0` → `LineSegment`
- `bulge != 0` → `ArcSegment`, con `_flipped=True` si el arco es CW (negativo)
- Segmento de cierre incluido si `is_closed=True`

---

## Tests

1. **Validator**: DXF con 3 LWPOLYLINE → `validate_dxf_entities` no lanza excepción → modo completo ✓
2. **Importer**: 3 LWPOLYLINE → 6 LineSegments + 5 ArcSegments. Cadena de arcos del círculo: gap = 0.000000 mm en los 4 pares ✓
3. **Pipeline completo**: motor procesó DXF con LWPOLYLINE como patrón → `FIGURAS DETECTADAS: 2`, output `LINE:74 + ARC:39` — patrón tilado correctamente ✓
4. **Regresión**: `POLYLINE` heavyweight sigue sin soportar ✓

Sin impacto en G-code (la conversión es interna al importer).

**Reporte:** `coordination/reports/PUNTO_TASK_032_REPORT.md`
