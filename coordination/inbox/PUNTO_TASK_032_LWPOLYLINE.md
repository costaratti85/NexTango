# PUNTO_TASK_032 — Soporte LWPOLYLINE en validador e importer (Opción A)

**Para:** Punto  
**De:** Nova  
**Fecha:** 2026-06-18  
**Prioridad:** Normal

---

## Decisión

Constantino confirmó **Opción A** de tu análisis en MSG_016.

## Alcance

1. **`dxf_validator.py`**: agregar LWPOLYLINE a entidades soportadas, con lógica:
   - Sin flags de spline/mesh → soportada (modo completo)
   - Con flags de spline → no soportada (modo restringido)

2. **`dxf/importer.py`** (motor legacy): leer LWPOLYLINE → emitir ARC/LINE por segmento según bulge por vértice. Incluir el segmento de cierre si `is_closed=True`.

3. **Fuera del alcance**: POLYLINE heavyweight — queda en modo restringido hasta decisión explícita futura.

4. Probar con el DXF que originalmente activó el problema (polilínea de arcos que entró en modo restringido).

## Reporte

`coordination/reports/PUNTO_TASK_032_REPORT.md` y mensaje en `coordination/channel/Nova/`.
