# MSG_223 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino) + Dispatch
**Fecha:** 2026-07-24
**Asunto:** Relevamiento + diseño de la sección "DXF" — el algoritmo de organización YA
localizado, contrato definido. NO implementé nada, como se pidió.

## 1) El algoritmo de organización — localizado y confirmado

**`arrange_cad_result_items(items)`** en
`Programas_hechos/Panel Decorativo/layout/cad_result_layout.py:87`.

Es la función real y única en uso — TODOS los call-sites de producción la importan desde ahí
(`main.py`, `panel_sales_local_app.py` ×3, `legacy_panel_adapter.py`, y el test
`test_panel_label_offset.py`). Hace exactamente lo que describís: agrupa por
`(material, thickness)`, ordena cada grupo por `quantity` descendente, etiqueta de material
a la izquierda de cada fila (`_abbreviate_material`, lee `material_table.json`), etiqueta
`×N` de cantidad a 200mm debajo de cada pieza (el ajuste que hice yo mismo hace poco).

**Se puede invocar tal cual, sin tocarla.** No necesita ningún cambio para este flujo nuevo.

⚠️ **Hallazgo aparte** (no lo toqué, lo marco): existe un `dxf/cad_result_layout.py`
duplicado y desactualizado (98 líneas vs 155, con el offset de etiqueta viejo de 300mm) que
**no lo importa nadie** — código muerto que puede confundir a futuro. Lo dejo anotado, no es
parte de esta tarea.

### Firma exacta y contrato de input
```python
def arrange_cad_result_items(items: list[CADResultItem]) -> list:
    """Devuelve una lista PLANA: geometría trasladada (Piece/Polyline) +
    TextLabel de material (uno por fila) + TextLabel de cantidad (uno por
    pieza) — lista para pasar directo a MixedDXFExporter().save(...)."""
```

`CADResultItem` (`models/cad_result_item.py`) — los campos que `arrange_cad_result_items`
realmente usa:
- `material` (str), `thickness` (float) — **clave de agrupación por igualdad exacta** (no
  tolerancia — dos espesores "iguales" con distinta representación float NO agruparían en la
  misma fila; a tener en cuenta al construir los items del DXF nuevo).
- `quantity` (int) — orden dentro de la fila + texto de la etiqueta `×N`.
- `geometry_items` (list) — la geometría real de la pieza (ver punto 2).
- `occupied_width` / `occupied_height` (float, mm) — footprint usado para ubicar en la fila.
- `cut_length_mm`, `pierce_count`, `bend_count` — no los usa `arrange_cad_result_items`
  (sí los usa el pricing en otro lado); para este flujo (solo compilar un DXF, sin costear)
  pueden ir en 0.

## 2) El flujo completo — plan concreto, con TODAS las piezas ya existentes salvo una

Rastreé toda la cadena real (la misma que usa `pattern_type="dxf"` del motor hoy) hasta el
exportador final. Encontré que **está casi completa** — falta una sola pieza chica y
aditiva (filtro por capa), nada más.

**Paso 1 — selección múltiple de archivos**: del lado de Vega, puede reusar
`list_dxf_files()` (`api/patrones.py`) para navegar carpetas — ya existe, ya lo usa el picker
de "reapuntar DXF" de `update_pattern`.

**Paso 2 — material/espesor/cantidad por archivo**: validación de completitud, del lado del
backend del endpoint nuevo (no existe todavía, lo define quien construya esto).

**Paso 3 — extraer SOLO la capa "Dibujo Sin sangria"**: acá está la única pieza que falta.
`DXFImporter.load(filename)` (`dxf/importer.py:46`) ya hace la conversión DXF→geometría del
motor (LINE/ARC/CIRCLE/LWPOLYLINE-con-bulge → `LineSegment`/`ArcSegment` dentro de un
`Piece`) — es EXACTAMENTE la lógica que hace falta, pero hoy **no filtra por capa** (itera
`for entity in msp` sin mirar `entity.dxf.layer`). Propongo extenderla de forma aditiva:
```python
def load(self, filename, layer=None):
    ...
    for entity in msp:
        if layer is not None and entity.dxf.layer != layer:
            continue
        ...  # misma lógica de siempre
```
`layer=None` (default) preserva el comportamiento actual para TODOS los call-sites
existentes (cero riesgo de regresión) — el flujo nuevo pasaría `layer="Dibujo Sin sangria"`.

**Paso 4 — compilar el DXF final**: por cada archivo ya con material/espesor/cantidad:
```python
piece = DXFImporter().load(ruta_archivo, layer="Dibujo Sin sangria")
bbox = piece.bbox()
item = CADResultItem(
    name=nombre_archivo, quantity=cantidad, material=material, thickness=espesor,
    geometry_items=[piece],
    occupied_width=bbox.max_x - bbox.min_x,
    occupied_height=bbox.max_y - bbox.min_y,
    cut_length_mm=0, pierce_count=0,
)
```
Con la lista de `CADResultItem` completa: `arranged = arrange_cad_result_items(items)` →
`MixedDXFExporter().save(arranged, output_path)`. Los tres — `Piece`, `ArcSegment`/
`LineSegment`, `TextLabel` — ya tienen `export_dxf()`, así que el exportador no necesita
ningún cambio tampoco.

## Lo único a confirmar antes de construir
1. **El nombre exacto de la capa** — "Dibujo Sin sangria" tal cual lo escribiste, pero no
   tengo un DXF de muestra real para confirmar mayúsculas/espacios/tildes exactos tal como
   los graba el software que usa Constantino. Antes de construir, pediría un archivo de
   ejemplo.
2. La sensibilidad de agrupación por `thickness` EXACTO (sin tolerancia) — si el espesor
   viene de un select/dropdown ya normalizado (como en el resto del sistema) no es problema;
   si se escribe a mano libre podría generar filas separadas por error de tipeo (ej. "2.0" vs
   "2").

## Resumen para Vega (cuando arranque la UI)
El backend expone: selección de archivos + material/espesor/cantidad por archivo → un
endpoint nuevo que hace los pasos 3-4 de arriba → devuelve el DXF compilado. La UI no
necesita saber nada de la lógica de organización interna — solo junta la lista
`[{archivo, material, espesor, cantidad}, ...]` y la manda.

No construí nada — es diseño, como se pidió. Avisen si esto alcanza para pasar a
implementación o si Constantino quiere ajustar algo del flujo antes.

— Punto
