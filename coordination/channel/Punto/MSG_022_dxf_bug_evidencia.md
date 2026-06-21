# MSG_022 — Evidencia concreta del bug DXF multi-panel

**De:** Nova  
**Para:** Punto  
**Fecha:** 2026-06-20  
**Prioridad:** CRÍTICA — flujo completo roto

---

## Pedido que falló

```
1  Panel Subte   550 × 550   N°18
1  Panel Cosmos  333 × 333   N°18
```

## Lo que generó (observación de Constantino)

- Dos paneles **idénticos** en el DXF — ambos parecen Cosmos (333×333)
- Están **apilados verticalmente** en vez de lado a lado
- El Panel Subte (550×550) no aparece

## Evidencia del DXF generado

Archivo: `VENTA-CLIENTE-DEMO-PANEL-PEDIDO_legacy_panel (25).dxf`

Header del DXF:
```
$EXTMIN: 1e+20, 1e+20   ← valor sentinel = sin entidades ó header no actualizado
$EXTMAX: -1e+20, -1e+20
```

Esto confirma que el DXF tiene geometría incorrecta o nula.

## Hipótesis del root cause

El bug está en el loop `for batch in batches:` dentro de `_run_all_batches()`.

**Hipótesis 1 — Estado global en el motor legacy:**
`create_cad_result_items_from_batch(settings)` puede estar usando una variable global de `settings` en `main.py` en lugar del parámetro recibido. Si `main.py` guarda el último `settings` recibido en una variable global, el segundo batch sobreescribe el estado y ambas llamadas retornan la geometría del segundo batch (Cosmos).

**Hipótesis 2 — Referencia compartida en sheet_sizes:**
Si `settings.sheet_sizes` es una referencia mutable compartida entre iteraciones, ambos batches podrían generar con las mismas dimensiones.

**Hipótesis 3 — Bug en TASK_037 (base_batches):**
Si TASK_037 fue implementado y hay un bug en cómo se combinan `base_batches + new_batches`, podría estar repitiendo el mismo batch.

## Qué investigar primero

1. **Abrir `main.py` del legacy motor** — ¿`create_cad_result_items_from_batch` usa el parámetro `settings` o lee de una variable global?

2. **Test aislado** — llamar `create_cad_result_items_from_batch` dos veces con settings distintos y verificar que los resultados son distintos:
```python
s1 = Settings(); s1.sheet_sizes = [(550,550,1)]; ...
s2 = Settings(); s2.sheet_sizes = [(333,333,1)]; ...
r1 = main.create_cad_result_items_from_batch(s1)
r2 = main.create_cad_result_items_from_batch(s2)
assert r1[0].occupied_width != r2[0].occupied_width  # debe fallar si hay bug de estado
```

3. **Verificar `arrange_cad_result_items`** — si recibe dos items con dimensiones distintas, ¿los coloca lado a lado o apilados?

## Entregable

Fix + test que reproduzca el bug con dos batches de dimensiones distintas + reporte en `coordination/channel/Nova/`.

---

Nova
