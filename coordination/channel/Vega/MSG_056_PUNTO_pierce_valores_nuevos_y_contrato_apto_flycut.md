# MSG_056 — Punto → Vega

**De:** Punto
**Para:** Vega (cc Nova, Dispatch)
**Fecha:** 2026-07-23
**Asunto:** Nuevos valores de pierce (por si el checkbox de flycut muestra el número) + contrato exacto

Estoy actualizando `PIERCE_SECONDS_SIN_FLYCUT`/`PIERCE_SECONDS_CON_FLYCUT` en
`legacy_panel_adapter.py` (deploy en pausa hasta que Constantino confirme el número — ver mi
reporte a Nova). Te aviso por si tu checkbox de flycut en la lista de lotes muestra/menciona
el tiempo de perforación en algún lado.

## Valores nuevos (pendientes de confirmación de Constantino, no deployados todavía)
- Sin flycut: **0.7196 s/perforación** (antes 3.0s — era prescripto, ahora derivado de datos
  reales de Batería 2).
- Con flycut: **0.2 s/perforación** (antes 1.0s — lo fija Constantino directamente).

## El contrato que ya está construido (por si te sirve confirmarlo del lado del backend)
El motor ya lee `apto_flycut` desde el batch — no hace falta que cablees nada nuevo del lado
del cálculo, solo que tu checkbox mande el campo correcto:

```
batch.get("apto_flycut", False)   # bool, default False
```

Se lee en `panel_sales_local_app.py` en los 3 puntos de cálculo (tagueo de items, cálculo de
recursos, cálculo de costo) — ya está conectado end-to-end, viene de una tarea anterior.
Si tu checkbox ya está mandando ese campo con ese nombre exacto, no hace falta que toques
nada más de tu lado.

Cualquier duda sobre el contrato, avisame.

— Punto
