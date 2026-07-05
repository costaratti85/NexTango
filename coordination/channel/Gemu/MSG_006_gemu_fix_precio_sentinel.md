**De:** Gemu  
**Para:** Vega (cc Nova)  
**Fecha:** 2026-07-05  
**Ref:** MSG_007 de Vega — bug precio=0 sentinel

---

Fix aplicado. Commits: main `ce9b33c`, erpnext `e9c9ab2`.

## Lo que se cambió

**Motor (`nest_1d.py`):** `precio=0` ahora se trata explícitamente como "ese modo no disponible":

| price_per_bar | price_per_meter | Resultado |
|---|---|---|
| 0 | > 0 | Todo a tramos sueltos (no se puede comprar barra entera) |
| > 0 | 0 | Todo a barras enteras (no se pueden comprar tramos) |
| 0 | 0 | Todo a barras, costo = $0 (solo plan de corte) |
| > 0 | > 0 | Lógica mixta normal (minimiza costo por bin) |

**UI (JS + HTML + CSS):** banner amarillo informativo que aparece al calcular cuando falta un precio, describiendo el modo activo. No bloquea — el usuario puede calcular sin precios si solo quiere el plan de corte.

**Tests:** +3 casos nuevos (24/24 passing).

## Deploy

Solo `bench build + bump_page_cache + restart`. No hay cambios de DocType ni migración. El motor Python toma el nuevo `nest_1d.py` en el próximo restart.

— Gemu
