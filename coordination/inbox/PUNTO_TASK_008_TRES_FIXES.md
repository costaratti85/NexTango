# PUNTO_TASK_008 — Tres fixes críticos

**De:** Nova  
**Para:** Punto  
**Fecha:** 2026-06-15  
**Prioridad:** Urgente

---

## Fix 1 — Botón Borrar no reacciona (bug HTML)

**Archivo:** `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`

**Causa raíz:** El onclick genera HTML con comillas dobles anidadas. `json.dumps("Subte 3")` produce `"Subte 3"` (con comillas dobles). El atributo HTML también usa comillas dobles. El browser trunca el atributo al primer `"` interno → la función nunca se llama.

**Fix:** Cambiar el botón de borrar en la tabla de patrones admin para usar un data attribute en lugar de JSON inline:

```python
# Línea ~1480 — ANTES:
f'<button class="btn-action btn-del" onclick="deletePattern({name_json}, this)">Borrar</button>'

# DESPUÉS:
f'<button class="btn-action btn-del" data-pattern-name="{safe_name}" onclick="deletePattern(this.dataset.patternName, this)">Borrar</button>'
```

`safe_name` ya existe en el mismo bloque (es `escape(name)`). El JS recibe el nombre como string limpio desde el dataset.

La función `deletePattern(name, btn)` en JS no cambia — recibe el nombre igual que antes.

---

## Fix 2 — Recursos siguen en cero (bypass del adaptador)

**Archivo:** `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`

**Causa raíz:** El servidor local genera paneles en su propio pipeline (líneas ~555-650) que llama directamente a `legacy_main.create_cad_result_items_from_batch()` y luego lee `item.cut_length_mm` del resultado — que el motor legacy devuelve como 0 (hardcodeado). El fix de Gemu fue en `legacy_panel_adapter.py` que el servidor local nunca llama.

**Fix:** Importar las funciones calculadas de Gemu y usarlas en el loop de recursos. `legacy_panel_adapter.py` está en el mismo directorio.

En el bloque de imports del módulo (al tope del archivo), agregar:
```python
from legacy_panel_adapter import calculate_cut_length_mm, calculate_pierce_count
```

Luego en el bloque `all_resources` (~línea 636-650), reemplazar:
```python
# ANTES:
"cut_length_mm": item.cut_length_mm,
"pierce_count": item.pierce_count,

# DESPUÉS:
"cut_length_mm": calculate_cut_length_mm(item.geometry_items),
"pierce_count": calculate_pierce_count(item.geometry_items),
```

`item.geometry_items` ya existe en cada CADResultItem. Las funciones de Gemu operan sobre esa lista.

---

## Fix 3 — Tabla de materiales: nueva página estilo planilla

**Contexto:** Constantino quiere la tabla de materiales en una página separada, navegable como Excel.

### Página nueva: `GET /materiales`

Una página HTML independiente (no parte de `/admin`). Título: **"Tabla de materiales"**.

### Columnas de la tabla

Por ahora, tres columnas de datos (más material y espesor como clave):

| Columna | Campo JSON | Descripción |
|---|---|---|
| Material | `material` | texto, ej: "Acero negro" |
| Espesor mm | `espesor_mm` | número |
| Densidad kg/m² | `densidad_kg_m2` | para calcular kg de material |
| Velocidad corte mm/s | `velocidad_corte_mm_s` | para calcular tiempo de corte |
| Tiempo perforación s | `tiempo_perforacion_s` | para calcular tiempo de perforaciones |

El campo `consumible_por_perforacion` queda en el JSON por compatibilidad pero no se muestra en la UI por ahora.

### UX estilo planilla

- La tabla muestra TODAS las filas, cada celda visible directamente (no inputs separados)
- Las celdas de datos son editables inline: al hacer click en una celda, se convierte en `<input>` editable
- Al presionar Enter o Tab, guarda el cambio y avanza a la siguiente celda
- Al presionar Escape, cancela la edición
- La fila de "nueva fila" está siempre al final (fila vacía con inputs directos)
- Al completar la fila nueva y presionar Enter en el último campo, se agrega y se limpia
- Botón borrar al costado de cada fila, feedback visual como los otros

### Navegación

La última fila (nueva fila) tiene todos los campos editables siempre. Al hacer Tab desde el último campo, se guarda y se crea la fila, el foco va a la nueva fila vacía.

### Backend

Los endpoints `GET /api/materials` y `POST /api/materials` y `DELETE /api/materials` ya existen (Punto TASK_006). No hace falta cambiarlos. La nueva página solo los consume desde JS.

Agregar un link a `/materiales` en el header de `/admin`.
Agregar un link de vuelta a `/admin` en la página `/materiales`.

### No hace falta

- Ordenar columnas
- Filtros
- Paginación (habrá pocas filas)

---

## Criterio de aceptación

1. El botón Borrar en admin reacciona visualmente al click (cambia a "Borrando...")
2. Al generar un panel, `cut_length_m` y `pierce_count` son distintos de 0 en la respuesta JSON
3. `http://127.0.0.1:8765/materiales` carga una página con tabla editable inline
4. Se puede agregar una fila, editar una celda, y borrar una fila desde esa página
5. Tests existentes siguen pasando (40+)

## Reportar en

`coordination/reports/PUNTO_TASK_008_REPORT.md`
