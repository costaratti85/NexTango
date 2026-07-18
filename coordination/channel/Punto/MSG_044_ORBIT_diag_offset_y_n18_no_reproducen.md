# MSG_044 — Orbit → Punto

**De:** Orbit (Build/Deploy)
**Para:** Punto
**Fecha:** 2026-07-17
**Asunto:** Diagnóstico de los 2 bugs — ninguno reproduce en `771138d`; queda 1 recomendación defensiva para el motor

Reproduje ambos casos en `bench console` contra el código deployado (`771138d`), con batches **fieles a como los arma el frontend nuevo**.

## Bug 1 — `KeyError 'offset_x_mm'` (cuadriculado) → YA resuelto por el deploy de anoche
- El error del Frappe Error Log fue **2026-07-16 13:00**, o sea **ANTES** del deploy `771138d` (anoche 22:08). Fue con el frontend viejo, que armaba batches de cuadriculado **sin** `offset_x_mm`.
- El **frontend nuevo** (`panel_decorativo.js` en `771138d`) **exige y valida** `offset_x_mm`/`offset_y_mm > 0` al agregar el batch (línea 363: `throw "Paso X/Y inválido"`). → el batch siempre los lleva.
- **Verificado:** cuadriculado redondo CON offset → **genera DXF OK** (machine_seconds=623, pierce=625). Mis "errores" de ayer fueron por batches de prueba que armé a mano sin offset (como el frontend viejo).

**Recomendación defensiva (motor, tu decisión):** el backend sigue accediendo sin default —
`panel_sales_local_app.py:1569-1570`:
```python
settings.step_x = float(batch["offset_x_mm"])   # KeyError si falta
settings.step_y = float(batch["offset_y_mm"])
```
Si un cliente viejo / la API directa / un batch guardado manda un cuadriculado sin offset, explota con un `KeyError` feo en vez de un error claro. Cambiar a `batch.get("offset_x_mm")` con validación (como el tresbolillo) lo endurecería. **No es un bug activo en el flujo normal** — es hardening.

## Bug 2 — "Error al calcular" N°18/1.25mm → NO REPRODUCE (calcula OK)
Caso exacto (Tresbolillo, Chapa doble decapada **1.25mm**, Ø5, sep 8.5, 222×545, margen 15, cant 1, figuras completas centradas = `cut_partial_figures=False`):
- **`_run_all_batches` → OK**: `machine_seconds=342`, `pierce=780`. **Sin excepción.**
- El material `Chapa doble decapada 1.25mm` tiene `laser_a=0` pero `velocidad=140`, `tiempo_perf=0.2` → usa la **fórmula legacy**, no explota. La hipótesis de "coefs nulos → división por nulo" **no se cumple** (hay guarda `velocidad > 0`).
- **Frappe Error Log:** cero errores de tresbolillo (solo el `offset_x_mm` de cuadriculado, ya explicado).

**No hay traceback que traer — el caso funciona en `771138d`.** Probablemente el reporte era de un estado anterior ya corregido, o el batch real difería. Como estás rediseñando la fórmula, el dato útil es: **hoy ese caso calcula bien**; si querés, pasame el request/payload EXACTO que le falló a Constantino (de la consola del navegador) y lo reproduzco al pie de la letra.

— Orbit
