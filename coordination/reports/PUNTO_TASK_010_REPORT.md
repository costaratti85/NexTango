# PUNTO_TASK_010 — Recursos consumidos por pieza individual

**Agente:** Punto (UI)
**Fecha:** 2026-06-15
**Estado:** COMPLETADO

## Qué se hizo

Se reemplazó el bloque de "Recursos consumidos" en `render_form()` para mostrar los recursos
**por pieza individual** en lugar de totales del pedido completo.

### Archivo modificado

`apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`

### Cambios en la lógica (bloque Python server-side, ~líneas 880–970)

- **Antes:** un solo panel que sumaba todos los recursos del lote (`_total_kg`, etc.)
- **Ahora:** un bloque por tipo de panel, con valores divididos por `quantity`:
  - `material_kg / quantity` → kg / pieza
  - `machine_seconds / quantity` → tiempo / pieza
  - `pierce_count / quantity` → perforaciones / pieza
  - `consumibles_used / quantity` → consumible / pieza

### Formato visual

```
Panel: Tresbolillo 500×300 mm  (×3 unidades)
  Material:        1.250 kg / pieza
  Tiempo maq.:     2 min 15 s / pieza
  Perforaciones:   42.0 / pieza
  Consumible:      0.0210 u / pieza
```

- Si hay 2+ tipos de panel con datos, aparece una fila de total al pie:
  `Total del pedido: X.XX kg — Y min ZZ s — N perforaciones`
- Si `consumed_resources` es null para un tipo, se muestra el aviso
  de material faltante específico para ese tipo (con nombre y espesor).
- Si todos los tipos son null, se muestra solo el bloque de advertencia
  (sin título "Recursos consumidos").

### CSS agregado

Cuatro clases nuevas dentro del `<style>` de `render_form()`:
- `.consumed-type-block` — borde izquierdo azul por sección
- `.consumed-type-block.consumed-warn` — variante amarilla para null
- `.consumed-type-header` — encabezado de tipo de panel
- `.consumed-qty-badge` — texto gris `(×N unidades)`
- `.consumed-total-row` — fila de totales separada por línea superior

## Tests

- 28 tests unitarios existentes: todos pasan sin modificación
- Tests con `tmp_path` (fixture de pytest) fallan por `PermissionError` de Windows
  en el directorio temporal del sistema — **pre-existente, no relacionado con este cambio**
- Validaciones manuales adicionales con mock:
  - 3 paneles iguales → muestra `1.250 kg / pieza` (no `3.750`)
  - 2 tipos mixtos → cada uno muestra sus recursos individuales + total al pie
  - Todo null → aviso específico por tipo, sin total
  - Mixto (uno con datos, uno null) → muestra datos donde hay, aviso donde falta

## Criterios de aceptación

- [x] 3 paneles del mismo tipo → se muestra el valor por pieza (no el total del lote)
- [x] Cada tipo de panel tiene su propia sección con nombre y dimensiones
- [x] Material faltante muestra aviso específico para ese tipo
- [x] Total del pedido aparece al pie solo si hay 2+ tipos con datos
- [x] Tests existentes siguen pasando
