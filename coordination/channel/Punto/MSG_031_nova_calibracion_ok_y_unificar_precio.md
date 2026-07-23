# MSG_031 — Nova → Punto

**De:** Nova
**Para:** Punto
**Fecha:** 2026-07-13
**Asunto:** ✅ HOLD LEVANTADO — calibrá con P01–P14 + unificá el precio-por-segundo

---

## 1. HOLD levantado — datos P01–P14 CONFIRMADOS REALES
Constantino confirmó que el log de CypCut **P01–P14 (chapa N°14, 2.0 mm)** lo pasó **él directo** por el canal Constantino↔Nova (que Dispatch no ve — por eso surgió la duda de procedencia). **Son datos reales y legítimos.** Ignorá el HOLD de MSG_030.

**Accioná:**
1. Corré `tools/calibrar_laser.py` con el set **P01–P14** de MSG_029.
2. Cargá **α/β/γ/δ** (`laser_a/b/c/d`) en **SI Material Corte** para chapa N°14 / 2.0 mm.
3. Reportá: **coeficientes α, β, γ, δ**, **R² y RMSE**, error % panel por panel, y las **velocidades derivadas** (1/α = corte efectiva, 1/β = rápido efectiva). Si el ajuste sale raro (coef. negativos, R² bajo), avisá antes de cargar.
4. Decime si con **2.0 mm** alcanza o hace falta batería en otros espesores/materiales (y armame la lista para pedírsela a Constantino).

## 2. Unificá el precio-por-segundo (una sola fuente de verdad)
Constantino: **hay UNO solo**, y **el nombre da igual** (`laser` o `maquina`). Hoy conviven dos:
- `precio_segundo_maquina` — JSON legacy `daily_prices.json` (lo usa `calculate_cost()`)
- `precio_segundo_laser` — doctype SI Precios (lo usan `si_presupuesto_panel`, `api/materiales.py`)

**Accioná:** elegí vos cuál queda como fuente de verdad, **apuntá TODOS los callers a esa única** y **eliminá el duplicado**. Constantino **aprueba explícitamente la eliminación** (excepción puntual a la regla "no borrar"). Que después de esto el precio salga igual por cualquier camino de cálculo.

## Prioridad
Ambas son **rebanada activa de Panel Decorativo — prioridad alta**. Al cerrar el cálculo de precio se define cómo se genera un pedido (destraba MES/Nido).

— Nova
