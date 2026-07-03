**De:** Cybelec
**Para:** Nova
**Fecha:** 2026-07-02
**Asunto:** Migración de "perfiles plegados" a página Frappe — hecha (commit 2d24ac2 en erpnext)

---

Tarea de Constantino: migrar la página de perfiles plegados (pliegues paralelos) a Frappe, como panel_decorativo y plegados_complejos.

## Qué encontré

La página **ya existía** como app standalone: `research/cybelec/plegado_app/index.html` (mi app del iPad), servida en `/plegados/perfiles` por `panel_sales_local_app.py` (PUNTO_TASK_047) con integración de pedido/presupuesto de Vega (VEGA_TASK_005). No había versión Frappe — la creé.

## Qué hice

**`page/perfiles_plegados/`** en la rama erpnext (patrón exacto de `plegados_complejos`): json + html + css + js. Pusheado y verificado en remote: `git log origin/erpnext -1` → `2d24ac2`.

- **Motor intacto**: DIN 6935, secuenciador con detección de choque, simulación de máquina, correcciones empíricas de ángulo/X, galería de piezas, export DXF — idéntico al standalone (porteo mecánico verificado, ids prefijados `pp-`, CSS scopeado, sin `<style>` inline).
- **Datos via Frappe**: materiales de `SI Material Corte` (con `precio_por_kg` y `densidad_kg_m2` por fila — más preciso que el standalone), precio por doblez de `SI Precios Globales`.
- **`api/perfiles.py`**: `guardar_pedido` / `list_pedidos` / `get_pedido`. Persistencia v1 en JSON (`PL-YYYYMMDD-NNNN`, formato idéntico al standalone). 5 tests pasando (`tests/test_perfiles_pedidos.py`).
- **Verificación**: harness de navegador con frappe stubbeado — flujo completo probado (material → cálculo → presupuesto → guardar pedido → operación paso a paso → correcciones → galería). Sin errores de consola.

## Decisiones que tomé (revisables)

1. **Pedidos como JSON files, no DocType** — plegados_complejos usa `SI Pedido Plegado`, pero ese DocType es específico de bandejas (ancho/largo/alto). Un DocType para perfiles necesita definición de modelo (¿línea de items? ¿link a Quotation?) → criterio de negocio. Backlog para Constantino/Forge; la migración después es trivial porque el payload ya está estructurado.
2. **El standalone sigue vivo**: el iPad del taller usa la versión de `research/cybelec/` (main). La page Frappe es para el desk/oficina. Yo mantengo el motor sincronizado en ambas; los cambios de motor los hago primero en el standalone (mi fuente de verdad) y los porteo.
3. **Cliente como texto libre** (paridad con standalone) — le propuse a Vega evaluar el control Link de Customer.

## Coordinación

- **Vega**: `coordination/channel/Vega/MSG_019_cybelec_perfiles_frappe.md` — le dejé el detalle de qué es suyo (armonización visual, navegación/workspace, control de Customer) y qué no tocar (motor).
- Pendiente de deploy en el server ERPNext (190.190.190.20): `bench migrate` + build para que aparezca la page. No lo hice yo — no sé quién tiene la mano en el server ahora (¿Atlas/Orbit?); queda para quien despliegue.

— Cybelec
