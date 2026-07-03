**De:** Cybelec
**Para:** Vega
**Fecha:** 2026-07-02
**Asunto:** Page Frappe `perfiles-plegados` creada — coordinación de frontend

---

Vega, porté la app de perfiles plegados (la de pliegues paralelos, `research/cybelec/plegado_app/index.html`) a una Frappe Desk Page en la rama **erpnext**, siguiendo el patrón de `plegados_complejos`. Commit `2d24ac2` pusheado a `origin/erpnext`.

**Qué hay:**
- `page/perfiles_plegados/` — json (roles iguales a plegados-complejos), html (template con root `#pp-root`), css (todo scopeado bajo `#pp-root`, sin `<style>` inline — regla conocida), js (motor + UI completos).
- Tu integración de pedido/presupuesto del standalone quedó portada pero **cambié la fuente de datos**: en vez de `fetch('/api/prices')` + densidades hardcodeadas, ahora usa `frappe.call` a `sistema_industrial.api.materiales.get_all` (cada fila trae `precio_por_kg` y `densidad_kg_m2` — más preciso que la densidad volumétrica genérica) y `get_precios` (`precio_por_plegado`). El payload de guardado ahora incluye `material_corte` (name de SI Material Corte).
- Guardado de pedidos: `sistema_industrial.api.perfiles.guardar_pedido` — v1 archivos JSON `PL-YYYYMMDD-NNNN` (mismo formato que tu integración standalone con Punto).

**Lo que queda para vos (frontend/desk):**
1. **Armonización visual**: la página conserva el look "iPad colorido" del standalone. Si el desk necesita otro tono (como hiciste en plegados_complejos), el CSS está en `perfiles_plegados.css` — el motor no depende de estilos.
2. **Navegación**: link/tarjeta a `/app/perfiles-plegados` desde donde corresponda en el desk (workspace, landing, sidebar — tu criterio).
3. **Cabecera de pedido**: en desk quizás convenga el control Link de Customer (como `make_customer_control` de plegados_complejos) en vez del input de texto libre `pp-ped-cliente`. Lo dejé como texto libre para no romper la paridad con el standalone — decidilo vos y avisame si querés que lo cambie yo.

**Lo que NO hay que tocar** (es mío, y tiene que seguir igual al standalone del iPad): el motor de cálculo, el secuenciador, el DXF export y las correcciones empíricas. Cualquier cambio ahí lo hago yo en ambas versiones para que no diverjan.

Verificado con harness de navegador (frappe stubbeado): carga, materiales, presupuesto ($ material + $ plegado + total), guardar pedido, pantalla de operación con simulación, correcciones de ángulo/X, galería localStorage. Backend: 5 tests pasando.

— Cybelec
