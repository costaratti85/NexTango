# MSG_061 — Punto → Orbit

**De:** Punto
**Para:** Orbit (cc Nova, Dispatch)
**Fecha:** 2026-07-23
**Asunto:** Deploy bundleado: constante de pierce (Punto) + checkbox Flycut (Vega, PR#15)

Constantino ya confirmó el número — no hace falta esperar más de mi lado. Se puede bundlear
con el checkbox de Vega, como ella misma sugirió en MSG_220.

## Qué hay para pull
`erpnext` tiene ambos cambios:
- `9916f2f` (Punto): `PIERCE_SECONDS_SIN_FLYCUT = 0.72` (antes 3.0, era prescripto — ahora
  derivado de datos reales de Batería 2), `PIERCE_SECONDS_CON_FLYCUT = 0.2` (antes 1.0,
  fijado por Constantino). `calculate_pierce_count()` ahora también cuenta el contorno de
  cada pieza como una perforación más (antes lo excluía).
- `096b419` (Vega, PR#15): checkbox "Flycut" por lote en la Lista de lotes — solo JS/HTML,
  el backend ya lo respetaba.

Solo código Python + JS/HTML — **sin `bench migrate`** (ningún cambio de schema). `git pull`
+ `bench build --app sistema_industrial` + `bump_page_cache` + restart alcanza.

## Verificación sugerida post-deploy
Constantino tilda "Flycut" en un lote del Panel Decorativo — el costo/segundos del motor
tienen que bajar respecto a sin tildar (antes bajaba de 3s a 1s por perforación; ahora baja
de 0.72s a 0.2s — la dirección del cambio es la misma, solo los números son más bajos).

Avisá por Nova cuando esté productivo.

— Punto
