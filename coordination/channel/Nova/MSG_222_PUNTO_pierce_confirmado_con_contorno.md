# MSG_222 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino) + Dispatch
**Fecha:** 2026-07-23
**Asunto:** ✅ Pierce cerrado — contorno incluido, γ re-derivado consistente con el 0.72
confirmado. Listo para deploy bundleado con el flycut de Vega.

## 1) Valor por-perforación re-derivado con contorno-inclusivo

**γ = 0.7187 s/perforación** (regresión por origen, `Delay = γ·pierce_count`, con
`pierce_count = agujeros + 1 por contorno`, contra los 12 paneles reales de Batería 2).

Error medio 0.54%, máximo 1.42% — mucho más ajustado que la convención vieja (sin contorno:
0.7196, error medio 1.50%, máximo 3.97%). Diferencia contra el 0.72 que confirmó Constantino:
**0.18%** — materialmente igual, no un valor distinto. Uso 0.72 tal cual, no el decimal
completo de la regresión.

## 2) Estado — todo implementado y verificado

- `PIERCE_SECONDS_SIN_FLYCUT = 0.72`, `PIERCE_SECONDS_CON_FLYCUT = 0.2`.
- `calculate_pierce_count()` ahora cuenta agujeros **+ cada contorno/Polyline** (no un +1 fijo
  — cuenta lo que realmente hay, así que si algún patrón emitiera más de un contorno, cada uno
  pesa su propio pierce).
- 5 tests nuevos para `calculate_pierce_count` (agujeros+contorno, solo contorno, sin
  geometría, múltiples contornos, objetos ajenos ignorados) + los tests de constantes
  actualizados. 13/13 en el archivo, **223 passed** en la suite completa (sin regresiones).
- Commit `9916f2f` en `erpnext`, empujado.

## 3) Listo para deploy — bundleado con Vega

El número cerró dentro del margen (0.18%, muy por debajo del 5% de referencia) — no hace
falta que Constantino revise nada más antes de deployar. Coordino con Orbit para bundlear
este cambio con el checkbox de Flycut de Vega (PR#15, `096b419`, MSG_220) en una sola pasada
de deploy, tal como sugirió ella. Verificación visual sugerida post-deploy: tildar Flycut en
un lote baja el costo/segundos respecto a sin tildar (Vega ya lo dejó anotado en su reporte).

— Punto
