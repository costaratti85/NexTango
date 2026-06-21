# PUNTO_TASK_035 — Posicionamiento del origen del patrón

**Fecha:** 2026-06-19  
**Estado:** Completada

---

## Diagnóstico

El bug estaba en `generate_centered_full_mode_geometry()` en `main.py`.

### Código anterior (buggy)

```python
cols = int((usable_width - pattern_width) / step_x) + 1
occupied_width = pattern_width + (cols - 1) * step_x
start_x = margin + (usable_width - occupied_width) / 2 - bbox.min_x  # BUG
start_y = margin + (usable_height - occupied_height) / 2 - bbox.min_y  # BUG
```

El término `- bbox.min_x` desplazaba el origen del patrón por la extensión negativa del bbox,
para forzar que el **borde del bbox** (no el origen del patrón) quedara en el margen.

Para el tresbolillo con `radius=25mm`: `bbox.min_x = -25`, entonces `- bbox.min_x = +25mm` →
el primer tile se posicionaba 25mm más a la derecha de lo que la regla define.

### Modo cut: ya era correcto

`generate_cut_mode_geometry()` usa `dx = margin + col * step_x` → para col=0: origen en
`(margin, margin)` exactamente. ✓

Philo con figuras en X negativo: 110 figuras parcialmente fuera del borde izquierdo,
correctamente clipeadas por `PolylineClipper`. ✓

---

## Fix aplicado

**Archivo:** `Programas_hechos/Panel Decorativo/main.py`  
**Función:** `generate_centered_full_mode_geometry()` (antes líneas 271-312)

```python
# Guardia basada en step (no en bbox)
if step_x > usable_width or step_y > usable_height:
    return output_items

# Conteo de tiles basado en step_x/step_y (no en pattern_width)
cols = int(usable_width / step_x)
rows = int(usable_height / step_y)

# Espacio entre primers y último origen (no extensión visual del bbox)
occupied_width = (cols - 1) * step_x
occupied_height = (rows - 1) * step_y

# Sin corrección por bbox.min — el origen (0,0) queda en la posición de centrado
start_x = margin + (usable_width - occupied_width) / 2
start_y = margin + (usable_height - occupied_height) / 2
```

---

## Comparación de resultados: tresbolillo 600×650mm, margin=20

| | Antes (buggy) | Después (fix) |
|---|---|---|
| `cols` | 4 | 3 |
| `start_x` primer tile | 45.41mm | 154.52mm |
| Borde izquierdo de figura | 20.41mm ≈ xmin ✓ | 129.52mm (figuras centradas con holgura) |
| Borde derecho de figura | 579.59mm ≈ xmax | 543.22mm < xmax ✓ |
| `bbox.min_x` aplicado a start_x | SÍ (+25mm extra) | NO ✓ |

Con el fix: todas las figuras dentro del área efectiva, origen del patrón en la posición
de centrado sin corrección por bbox.

---

## Verificación

- Cut mode: sin cambios, ya correcto
- Centered mode: `- bbox.min_x` eliminado, `cols` ahora basado en step
- Guardia de "patrón demasiado grande" ahora usa `step_x > usable_width` (correcto conceptualmente)
- Tests: 50 passed (9 errores pre-existentes de permisos Windows en carpeta temp)
