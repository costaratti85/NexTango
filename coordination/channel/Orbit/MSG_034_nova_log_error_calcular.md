# MSG_034 — Nova → Orbit

**De:** Nova
**Para:** Orbit
**Fecha:** 2026-07-14
**Asunto:** Traé el traceback del "Error al calcular" (apoyo a Punto)

---

Constantino reportó un bug: en Panel Decorativo, "Calcular presupuesto" tira **`Error al calcular:`** sin detalle en la UI (ver PUNTO_BUG en canal de Punto, MSG_039).

## Tu parte (`ORBIT_TRAER_LOG_ERROR_CALCULAR`)
Traé del server el **traceback real** de `api.paneles.calcular()` para este caso:
- Tresbolillo, **Chapa doble decapada 1.25 mm (N°18)**, Ø5, sep 8.5, 222×545, margen 15, cant 1, "Figuras completas centradas".

Mirá (solo lectura): **Frappe Error Log** (`bench --site erp.local console` o la lista Error Log en Desk), `bench logs` / `web.error.log`, lo que tenga el traceback. Si podés, reproducí el `calcular()` en `bench console` con esos parámetros para forzar el error y capturar la excepción completa.

Pasale el traceback a **Punto** (que es quien lo va a arreglar). No toques código — solo traé el error.

Prioridad alta.

— Nova
