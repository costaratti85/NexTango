# VEGA_TASK_003 — Actualizar wireframes con decisiones de Constantino

**De:** Nova  
**Para:** Vega  
**Fecha:** 2026-06-13  
**Prioridad:** Baja — los wireframes son referencia, no bloquean nada  
**Archivos a modificar:**
- `coordination/wireframes/panel_gallery_main.html`
- `coordination/wireframes/panel_gallery_admin.html`

---

## Contexto

Vega identificó 4 divergencias entre los wireframes entregados y las decisiones implementadas. Esta tarea las corrige para que los wireframes sigan siendo una fuente de verdad confiable.

---

## Correcciones requeridas

### 1. Tresbolillo — params al paso 1 (CRÍTICA)

En `panel_gallery_main.html`, el bloque condicional `#block-tresbolillo` con campos de diámetro y distancia está en el paso 3.

**Nuevo comportamiento:** Al seleccionar la card de Tresbolillo en el paso 1, aparece un bloque inline debajo de la grilla (dentro del paso 1) con:
- Campo: Diámetro agujero mm
- Campo: Distancia entre centros mm  
- Botón: "Confirmar patrón →"

Recién al confirmar se avanza al paso 2. Para patrones DXF, el click en la card sigue avanzando directo al paso 2.

El bloque de tresbolillo en el paso 3 debe ser eliminado.

### 2. Offset DXF — solo en admin, no en el flujo del vendedor (CRÍTICA)

En `panel_gallery_main.html`, el paso 3 tiene un bloque condicional `#block-dxf-offset` con Offset X/Y visibles para el vendedor.

**Nuevo comportamiento:** El vendedor no ve ni toca el offset. Los campos existen como `<input type="hidden">` y se cargan automáticamente al seleccionar el patrón. Eliminar el bloque condicional visible del paso 3.

### 3. Admin — eliminar visibilidad/cliente (MENOR)

En `panel_gallery_admin.html`:
- Quitar columna de visibilidad de la tabla de patrones
- Quitar badges Público/Privado
- Quitar el bloque condicional de asignación por código de cliente del formulario

### 4. Link al admin — misma pestaña (MENOR)

En `panel_gallery_main.html`, el link o botón que abre el admin tiene `target="_blank"`. Quitarlo — el admin vive en la misma pestaña en `/admin`.

---

## Criterio de aceptación

Los wireframes HTML estáticos abren en el browser y reflejan fielmente el flujo actualmente implementado. No hace falta funcionalidad JS — solo que la estructura visual sea correcta.

---

## Reportar en

`coordination/reports/VEGA_WIREFRAME_SYNC_REPORT.md` — una línea por corrección confirmada.
