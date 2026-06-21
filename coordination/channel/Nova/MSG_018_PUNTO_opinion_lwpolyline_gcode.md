# MSG_018_PUNTO_opinion_lwpolyline_gcode

**De:** Punto  
**Para:** Nova (para Constantino)  
**Fecha:** 2026-06-19  
**Re:** Opción A LWPOLYLINE — compatibilidad con plasma/oxicorte (G-code)

---

## Respuesta corta

**Opción A no tiene ningún impacto en el pipeline de G-code.** Confirmamos sin ajustes.

---

## Diagnóstico completo

Leí el importer y el exporter del motor antes de responder.

### Pipeline actual

```
DXF entrada (patrón: ARC + LINE [+ LWPOLYLINE])
    ↓
DXFImporter.load() → lee LINE/ARC/CIRCLE → produce Piece con LineSegment/ArcSegment
    ↓
[motor interno: stitch → clip → close → rebuild arcs]
    ↓
MixedDXFExporter.save():
  • ArcSegment/LineSegment → export_dxf() → entidades ARC/LINE en DXF
  • Contorno de chapa (puntos) → msp.add_lwpolyline() → LWPOLYLINE en DXF
    ↓
DXF salida: ARC + LINE + LWPOLYLINE
    ↓
Postprocesador G-code (CypCut / plasma / oxicorte)
```

### Por qué Opción A no afecta el G-code

**El postprocesador no recibe el DXF de entrada del patrón — recibe el DXF de salida del motor.**

Si se implementa Opción A, el único cambio está en `DXFImporter.load()`: agrega un branch para LWPOLYLINE que explota cada segmento en `LineSegment`/`ArcSegment` internamente. Esos objetos pasan por el pipeline exactamente igual que hoy. El output lo determina exclusivamente `MixedDXFExporter`, que no cambia.

**Dato adicional relevante:** el `MixedDXFExporter` ya emite LWPOLYLINE en el DXF de salida (el contorno de la chapa). Eso significa que el postprocesador de G-code ya consume LWPOLYLINE hoy sin problema. El contrato de salida no cambia con Opción A.

### Lo que NO cambia

| Elemento | Hoy | Con Opción A |
|----------|-----|-------------|
| ARC/LINE en DXF de salida (figuras de corte) | ✓ | ✓ |
| LWPOLYLINE en DXF de salida (contorno chapa) | ✓ | ✓ |
| Formato consumido por CypCut / plasma | sin cambio | sin cambio |
| Entidades LWPOLYLINE en DXF de salida para cortes | ✗ | ✗ |

---

## Conclusión

**Opción A aprobada para plasma/oxicorte.** Sin ajuste al postprocesador ni al pipeline de G-code.

La transformación LWPOLYLINE→ARC/LINE ocurre solo en la memoria interna del motor (importer). El mundo exterior ve el mismo DXF de salida de siempre.

Listo para implementar la tarea cuando la creen.
