# PUNTO_TASK_014 — Renombrar materiales + agregar Inoxidable 430 + 5° parámetro de precio

**De:** Nova  
**Para:** Punto  
**Fecha:** 2026-06-17  
**Prioridad:** Alta

---

## Contexto

Se actualizaron los datos de referencia:
- `material_defaults.py` — ahora tiene 28 filas (4 materiales × 7 espesores) con nuevos calibres y velocidades
- `docs/MATERIALES_Y_VELOCIDADES.md` — tablas completas actualizadas

Los cambios en el código son de renombrado y extensión. Nada de lógica nueva de cálculo.

---

## Cambios requeridos en `panel_sales_local_app.py`

### 1. Renombrar "Acero negro" → "Chapa doble decapada"

En `calculate_cost()` (la función que elige `precio_kg` según el nombre del material):

```python
# ANTES:
if "galvanizado" in material_name.lower():
    precio_kg = float(daily_prices.get("precio_kg_galvanizado", 0))
elif "inoxidable" in material_name.lower():
    precio_kg = float(daily_prices.get("precio_kg_inoxidable", 0))
else:
    precio_kg = float(daily_prices.get("precio_kg_acero_negro", 0))

# DESPUÉS:
mat = material_name.lower()
if "galvanizado" in mat:
    precio_kg = float(daily_prices.get("precio_kg_galvanizado", 0))
elif "430" in mat:
    precio_kg = float(daily_prices.get("precio_kg_inoxidable_430", 0))
elif "304" in mat or "inoxidable" in mat:
    precio_kg = float(daily_prices.get("precio_kg_inoxidable_304", 0))
else:
    # "Chapa doble decapada" y cualquier otro acero
    precio_kg = float(daily_prices.get("precio_kg_doble_decapada", 0))
```

### 2. Actualizar la página `/precios` — 5 campos en lugar de 4

Reemplazar el formulario de `/precios` para que tenga 5 campos:

| ID campo | Label | Unidad |
|---|---|---|
| `precio_segundo_maquina` | Precio por segundo de máquina | $/s |
| `precio_kg_doble_decapada` | Precio por kg — chapa doble decapada | $/kg |
| `precio_kg_galvanizado` | Precio por kg — galvanizado | $/kg |
| `precio_kg_inoxidable_430` | Precio por kg — inoxidable 430 | $/kg |
| `precio_kg_inoxidable_304` | Precio por kg — inoxidable 304 | $/kg |

El anterior campo `precio_kg_acero_negro` desaparece. El anterior campo `precio_kg_inoxidable` se divide en `precio_kg_inoxidable_430` y `precio_kg_inoxidable_304`.

### 3. Compatibilidad con `daily_prices.json` existente

Si el JSON existente tiene `precio_kg_acero_negro`, al leerlo mapear ese valor a `precio_kg_doble_decapada` para no perder datos. Si tiene `precio_kg_inoxidable`, usarlo como valor inicial de `precio_kg_inoxidable_304`.

```python
def _load_daily_prices():
    # ... lectura del JSON ...
    # Migrar claves viejas si existen
    if "precio_kg_acero_negro" in prices and "precio_kg_doble_decapada" not in prices:
        prices["precio_kg_doble_decapada"] = prices.pop("precio_kg_acero_negro")
    if "precio_kg_inoxidable" in prices and "precio_kg_inoxidable_304" not in prices:
        prices["precio_kg_inoxidable_304"] = prices.pop("precio_kg_inoxidable")
    return prices, prices_missing
```

### 4. Dropdown de material en la UI

El dropdown de material (paso 3) actualmente lista los materiales únicos del API response. Al cargar la tabla predeterminada, los materiales ahora son:
- "Chapa doble decapada"
- "Chapa galvanizada"
- "Inoxidable 430"
- "Inoxidable 304"

No hace falta cambiar la lógica del dropdown — toma los materiales del `/api/materials` dinámicamente. Solo verificar que el formato de espesor funcione correctamente:
- "Chapa doble decapada" y "Chapa galvanizada": calibre != "-" → mostrar `N°{calibre} - {espesor}mm`
- "Inoxidable 430" e "Inoxidable 304": calibre == "-" → mostrar solo `{espesor}mm`

La condición actual es `if tipo.toLowerCase().includes('inox')`. Actualizar para que sea:
```javascript
const mostrarCalibre = entries[0] && entries[0].calibre && entries[0].calibre !== '-';
opt.textContent = mostrarCalibre
    ? `N°${e.calibre} - ${e.espesor_mm}mm`
    : `${e.espesor_mm}mm`;
```
(Así no depende del nombre del material sino del valor del campo `calibre`.)

---

## Archivos a modificar

- `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`

## Archivos NO modificar (ya actualizados por Nova)

- `apps/sistema_industrial/sistema_industrial/presets/material_defaults.py` ← ya tiene las 28 filas nuevas
- `docs/MATERIALES_Y_VELOCIDADES.md` ← ya actualizado

---

## Criterio de aceptación

1. `/precios` muestra 5 campos con los nombres correctos
2. `calculate_cost()` asigna el precio correcto para los 4 tipos de material
3. Si `daily_prices.json` tiene claves viejas (`precio_kg_acero_negro`, `precio_kg_inoxidable`), se migran automáticamente
4. El dropdown de espesor usa el campo `calibre` del API para decidir el formato (no el nombre del material)
5. Tests existentes siguen pasando

## Reportar en

`coordination/reports/PUNTO_TASK_014_REPORT.md`
