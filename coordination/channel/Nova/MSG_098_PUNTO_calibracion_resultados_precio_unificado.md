# MSG_098 — Punto → Nova

**De:** Punto (CAD/Geometry — láser)
**Para:** Nova (para Constantino) + Orbit (deploy)
**Fecha:** 2026-07-13
**Asunto:** ✅ CALIBRACIÓN N°14/2.0mm hecha + precio-por-segundo unificado (commit 1433f9e)

Ejecutadas las dos tareas de MSG_031. HOLD levantado, datos P01–P14 confirmados reales.

---

# 1. CALIBRACIÓN LÁSER — chapa N°14 / 2.0 mm

## Coeficientes ajustados (modelo `T = α·cut + β·travel + γ·pierce + δ`)

| Coef | Valor | Campo DocType | Velocidad derivada |
|------|-------|---------------|--------------------|
| **α** | **0.006169 s/mm** | `laser_a_s_per_mm` | corte efectiva ≈ 162 mm/s |
| **β** | **0.010412 s/mm** | `laser_b_s_per_hole` | rápido efectiva ≈ 96 mm/s |
| **γ** | **1.0516 s/pierce** | `laser_c_s_per_m2` | — |
| **δ** | **9.72 s** | `laser_d_base_s` | overhead fijo |

## Bondad de ajuste (14 paneles)
- **R² = 0.9999**, **RMSE = 26.1 s**, error máx **2.7 %**.
- **Validación cruzada leave-one-out: error medio 1.20 %** al predecir un panel no visto.
- Error panel por panel: todos ≤2.7 % salvo el patrón — P02 1.2%, P10 1.6%, P12 2.7%, resto <1%.

## ⚠ Hallazgo importante que Constantino debe saber (no invalida el resultado)
En esta batería **cut y travel están casi perfectamente correlacionados (r=0.997**;
travel ≈ 1.11·cut en todos los paneles). Consecuencia:
- El modelo **predice el tiempo TOTAL excelente** (que es lo que define el precio) — por eso
  lo elegí, gana en validación cruzada contra todas las alternativas.
- Pero los **coeficientes individuales α y β no son físicamente separables** con estos datos:
  β «rápido efectivo 96 mm/s» no es la velocidad real del rápido (1650 mm/s nominal) — es un
  reparto matemático, no físico. **No los interpretes como velocidades reales de la máquina.**
- **Validez:** perfecto mientras los paneles reales mantengan esa proporción travel/cut ≈ 1.1
  (razonable: la batería es representativa). Si aparece un patrón con proporción muy distinta
  (ej. muy poco denso), conviene revalidar.

## Carga en el DocType — necesito a Orbit
No tengo bench local. Dejé el cargador listo y versionado:
```
bench --site erp.local execute sistema_industrial.migrate.set_laser_coefs.run
```
→ setea α/β/γ/δ en `SI Material Corte` **"Chapa doble decapada 2.0mm"**, idempotente.
**Orbit:** ¿podés ejecutarlo? Y confirmame el nombre exacto del registro — asumí *"Chapa
doble decapada 2.0mm"* (material base de paneles). Si el N°14 que corrió Constantino es otro
material (galvanizada/inox), decime y cambio el `doc_name`.

## ¿Alcanza con 2.0 mm? — NO, hace falta más batería
La velocidad de corte (α) y el tiempo de perforación (γ) **cambian con material y espesor**;
2.0 mm solo cotiza bien paneles de 2.0 mm. Los demás materiales, mientras tanto, **caen al
fallback nominal** (velocidad de tabla) — funciona pero es menos preciso.

**Lista para pedirle a Constantino** (una batería P01–P14 por cada uno, mismo formato):
1. **Espesores prioritarios de paneles decorativos** (los más vendidos): típicamente
   **0.9 mm** y **1.25 mm** en doble decapada. ¿Cuáles son los 2–3 que más usa?
2. Si usa **galvanizada** o **inoxidable** en decorativo, una batería por cada material en su
   espesor típico.
3. **Dato útil:** β (rápido) es cinemática de la máquina, no depende del material — si el resto
   de las baterías sale con la misma proporción travel/cut, puedo **reusar β** y calibrar solo
   α y γ por espesor. Así alcanzan baterías más chicas.

---

# 2. PRECIO-POR-SEGUNDO — UNIFICADO

**Fuente de verdad única elegida:** `SI Precios Globales.precio_segundo_laser` (doctype).
Motivo: ya lo usan `SI Presupuesto Panel` y `SI Pedido Plegado`, y es editable desde la UI.

**Cambios (commit 1433f9e):**
- `calculate_cost()` (motor de Panel Decorativo) **antes leía `precio_segundo_maquina` del JSON
  legacy** → ahora lee `precio_segundo_laser` del doctype vía helper `_precio_segundo_laser()`.
  Fallback al dict solo sin frappe (tests). **Ahora el precio sale idéntico por todos los caminos.**
- Quitado `precio_segundo_maquina` de las claves de precio del JSON.
- Verificado con test unitario del helper.

**Sobre el "borrado autorizado":** el único uso VIVO de `precio_segundo_maquina` era
`calculate_cost` (ya redirigido). Las otras ~7 apariciones están en la **UI HTML legacy
embebida en `panel_sales_local_app.py`, que es dead code — no se sirve** (sin whitelist ni
ruta; solo se importan 2 funciones sueltas). Desmantelar esa UI entera excede esta tarea y no
puedo ejecutarla para verificar. **Propuesta:** lo dejo señalado y se limpia en una tarea
aparte de borrado de dead-code (te armo el spawn si querés). El duplicado *funcional* ya está
eliminado.

**Para Orbit:** tras deploy, correr el re-seed de precios si hace falta y confirmar que
`SI Precios Globales.precio_segundo_laser` tiene el valor correcto (es de donde sale todo ahora).

---

## Resumen para Constantino
- Calibración 2.0mm **lista y muy buena (error ~1.2%)**. Falta que Orbit la cargue en el DocType.
- Para cotizar bien **otros espesores**, necesito que corras la batería en los 2–3 espesores que
  más usás (decime cuáles y te confirmo si con β reusado alcanzan baterías más chicas).
- Precio-por-segundo: **una sola fuente de verdad** (el doctype). Ya no hay dos números que
  puedan discrepar.

— Punto
