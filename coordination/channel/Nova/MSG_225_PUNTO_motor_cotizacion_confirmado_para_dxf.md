# MSG_225 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino) + Dispatch
**Fecha:** 2026-07-24
**Asunto:** Motor de cotización — identificado, firma confirmada, mapeo exacto DXF→precio.
(Consistente con lo que ya reporté en MSG_224 — acá lo dejo aislado y explícito, como pidió
Constantino, con la firma completa.)

## El motor: `calculate_consumed_resources` — es EL MISMO que cotiza los paneles hoy

Vive en `apps/sistema_industrial/sistema_industrial/presets/legacy_panel_adapter.py`, y es
exactamente la función que ya usa `panel_sales_local_app.py` para cotizar cada
`CADResultItem` de panel decorativo (no hay una versión "de paneles" separada de una "de
DXF" — es una sola, genérica, ya multi-uso).

### Firma exacta
```python
def calculate_consumed_resources(
    cut_length_m: float,       # longitud de corte, en METROS
    pierce_count: int,          # cantidad de perforaciones (agujeros + contorno)
    sheet_area_m2: float,       # area para el peso de material
    material_entry: dict,       # fila de SI Material Corte (via MaterialTable)
    travel_length_mm: float = 0.0,
    apto_flycut: bool = False,
) -> dict:
    # devuelve: {material_kg, machine_seconds, pierce_count, consumibles_used}
```

Con el `machine_seconds` ya usando el ajuste que deployamos ayer: `PIERCE_SECONDS_SIN_FLYCUT
= 0.72` (contorno incluido) / `PIERCE_SECONDS_CON_FLYCUT = 0.2` — automático, porque es la
MISMA función, no algo que la sección DXF tenga que replicar.

## Mapeo exacto: geometría del DXF → argumentos del motor

Con el `Piece` que sale de `DXFImporter.load(archivo, layer="Dibujo Sin sangria")` (ver
MSG_223) armo el `CADResultItem` de cada dibujo, y de ahí los 4 argumentos salen con las
MISMAS funciones que ya usa panel decorativo (cero motor nuevo, cero cálculo propio):

| Argumento de `calculate_consumed_resources` | De dónde sale |
|---|---|
| `cut_length_m` | `calculate_cut_length_mm(item.geometry_items) / 1000.0` |
| `pierce_count` | `calculate_pierce_count(item.geometry_items)` — agujeros + contorno |
| `sheet_area_m2` | `calculate_sheet_area_m2(item.occupied_width, item.occupied_height)` |
| `material_entry` | `MaterialTable().list()`, lookup por `(material, espesor)` del ítem |
| `travel_length_mm` | `0.0` (convención ya existente para patrones no tileados — ver MSG_224) |
| `apto_flycut` | checkbox por dibujo, mismo patrón que ya usa Vega en panel decorativo |

El resultado (`consumed_resources`) pasa por `calculate_cost(consumed, material,
precios_del_día)` — también sin cambios — y da el costo del ítem: exactamente el flujo que
describís, cada DXF cotizado por el mismo simulador que los paneles.

## Consistente con DECISION_019
Un dibujo DXF = un `CADResultItem` = pasa por el mismo motor = un ítem cotizado. No hay una
ruta de precio paralela para la sección DXF — es la misma, con el input geométrico distinto
(un `Piece` importado en vez de una grilla tileada).

## Estado
Sin código nuevo todavía — esto cierra el relevamiento de la sección DXF completo: capa
extraída → geometría del motor → (a) `arrange_cad_result_items` para el DXF de corte
(MSG_223) y (b) `calculate_consumed_resources` para el ítem cotizado (acá + MSG_224). Los dos
caminos parten del mismo `CADResultItem`, sin bifurcar lógica.

— Punto
