# PUNTO_TASK_030 — Panel Philo rectángulo vacío + botón borrar

**Fecha:** 2026-06-18  
**Estado:** Completada

---

## Diagnóstico

### Bug A — Botón "Borrar" no responde en /admin

**Causa raíz:** En la implementación de TASK_029 (función `_doFinalize` en el JS de la página admin), el mensaje del `confirm()` dialog usaba `\n` dentro del f-string de Python. En un f-string, `\n` se renderiza como salto de línea real — no como la secuencia de escape JS `\n`. Resultado: el bloque `<script>` tenía un string literal JS partido en varias líneas, causando un `SyntaxError` que impedía que TODO el script cargara (incluyendo `deletePattern`).

**Fix:** Reemplazar `\n` por `\\n` en las líneas 3438-3439 de `panel_sales_local_app.py`.

Verificado con `node --check`: script sin errores después del fix.

---

### Bug B — Rectángulo vacío en panel Philo

**Causa raíz:** El modo de distribución por defecto en el formulario es "Figuras completas centradas" (`cut_partial_figures=False`). El patrón Philo tiene `step_y=623mm`. Una chapa de 650×650mm con margen 15mm tiene área efectiva de 620mm en Y. Como 623 > 620, **no entra ni una fila completa** de figuras → el motor genera solo el rectángulo de la chapa (pierce_count=0).

Esto se resuelve usando la distribución "Cortar figuras en borde" (`cut_partial_figures=True`), con la que salen 479 items de geometría correctamente.

**Fix:** Se mejoró el mensaje de advertencia que aparece en el resultado cuando `pierce_count=0` y `geometry_item_count<=1`:
- Antes: `"Legacy engine returned pierce_count=0; preserving legacy value."` (texto técnico e incorrecto)
- Después: mensaje claro que explica que el DXF es solo el rectángulo, y recomienda cambiar la distribución o ajustar el tamaño de chapa.

---

## Cambios realizados

**`apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`:**

1. Líneas 3438-3439: `\n` → `\\n` en el confirm dialog de `_doFinalize` (fix JS syntax error)
2. Líneas 1463-1471: warning de pierce_count=0 mejorado con detección de panel vacío

---

## Para Constantino

Para generar un panel Philo en una chapa 650×650mm:
- Seleccioná la distribución **"Cortar figuras en borde"** antes de generar.
- Alternativamente, usá una chapa más grande (≥700mm en alto) para que el paso de 623mm entre sin cortar.
