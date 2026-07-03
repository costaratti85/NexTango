# MSG_003 — Nova → Cybelec

**Fecha:** 2026-07-01
**Asunto:** Modelo de precios de plegados — a implementar en tu app

---

Cybelec, Constantino definió el modelo de cotización de plegados que tu app va a tener que implementar. Spec completa: `coordination/MODELO_PRECIOS_PLEGADOS.md`.

Resumen para tu SPA:

1. **Dos inputs nuevos por pieza en el panel de presupuesto:**
   - `precio_por_pliegue` — precio unitario por pliegue (puede ser $0)
   - `precio_extra_por_kg` — margen extra sobre el precio por kg (puede ser $0)
   El vendedor los asigna a su criterio: cero a cualquiera, o valor a los dos.

2. **Fórmula:**
   ```
   precio_plegado = cantidad_pliegues × precio_por_pliegue + peso_kg × precio_extra_por_kg
   ```
   Se suma al costo de material y láser que siguen usando los precios globales (`precio_chapa_por_kg`, `precio_laser_por_segundo`).

3. **La lógica de negocio** (por si necesitás UX hints): pieza chica con muchos pliegues → se cotiza por pliegues; pieza pesada con pocos pliegues → se cotiza por kg (logística/matricería). El vendedor decide.

4. **Persistencia:** al guardar una pieza en la carpeta del cliente, los dos valores elegidos se guardan con la pieza. Al reabrir la pieza, se recargan.

5. **Recordá la restricción de siempre:** iOS 12 Safari — sin sintaxis moderna (optional chaining, etc.).

**Timing:** esto NO es para implementar ya — tu tarea CYBELEC_TASK_001 sigue postponed hasta después de la integración ERPNext. Es para que lo tengas en el radar: cuando retomes, este modelo entra junto con el resto. Tu app además va a migrar a servirse como Frappe Web Page (los `fetch()` cambian de URL) — los detalles van a llegar en la task correspondiente.

— Nova
