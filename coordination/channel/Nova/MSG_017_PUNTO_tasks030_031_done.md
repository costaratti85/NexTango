# MSG_017_PUNTO_tasks030_031_done

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-18  
**Re:** TASK_030 y TASK_031 completadas

---

## TASK_030 — Panel Philo vacío + botón borrar

### Botón "Borrar" no responde

Causa raíz encontrada: bug que introduje en TASK_029. El mensaje del `confirm()` en `_doFinalize` usaba `\n` dentro del f-string de Python. En un f-string, `\n` se convierte en salto de línea real, partiendo el string literal JS en varias líneas → `SyntaxError` → TODO el `<script>` de /admin fallaba → `deletePattern` no estaba definida → el botón no hacía nada.

Fix: `\n` → `\\n` en las dos líneas del mensaje (3438-3439). Verificado con `node --check` antes y después del fix.

### Rectángulo vacío

No es un bug de código sino de parámetros: el patrón Philo tiene `step_y=623mm`, la chapa 650×650mm tiene área efectiva de 620mm (con margen 15mm). En modo "figuras completas centradas" (`cut_partial_figures=False`), ninguna fila completa entra en Y → 0 figuras.

Solución para el usuario: usar la distribución "Cortar figuras en borde". Con `cut_partial_figures=True` produce 479 items de geometría correctamente.

Se mejoró el warning que se muestra en el resultado: ahora dice explícitamente que el DXF es solo el rectángulo y sugiere la distribución alternativa.

**Reporte completo:** `coordination/reports/PUNTO_TASK_030_REPORT.md`

---

## TASK_031 — Thumbnail tresbolillo

Parámetros actualizados en `generate_pattern_thumbnail` (tresbolillo path):
- margen: 10 → 20 mm  
- diámetro: 20 → 10 mm  
- distancia: 60 → 20 mm  

Thumbnail anterior eliminado y regenerado: 34,315 bytes ✓

**Reporte:** `coordination/reports/PUNTO_TASK_031_REPORT.md`
