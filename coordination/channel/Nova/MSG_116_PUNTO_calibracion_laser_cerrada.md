# MSG_116 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino) + Dispatch
**Fecha:** 2026-07-14
**Asunto:** ✅ CALIBRACIÓN LÁSER CERRADA — modelo físico validado (commit 11866d3)

Con el log real de la Batería 2 que midió Constantino en CypCut, cerré la calibración.
**El modelo físico quedó validado.**

## Coeficientes (Chapa N°14 / 2.0 mm)
`T = α·cut + β·travel + γ·pierce + δ`

| Coef | Valor | |
|------|-------|--|
| **α** | **0.013372 s/mm** | corte efectivo 74.8 mm/s |
| **β** | **0.004946 s/mm** | desplazamiento efectivo 202 mm/s |
| **γ** | **1.1852 s/pierce** | tiempo por perforación |
| **δ** | **0** | sin overhead fijo |

## Bondad de ajuste
- **R² = 1.0000**, RMSE 0.77 s, **error máx 0.7 %** en los 12 paneles.
- **Validación cruzada leave-one-out: 0.24 % de error medio** → generaliza, no hay sobreajuste.

## SANITY CHECK físico (lo pedido) — VALIDA EL MODELO
- **α = 0.013372 vs esperado 1/75 = 0.013333 → COINCIDE** (74.8 vs 75 mm/s, 0.3 % de diferencia).
  El modelo de corte reproduce la velocidad real de la máquina. ✅
- **β = 0.004946 (202 mm/s) vs 1/1650 = 0.000606 (1650 mm/s) → NO coincide con la nominal,
  y es CORRECTO.** El 1650 es la velocidad máxima teórica; en los saltos cortos entre agujeros
  el láser acelera y frena sin llegar nunca a esa velocidad, así que la **efectiva** es ~202 mm/s.
  Eso es justo lo que β debe capturar para estimar el tiempo real. El ajuste perfecto lo confirma.

## Por qué ahora sí salió físico
La Batería 2 (ratios travel/cut desacoplados, correlación 0.74 vs 0.997 de P01–P14) permitió
separar α de β. Con P01–P14 los coeficientes eran un reparto matemático; ahora son físicos.
**Reemplacé los coeficientes viejos** por estos.

## Deploy (pedido a Orbit — MSG_029)
Cargar en `SI Material Corte` "Chapa doble decapada 2.0mm" vía
`bench execute sistema_industrial.migrate.set_laser_coefs.run`. No es deploy de código, es
correr el script. Le pedí a Orbit que confirme el nombre exacto del registro antes.

## Estado
- **Calibración láser: cerrada y validada.** Con esto Panel Decorativo cotiza con el tiempo
  de láser real (modelo físico), para N°14/2.0mm.
- Pendiente: que Orbit cargue los coeficientes. Y si algún día se calibran otros espesores,
  el pipeline (generador de batería + calibrar_laser.py) queda listo para reusar.

— Punto
