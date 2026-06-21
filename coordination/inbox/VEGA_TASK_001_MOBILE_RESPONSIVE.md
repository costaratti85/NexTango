# VEGA_TASK_001 — Mobile responsiveness: todas las páginas usables en ~390px

**De:** Nova  
**Para:** Vega  
**Fecha:** 2026-06-17  
**Prioridad:** Alta — sprint de paneles decorativos no se cierra sin esto  

---

## Contexto

La app corre en un servidor HTTP local Python en `panel_sales_local_app.py`. Todo el HTML/CSS está generado inline en ese mismo archivo — no hay framework CSS externo, solo estilos embebidos en f-strings. Constantino probó desde un Android (~390px) y hay dos problemas concretos.

---

## Problemas a resolver

### 1. Navbar se corta en mobile

**Archivo:** `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`  
**Función:** `_topbar_html()` (línea ~1624) y CSS en `_COMMON_CSS` (líneas ~1594–1607)

El topbar tiene en una sola fila:
- Logo "SistemaIndustrial"
- Link "Paneles Decorativos"
- Spacer flexible
- Badge "ADMIN"
- "Tabla de materiales"
- "Precios diarios"
- "Presupuestos"
- "Volver al catálogo"

No hay ningún `@media` para el topbar. En 390px todo esto desborda.

**Solución recomendada (simple, adecuada para herramienta interna):**
```css
/* mobile: topbar scrollable horizontalmente */
@media (max-width: 600px) {
  .topbar { 
    padding: 0 12px; 
    gap: 0; 
    overflow-x: auto; 
    overflow-y: hidden; 
    -webkit-overflow-scrolling: touch;
  }
  .topbar .spacer { display: none; }
  .topbar nav a, .topbar .admin-link, .topbar .back-link { 
    white-space: nowrap; 
    font-size: 12px; 
    padding: 6px 10px; 
  }
  .topbar .logo { font-size: 14px; margin-right: 8px; }
}
```

Si preferís implementar un hamburger menu colapsable con JS, también es aceptable — pero el scroll horizontal es más rápido y suficiente para una herramienta interna.

---

### 2. Página de presupuesto desborda a la derecha

**Función:** `render_presupuesto()` (línea ~4218)  
**CSS local** (líneas ~4224–4265)

Los problemas específicos:

| Elemento | CSS problemático | Fix |
|---|---|---|
| `.pres-header .meta` | `display:flex; gap:32px` — los 4 spans se van afuera | Agregar `flex-wrap:wrap; gap:8px 20px` |
| `.pres-body` | `padding:24px 28px 32px` — 28px lateral es mucho en 390px | `@media` → `padding:16px 12px 24px` |
| `.pres-table` | Sin wrapper `overflow-x` | Envolver con `<div style="overflow-x:auto">` |
| `.res-table td:first-child` | `min-width:180px` — fuerza overflow | `@media` → `min-width:100px` y `font-size:11px` |
| `.cliente-input` | `width:260px` fija — puede romperse en pantallas chicas | Cambiar a `max-width:260px; width:100%` |

---

### 3. Layout general — breakpoints faltantes

**CSS en `_COMMON_CSS`** (líneas ~1608–1621), aplicado a todas las páginas:

- `.card { padding:28px 32px }` → demasiado padding lateral en mobile → agregar `@media (max-width:600px) { .card { padding:16px 14px; } }`
- `.page-wrapper { padding:28px 20px 60px }` → el padding de 20px es razonable pero combina mal con el contenido interno
- `.form-row` ya tiene breakpoint en 700px (ok) — verificar que funcione bien

---

## Criterio de aceptación

1. La navbar es accesible en 390px — todos los links alcanzables sin que nada quede cortado visualmente fuera de viewport (scroll horizontal aceptable)
2. La página `/presupuesto` muestra la tabla completa y sin desborde horizontal — el contenido principal cabe en pantalla o tiene scroll controlado
3. Las páginas `/`, `/admin`, `/presupuestos`, `/materiales`, `/precios` son usables desde mobile (no se corta contenido, los formularios son manejables)
4. El comportamiento desktop no cambia
5. Tests existentes (`tests/test_panel_sales_local_app.py`) siguen pasando
6. Reportar en `coordination/reports/VEGA_TASK_001_REPORT.md`

---

## Nota técnica

Todo el CSS está embebido en el Python como strings — `_COMMON_CSS` se usa en todas las páginas, y cada función de renderizado tiene su propio bloque `<style>` adicional. Los cambios en `_COMMON_CSS` afectan a todas las páginas a la vez. Para CSS específico de presupuesto hay que editar el bloque `<style>` dentro de `render_presupuesto()`.

No hay build step — cambiar el `.py` y reiniciar el servidor es suficiente para probar.
