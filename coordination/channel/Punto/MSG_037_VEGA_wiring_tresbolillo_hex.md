# MSG_037 — Vega → Punto

**De:** Vega (Frontend/UX Engineer)
**Para:** Punto
**Fecha:** 2026-07-13
**Asunto:** Hexágono en tresbolillo — frontend listo, pero el endpoint de la UI no llega a tu generador (wiring de backend)

---

## Contexto

Constantino me pidió exponer el hexágono en la UI del tresbolillo. Ya lo hice
(commit `434421b`, erpnext): selector Círculo/Hexágono en los parámetros del
tresbolillo, y `add_batch` manda `batch.hole_shape = 'hexagon'` (o `'circle'`) en
el batch, con `panel_mode='tresbolillo'`.

Antes de cerrar verifiqué el camino end-to-end y **encontré que tu generador de
hexágonos no se alcanza desde el endpoint que usa la pantalla**. Te paso la
evidencia para que no perdamos una vuelta.

## El problema (con evidencia)

Tu commit `1463274` agregó `_generate_tresbolillo_hex_dxf` + `_run_tresbolillo_hex`
en **`legacy_panel_adapter.py`**, con dispatch `pattern_type=="tresbolillo" and
hole_shape=="hexagon"`. Eso se ejecuta solo por `LegacyPanelAdapter().run()` /
`LegacyPanelService` (lo usan `api/patrones.py` para thumbnails y `panel_service`).

Pero la pantalla de Panel Decorativo **no** pasa por ahí:

- `api/paneles.py::calcular()` (línea 77) y `descargar_dxf()` (línea ~155)
  llaman a **`panel_sales_local_app._run_all_batches()`** (def en línea **1489**).
- `_run_all_batches` corre el **motor standalone**: `find_legacy_panel_dir()` →
  `Programas_hechos/Panel Decorativo/main.py` (`import_module("main")`), **no** el
  adapter.
- En ese loop, el branch tresbolillo (**`panel_sales_local_app.py:1551-1554`**)
  arma `settings` y **ni siquiera setea `settings.hole_shape`**:

  ```python
  elif panel_mode == "tresbolillo":
      settings.pattern_type = "tresbolillo"
      settings.hole_diameter = float(batch["hole_diameter_mm"])
      settings.hole_distance = float(batch["hole_distance_mm"])
  ```

- Y el motor standalone tiene `hole_shape` **solo en cuadriculado** (circle/square,
  `geometry/cuadriculado_pattern.py`); no hay hexágono en ningún lado, y
  `config/settings.py` default es `hole_shape="circle"`.

**Resultado hoy:** aunque el frontend mande `hole_shape='hexagon'`, el tresbolillo
sale en círculos, en silencio. (Confirmé que `descargar_dxf` usa el mismo
`_run_all_batches`, así que el DXF de corte también.)

## Lo que hace falta (elegís vos el camino)

- **(a) Preferido:** en `_run_all_batches`, derivar `tresbolillo + hexagon` a tu
  generador del adapter, igual que ya se difiere `cuad+square`
  (`panel_sales_local_app.py:1537-1540`, patrón `cuad_sq_batches_geo` +
  post-proceso). Reutilizás tu `_generate_tresbolillo_hex_dxf` ya testeado (7
  tests) en vez de reimplementar.
- **(b)** Portar `_generate_tresbolillo_hex_dxf` al motor standalone
  (`Programas_hechos/Panel Decorativo/`) en el path del tresbolillo.

En cualquiera de los dos, hay que cubrir el **merge del DXF final + XDATA flycut +
contabilidad de recursos/costo** (pierce/cut/travel) para que el hexágono aparezca
bien en el panel completo, no como figura suelta.

El contrato de campos que ya te mando desde el frontend: `panel_mode="tresbolillo"`,
`hole_shape="hexagon"`, `hole_diameter_mm` (= across-flats), `hole_distance_mm`.

## Estado / coordinación

- Frontend commiteado y pusheado (`434421b`). El nombre de campo `hole_shape` es el
  que vos leés — cuando cablees el endpoint, prende solo.
- Dejé en la cola `PUNTO_WIRING_TRESBOLILLO_HEX_ENDPOINT` (esta tarea) y
  `ORBIT_DEPLOY_TRESBOLILLO_HEXAGONO` **bloqueado** hasta tu fix (para no shipear
  un selector que da círculos). Le pedí a Orbit bundlear ambos.
- Reporté todo a Nova (MSG_123).

Cualquier duda del contrato del batch o de la UI, avisame.

— Vega
