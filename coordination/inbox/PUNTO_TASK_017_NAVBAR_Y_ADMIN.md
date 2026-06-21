# PUNTO_TASK_017 — Navbar uniforme en todas las páginas + limpiar admin

**De:** Nova  
**Para:** Punto  
**Fecha:** 2026-06-17  
**Prioridad:** Alta

---

## Contexto

El usuario reporta dos problemas visuales:

1. La barra superior no es consistente entre páginas (en algunas los links están alineados a la izquierda, en otras a la derecha, falta algún botón, etc.)
2. La página de administración de parámetros muestra la tabla de materiales debajo de los parámetros — eso no corresponde ahí, para eso existe el link "Tabla de materiales" en el nav.

---

## La barra correcta (referencia: captura del usuario)

```
SistemaIndustrial   Paneles Decorativos   [ADMIN]   Tabla de materiales   Precios diarios   Presupuestos   Volver al catálogo
```

- Logo/nombre a la izquierda
- Todos los links a la derecha
- El botón `ADMIN` es un pill/badge, no un link de texto plano
- Orden fijo: ADMIN → Tabla de materiales → Precios diarios → Presupuestos → Volver al catálogo

Esta barra debe ser **idéntica** en todas las páginas que tienen topbar admin:
- `/` (catálogo / galería de patrones)
- `/admin`
- `/materiales`
- `/precios`
- `/presupuesto`
- Cualquier otra que exista

---

## Cambio 1: Unificar el topbar

Actualmente hay al menos `_TOPBAR_ADMIN_HTML` y posiblemente otros strings de navbar definidos por separado en distintas funciones de render. Unificar todo en una sola constante o función que genere el HTML del topbar, y usarla en todas las páginas.

**No cambiar** el contenido de las páginas — solo el topbar.

---

## Cambio 2: Quitar la tabla de materiales de la página admin

La página `/admin` (administración de parámetros) actualmente muestra la tabla de materiales debajo del formulario de parámetros. Ese bloque debe ser removido. El usuario accede a la tabla de materiales desde el link "Tabla de materiales" en el nav.

---

## Criterio de aceptación

1. Todas las páginas tienen el mismo topbar, con los mismos botones, en el mismo orden y alineación
2. La página `/admin` ya no muestra la tabla de materiales
3. Tests existentes siguen pasando

## Reportar en

`coordination/reports/PUNTO_TASK_017_REPORT.md`
