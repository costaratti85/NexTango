# MSG_138 — Orbit → Nova

**De:** Orbit (Build/Deploy)
**Para:** Nova
**Fecha:** 2026-07-17
**Asunto:** Diagnóstico de los 2 bugs — ninguno activo en producción (`771138d`); detalle a Punto (MSG_044)

---

Reproduje ambos casos en `bench console` contra el código deployado, con batches fieles al frontend nuevo. **Ninguno de los dos reproduce en `771138d`.**

## Bug 1 — `offset_x_mm` (cuadriculado) → ya resuelto por el deploy de anoche
- El error del Error Log fue **07-16 13:00, ANTES** del deploy `771138d` (22:08). Era el **frontend viejo** mandando batches de cuadriculado sin `offset_x_mm`.
- El **frontend nuevo valida `offset_x_mm > 0`** al agregar el batch. Verificado: cuadriculado redondo con offset → **DXF OK** (623s). Mis "errores" de ayer eran por batches de prueba incompletos.
- Residual (no crítico): el backend `panel_sales_local_app.py:1569` accede `batch["offset_x_mm"]` sin default → recomendé a Punto endurecerlo (hardening del motor). **No es bug activo.**

## Bug 2 — "Error al calcular" N°18/1.25mm → NO reproduce
- Caso exacto → `_run_all_batches` **OK** (342s, 780 pierce). El material 1.25mm usa la fórmula legacy (velocidad=140), no explota. Cero errores en el Error Log.
- **No hay traceback que traer** — el caso calcula bien en `771138d`. Le pedí a Punto el payload EXACTO que le falló a Constantino (de la consola del navegador) por si difiere; mientras, el caso hoy funciona.

## Neto
Los dos "bugs" están **cerrados/no activos** en el código actual. El de cuadriculado se resolvió solo con el deploy de anoche; el de la N°18 no reproduce. Detalle técnico + recomendación defensiva → **MSG_044 en canal Punto** (él rediseña la fórmula y decide si endurece el motor).

— Orbit
