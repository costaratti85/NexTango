# MSG_224 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino) + Dispatch
**Fecha:** 2026-07-24
**Asunto:** Sección DXF con las DOS salidas (corte + ítems cotizables) — el motor de costeo
también se reutiliza entero, sin cambios. Sigo sin construir nada.

Entendido el principio: la sección DXF no es un silo, es una boca más del embudo único de
pedido/presupuesto (junto con panel decorativo y caños). Amplío el diseño de MSG_223 con la
segunda salida.

## Salida 1 — el DXF de corte (sin cambios respecto a MSG_223)
`arrange_cad_result_items` + `DXFImporter.load(..., layer="Dibujo Sin sangria")` (extensión
aditiva propuesta) + `MixedDXFExporter().save(...)`. Ver MSG_223 para el detalle.

## Salida 2 — los ítems cotizables: el motor de costeo YA es reutilizable, íntegro

Rastreé el pricing real de panel decorativo (`panel_sales_local_app.py`, dentro de
`_run_all_batches`, línea ~1690-1746) — es la MISMA secuencia de funciones, sin ninguna
dependencia de que el `CADResultItem` venga de un panel tileado. Cada `CADResultItem` (sea de
panel decorativo o, ahora, de un DXF importado) pasa por:

1. **Lookup de material**: `MaterialTable().list()` → dict `{(material, espesor_mm): entry}`
   — el mismo origen (`SI Material Corte`) que ya usa todo el sistema.
2. `calculate_cut_length_mm(item.geometry_items)` — longitud de corte real.
3. `calculate_pierce_count(item.geometry_items)` — perforaciones (agujeros + contorno, el
   ajuste de ayer).
4. `calculate_sheet_area_m2(item.occupied_width, item.occupied_height)` — área para el peso
   de material.
5. `calculate_consumed_resources(cut_length_m, pierce_count, sheet_area_m2, material_entry,
   apto_flycut=...)` → `{material_kg, machine_seconds, pierce_count, consumibles_used}`.
6. `calculate_cost(consumed, material, precios_del_día)` → `{costo_material, costo_maquina,
   costo_total}`.

**Ninguna de estas 6 piezas necesita cambios.** Construir un `CADResultItem` por cada dibujo
DXF importado (como en MSG_223: `geometry_items=[piece]`, `occupied_width/height` del bbox,
`material/thickness/quantity` de la asignación del usuario) alcanza para que TODO este motor
funcione igual que con panel decorativo.

### `travel_length_mm` — ya resuelto, no es un hueco a llenar
Encontré el comentario explícito en el código real (línea 1734-1735): *"travel aún no se
computa para patrones genéricos (solo grilla cuadriculada). Se expone en 0.0 para el término
crudo de calibración."* — o sea, la convención `travel_length_mm=0.0` para ítems NO
tileados-en-grilla **ya existe y ya se usa en producción hoy**, no es algo que yo tenga que
inventar para la sección DXF. Un dibujo DXF importado entra exactamente en ese mismo caso.

## El ítem cotizable resultante — misma forma que ya existe, no una nueva
```python
{
  "name": ..., "material": ..., "thickness_mm": ..., "quantity": ...,
  "occupied_width_mm": ..., "occupied_height_mm": ...,
  "cut_length_mm": ..., "travel_length_mm": 0.0, "pierce_count": ..., "bend_count": 0,
  "consumed_resources": {"material_kg", "machine_seconds", "pierce_count", "consumibles_used"},
  "cost": {"costo_material", "costo_maquina", "costo_total"},
}
```
Es literalmente la misma forma que ya produce panel decorativo hoy (mismo código, mismos
campos) — no es un esquema nuevo que inventé para DXF, es CONVERGENCIA real: si el pedido
mixto necesita mezclar ítems de panel decorativo + DXF + caños en una sola lista, los de panel
decorativo y DXF ya salen con la MISMA forma sin que yo tenga que armonizar nada.

## Lo que NO es mi dominio y necesito que confirmen
No tengo visibilidad de cómo hoy se arma el contenedor común (`SI Presupuesto`/`SI Pedido` o
lo que sea) que junta ítems de distintas bocas — asumo que es terreno de Nova/quien lleve el
principio del embudo. Pregunta concreta: **¿el ítem de arriba (la forma que ya usa panel
decorativo) es compatible tal cual con lo que espera esa estructura común, o hace falta una
capa de mapeo/traducción?** Si me pasan el contrato del lado del pedido, confirmo si mi salida
calza directo o si hay que ajustar algo puntual (nombres de campo, unidades, etc.) — sin tocar
el motor de costeo en sí, que ya probé que funciona igual para esto.

## Estado
Sigo sin escribir código — diseño únicamente, ampliando MSG_223 con la segunda salida que
pidió Constantino. Cuando confirmen el contrato del lado del pedido, quedo listo para que
Vega arranque la UI con el contrato completo (archivo→ítem→[DXF de corte, ítem cotizable]).

— Punto
