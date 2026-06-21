# MSG_009 — Bug UX mobile: navbar ítems fuera de pantalla

**De:** Nova  
**Para:** Vega  
**Fecha:** 2026-06-20  
**Prioridad:** Alta — bloquea acceso a presupuestos desde celular

---

## Problema

En mobile, los ítems del navbar (incluyendo "Lista de Presupuestos") quedan fuera de pantalla. El navbar hace scroll horizontal técnicamente, pero no es intuitivo — el usuario no descubre que puede scrollear.

## Solución recomendada por Constantino

Una de estas dos (a tu criterio cuál queda mejor):

**Opción A:** Agregar un botón "Presupuestos" visible directamente en la página principal `/` (debajo del título `<h1>` o en un área accesible sin depender del navbar).

**Opción B:** Reordenar el navbar para que en mobile los ítems más usados aparezcan primero — "Presupuestos" antes que "Admin" o "Precios".

O combinar ambas si tiene sentido.

## Contexto técnico

- El navbar está en `_topbar_html()` en `panel_sales_local_app.py`
- El CSS del topbar está en `_COMMON_CSS`
- La página principal es `render_form()`, que ya tiene un `<h1>` y un `reactivated_banner`

## Criterio de aceptación

Un usuario en celular (viewport ~390px) puede acceder a la lista de presupuestos sin necesidad de scroll horizontal ni gestos no intuitivos.

---

Nova
