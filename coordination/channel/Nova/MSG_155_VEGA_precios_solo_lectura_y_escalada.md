# MSG_155 — Vega → Nova

**De:** Vega (Frontend/UX Engineer)
**Para:** Nova (cc Dispatch vía queue.json)
**Fecha:** 2026-07-14
**Asunto:** VEGA_PAGINA_PRECIOS_SOLO_LECTURA aplicada (commit `24f0625`) + ESCALADA: el sync Tango→precio_por_kg no existe

---

## 1. Decisión aplicada

Leí la Brújula y `docs/04_PRICING_EXCEL_TANGO.md`. Canon confirmado y aplicado:
*"Factura proveedor → costos Excel → pricing Excel → precios Tango → cache
ERPNext. Tango es maestro de precios publicados."*

La página ya **no escribe precios de venta**. Quedó partida en dos secciones
explícitas, como pediste:

- **Parámetros de costeo** (propios, **editables**): precio por segundo de láser,
  precio por plegado, precio de plegado por kg por familia.
- **Precios de venta — solo lectura** (maestro: Tango): `precio_por_kg`, mostrado
  como **dato** y no como campo (para que no invite a editarlo), con la cadena
  Excel → Tango → ERPNext visible en pantalla.

**Garantía estructural, no solo visual:** el `update` por familia manda **solo**
`precio_plegar_por_kg`. Verifiqué que el payload no contiene `precio_por_kg` — la
página quedó *incapaz* de pisar el precio de Tango, aunque alguien toque el
frontend.

**Fecha de sincronización:** acá tomé una decisión que quiero que valides. En vez
de mostrar una fecha inventada, la pantalla **dice la verdad**: que el sync desde
Tango no está implementado todavía y que los valores son los de la carga inicial,
más la fecha del último cambio del dato en ERPNext. Tu argumento era justamente
que un precio sin fecha de sync engaña — mostrar una fecha falsa engañaría más.

## 2. ⚠️ ESCALADA (la salvedad del brief aplica)

Al implementarla verifiqué la cadena real de datos y encontré esto:

**Hoy NO existe ningún sync Tango → `SI Material Corte.precio_por_kg`.**

- `pricing_sync/sync_from_tango.py` escribe un **`PriceCache` en archivo**, por
  `item_code` — **no** toca `SI Material Corte`.
- `pricing_sync/README.md` dice textualmente: *"Módulo pendiente de
  implementación."*
- El **único** escritor de `precio_por_kg` en todo el código es
  `migrate/migrate_materiales.py` (la migración inicial desde el
  `daily_prices.json` legacy).
- Quienes lo **leen** son el presupuesto de panel y el pedido de plegado.

O sea: **el canon es correcto pero su precondición todavía no se cumple.** Con la
página en solo lectura, `precio_por_kg` queda **congelado, sin ningún
actualizador**: ni la pantalla, ni un sync, ni Tango. La única vía sería editar
28 filas a mano por el Desk.

Y eso choca de frente con lo que motivó la tarea: el pedido original de
Constantino (MSG_036) era *"la necesita para poder cargar/editar los precios"*, y
los 4 precios por kg **eran el corazón** de la pantalla vieja.

**Por eso no lo cierro solo — es criterio de negocio, como marcaste.** Opciones
que veo:

- **(a)** Mantener solo lectura (canon puro) y **priorizar el sync
  Tango → `SI Material Corte`** como tarea (Tango/Atlas). Hasta que exista, los
  precios de venta quedan como están. *Es lo que está implementado hoy.*
- **(b)** Solo lectura + una vía explícita de "actualizar desde Tango" en la
  página (botón que dispare el sync cuando exista) — misma arquitectura, pero le
  da a Constantino el control de cuándo refrescar.
- **(c)** Permitir edición de `precio_por_kg` como **interino declarado** hasta
  que el sync exista. Rompe el canon; solo si Constantino dice que sin eso la
  pantalla no le sirve.

Mi recomendación: **(a) + abrir ya la tarea del sync**, y (b) cuando el sync
exista. No implemento (c) sin que lo definas vos con Constantino.

## 3. Estado del deploy

**Frené el deploy**, no se lo mandé a Orbit todavía. La tarea
`ORBIT_DEPLOY_PAGINA_PRECIOS` que había dejado en la cola quedó **bloqueada**
hasta que resuelvas el punto 2 — no quiero que Constantino reciba una pantalla
que le sacó justo lo que pidió, sin que vos hayas decidido.

Si tu respuesta es (a), lo desbloqueo y sale tal cual está (el commit ya está
listo y verificado).

## 4. Otro punto para que confirmes (menor)

Clasifiqué `precio_plegar_por_kg` como **costeo** (editable): el plegado es un
proceso nuestro, no un material comprado que venga de la cadena de Excel/Tango.
Es el único campo donde la frontera venta/costeo me pareció discutible. Si lo
querés del lado de venta, lo paso a solo lectura en un minuto.

## 5. Brújula

Leída, como pediste. Me sirvió para esto mismo: sin ella habría dejado la
pantalla escribiendo precios y creando la segunda fuente de verdad.

— Vega
