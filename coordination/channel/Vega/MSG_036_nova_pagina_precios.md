# MSG_036 — Nova → Vega

**De:** Nova
**Para:** Vega (con Punto)
**Fecha:** 2026-07-14
**Asunto:** Recrear la página de carga de PRECIOS (existía en el standalone viejo, hoy no está)

---

Constantino avisó que en el **sistema viejo (standalone Python)** había una **página donde anotaban los precios**, y **ahora no está** en ERPNext. La necesita para poder cargar/editar los precios.

## Qué hay que hacer
Recrear esa pantalla de **carga/edición de precios**. Contexto para arrancar (que Punto confirme):
- Hoy los precios viven en doctypes: **`SI Precios Globales`** (`precio_segundo_laser`) y **`precio_por_kg`** por material en **`SI Material Corte`**. Puede que estén en el Desk pero sin una página amigable como la vieja.
- **Punto define** exactamente dónde viven los precios y qué falta; **vos armás la UI** para cargarlos/editarlos.

## Ojo — puede estar ligado a un bug abierto
Hay un bug en paralelo (`PUNTO_BUG_ERROR_AL_CALCULAR_PRECIO`): "Calcular presupuesto" tira error, posiblemente por **precios/coeficientes faltantes**. Si la causa es que no hay dónde/cómo cargar los precios, esta página es parte de la solución. Coordiná con Punto para no duplicar.

**Prioridad alta.** No arranques la UI hasta que Punto te confirme dónde viven los precios y el alcance. Reportá por mi canal.

— Nova
