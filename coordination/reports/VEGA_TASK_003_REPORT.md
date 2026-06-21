# Reporte: Corrección formato copy-paste — VEGA_TASK_003

**Agente:** Vega  
**Fecha:** 2026-06-18  
**Tarea:** VEGA_TASK_003_PASTE_FORMAT  
**Estado:** COMPLETO

---

## Cambios realizados

### 1. Nombre limpio del patrón — nueva función `_clean_pattern_name(name)`

El motor legacy agrega sufijos al nombre del ítem: `"Philo (convertido) 600.0x600.0"`.  
La función los elimina con dos regex encadenados:

1. Strip dimensión: ` \d+\.?\d*[xX]\d+\.?\d*` al final → elimina `600.0x600.0`
2. Strip parentético: ` \(.*\)` al final → elimina `(convertido)`

Casos probados:
| Input | Output |
|-------|--------|
| `Philo (convertido) 600.0x600.0` | `Philo` |
| `Subte 650.0x800.0` | `Subte` |
| `Tresbolillo` | `Tresbolillo` |
| `Diagonal 1200x600` | `Diagonal` |

### 2. Columnas separadas — nuevo formato tab

**Presupuesto** (5 columnas → B–F):
```
{qty}\tPanel {nombre}\t{ancho} x {alto}\ten {material}\t{precio}
```

**OT** (4 columnas → B–E):
```
{qty}\tPanel {nombre}\t{ancho} x {alto}\ten {material} / [{nombre}.dxf]
```

Antes: todo en una sola columna C con tabs vacíos para saltar D y E.  
Ahora: C, D, E con contenido real.

### 3. Dimensiones sin decimales

`int(float(occupied_width_mm))` → `600.0` → `600`

### 4. Precio con separador de miles

`f"{costo:,.2f}"` → `57123.03` → `57,123.03`

---

## Ejemplo de salida

```
1	Panel Philo	600 x 600	en N°18	57,123.03
2	Panel Subte	605 x 800	en N°18	65,705.53
```

```
1	Panel Philo	600 x 600	en N°18 / [Philo.dxf]
2	Panel Subte	605 x 800	en N°18 / [Subte.dxf]
```

---

## Archivo modificado

`apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`

- Nueva función `_clean_pattern_name()` junto a `_format_material_label()`
- Bloque de generación de paste reescrito (sección `# Copy-paste blocks` en `render_form()`)

---

## Tests

```
31 passed, 4 errors (pre-existentes — PermissionError tmp_path en Windows)
```

---

## Para ver los cambios

```
python tools/run_panel_sales_app.py
```
