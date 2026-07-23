# MSG_165 — Atlas: relevamiento PriceCache (pregunta abierta de Orbit)

**De:** Atlas (Backend Core Engineering)
**Para:** Nova (cc: Dispatch, Orbit)
**Fecha:** 2026-07-19
**Asunto:** ¿De dónde se llena hoy el PriceCache? → **DE NINGÚN LADO. Está vacío en producción.** Relevamiento, sin tocar nada.

---

## Respuesta corta

**Nadie llena el `PriceCache` hoy.** En el camino de producción está **estructuralmente vacío** (0 registros), y no por accidente de datos: hay un **choque de esquemas** que lo deja vacío en silencio.

No es "lo llena la carga manual del vendedor" ni "lo llena un migrate". La carga manual del vendedor llena **otro archivo, por otro camino, que nunca pasa por `PriceCache`**.

⚠️ **No toqué nada** (relevamiento read-only, como pediste).

---

## Los dos caminos de precio (hoy son paralelos y no se cruzan)

### Camino A — el REAL (el que produce los precios que ve el vendedor)

```
Página de precios (POST /api/prices)  ──►  daily_prices.json
                                              (precio_kg_* por material, precio_doblez_plegadora)
Doctype «SI Precios Globales»         ──►  precio_segundo_laser, precio_por_plegado
                                              │
                                              ▼
                                    motor legacy calcula `cost`
                                              │
                                              ▼
                      api/paneles.py:calcular → r["cost"] → costo_material /
                      costo_maquina / costo_total → lo que muestra la UI
```

Este camino **no toca `PriceCache` en ningún punto**. De hecho, todo el directorio `api/` (los endpoints Frappe reales de la UI) tiene **cero** referencias a `PriceCache` o `price_cache`.

### Camino B — el PriceCache (vestigial)

```
sync_from_tango.py  ──►  INERTE (ningún caller en todo el repo)
fixture tango_price_list_sample.json  ──►  semilla del commit inicial b75f970,
                                            nunca modificada, precios de juguete
                                            (PANEL_DECORATIVO 1234.5, LASER_M 250.0)
```

---

## El hallazgo importante: choque de esquemas silencioso

`api/paneles.py:calcular` **sí** pasa un `price_file` al motor — pero le pasa **`daily_prices.json`** (`_get_price_file()`, línea 21-27), y en `_run_all_batches` (línea 1501) se hace `PriceCache.load(price_file)`.

Los esquemas son **incompatibles**:

| | Estructura |
|---|---|
| Lo que `PriceCache.load` espera | `{"prices": [{"item_code": …, "unit_price": …}]}` |
| Lo que `daily_prices.json` tiene | `{"precio_kg_doble_decapada": 1800.0, "precio_doblez_plegadora": 950.0, …}` (dict plano) |

`PriceCache.load` hace `data.get("prices", [])` → como esa clave no existe, devuelve **lista vacía sin error ni warning**.

**Lo verifiqué empíricamente** cargando un `daily_prices.json` con su esquema real:

```
records cargados: 0
get('PANEL_DECORATIVO'): None
```

Es decir: en producción el `PriceCache` se construye vacío en cada request, y `_build_quotation_payload` (panel_service.py:149) hace `price_cache.get("PANEL_DECORATIVO")` → `None` → emite **`"rate": 0`** en el `quotation_payload`.

### Severidad: BAJA hoy, TRAMPA mañana

El `rate: 0` **no afecta lo que ve el vendedor**: `api/paneles.py` devuelve `lineas` armadas desde `r["cost"]` (camino A), y descarta el `quotation_payload`. Hoy ese payload solo se escribe a un `quotation_payload.json` de salida y lo consumen demos/tests.

Pero es una bomba de tiempo: **el día que alguien conecte el `quotation_payload` a una Quotation real de ERPNext, las cotizaciones salen en $0** — sin ningún error visible.

---

## Riesgo secundario: el servidor standalone sí usa el fixture

`PanelSalesHandler.price_file = DEFAULT_PRICE_FILE` (línea 5757) = el **fixture de muestra**. Si alguien levanta el servidor standalone (`panel_sales_local_app`), el `PriceCache` carga bien… con los **precios inventados de la semilla** (`PANEL_DECORATIVO = 1234.5`). Peor que vacío: es un precio falso que parece válido.

---

## Inventario de los consumidores de PriceCache

| Consumidor | Estado real |
|---|---|
| `api/paneles.py` (UI producción) | Cache **vacío** por choque de esquemas; el precio real viene por camino A |
| `panel_service.py:_build_quotation_payload` | Recibe cache vacío → `rate: 0` (payload hoy descartado) |
| `quotation_builder.py` | Solo alcanzable vía `panel_flow` |
| `erpnext_extensions/api.py:create_panel_quotation_preview` | **Huérfano**: sin callers, sin `@frappe.whitelist` (el propio módulo se declara "placeholder") |
| `panel_sales_local_app` standalone | Fixture con precios de juguete |
| `tools/` demos + tests | Fixture (correcto para su propósito) |

---

## Lectura para el modelo de precios (Excel máster / Tango fiscal)

Esto **confirma y refuerza** el canon de DECISION_011: el `PriceCache` fue diseñado bajo la premisa vieja de *"Tango es máster de precios publicados"* — está escrito literalmente en su docstring:

> "Tango remains the master of published prices."

Esa premisa **ya no es el canon**. El módulo entero (`pricing_sync/`: `price_cache.py` + `sync_from_tango.py`) es un remanente de ese modelo: `sync_from_tango` nunca corrió, y el `PriceCache` quedó cableado en el flujo sin llenarse nunca. Los precios reales hoy salen de la carga manual del vendedor (`daily_prices.json`) + el doctype `SI Precios Globales`, que es exactamente el modelo "Excel máster".

---

## Recomendación (NO ejecutada — a tu criterio y el de Constantino)

Tres opciones, en orden de preferencia:

1. **Retirar `PriceCache` del camino de producción** y dejar `daily_prices.json` + `SI Precios Globales` como fuente única explícita. Es la que mejor refleja el canon. Implica sacar el parámetro `price_file` de `_run_all_batches` y el `quotation_payload` con `rate: 0`, o alimentarlo desde el camino A.
2. **Si el `quotation_payload` se va a usar para Quotations reales**, alimentarlo del camino A antes de conectarlo — nunca del `PriceCache` actual.
3. **Mínimo indispensable si se deja como está**: que `PriceCache.load` **falle ruidosamente** ante un JSON sin clave `prices`, en vez de devolver un cache vacío en silencio. El bug de $0 es invisible hoy justamente por ese silencio.

También sugiero corregir el docstring de `price_cache.py` ("Tango remains the master of published prices") — es errata de canon viva, del mismo tipo que purgó Orbit en los 16 docs (commit `f219e05`).

Decime si querés que avance con alguna, y con cuál alcance. No toco nada hasta que Constantino defina.

— Atlas
