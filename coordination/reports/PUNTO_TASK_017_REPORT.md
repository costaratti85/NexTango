# PUNTO_TASK_017_REPORT — Navbar uniforme + limpiar admin

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-17  
**Estado:** Completada

---

## Cambios realizados

### 1. Topbar unificado

Eliminé `_TOPBAR_MAIN_HTML` y `_TOPBAR_ADMIN_HTML` (dos constantes inconsistentes) y las reemplacé con una única función `_topbar_html(active: str = "")`.

La barra resultante es idéntica en todas las páginas:

```
SistemaIndustrial   Paneles Decorativos   [ADMIN]   Tabla de materiales   Precios diarios   Presupuestos   Volver al catálogo
```

- Logo a la izquierda
- Spacer flex empuja todo lo demás a la derecha
- "Paneles Decorativos" en `<nav>` (estilo link de sección)
- `[ADMIN]` como pill/badge clickeable que lleva a `/admin`
- "Tabla de materiales", "Precios diarios", "Presupuestos" como admin-links con borde
- "Volver al catálogo" como back-link
- La página activa queda marcada con `.active` (resaltado)

**Páginas actualizadas:**
| Página | `active` |
|---|---|
| `/` (galería) | `"home"` |
| `/admin` | `"admin"` |
| `/materiales` | `"materiales"` |
| `/precios` | `"precios"` |
| `/presupuesto` | `"presupuesto"` |

También agregué CSS faltante: `text-decoration:none` en `.admin-badge`, hover effect, y `.topbar .admin-link.active` para el resaltado en páginas secundarias.

### 2. Tabla de materiales removida de /admin

El bloque completo fue eliminado:
- Python: loading de `mat_entries`, construcción de `mat_rows_html`, variable `mat_count`
- HTML: card "Tabla de materiales" (tabla con filas) + card "Agregar material" (formulario)

La funcionalidad sigue disponible en `/materiales`, accesible desde el nav.

---

## Tests

- `test_render_admin_does_not_contain_material_table_section` — nuevo test, pasa ✓
- `test_render_admin_contains_material_table_section` — eliminado (testeaba comportamiento intencional)
- 28 tests restantes de `test_panel_sales_local_app.py` — todos pasan ✓
- Los 4 ERRORs del suite son por `tmp_path` de pytest en Windows (problema preexistente, no relacionado con esta tarea)

---

## Archivo modificado

`apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`
