# GEMU_TASK_005 — Reporte: Recursos Consumidos en /generate

**Agente:** Gemu  
**Fecha:** 2026-06-15  
**Estado:** Completado

---

## Qué se implementó

### 1. `calculate_consumed_resources()` — `legacy_panel_adapter.py`

Función pura agregada después de `calculate_sheet_area_m2()`. Convierte los outputs geométricos del motor a recursos físicos usando los factores de la tabla de materiales:

```python
def calculate_consumed_resources(
    cut_length_m: float,
    pierce_count: int,
    sheet_area_m2: float,
    material_entry: dict,
) -> dict:
```

Retorna `{"material_kg", "machine_seconds", "pierce_count", "consumibles_used"}` con redondeos apropiados.

Verificación con valores reales: entrada (3.5 m corte, 42 perforaciones, 0.06 m², acero 2 mm) → `{'material_kg': 0.942, 'machine_seconds': 63.0, 'pierce_count': 42, 'consumibles_used': 2.1}`.

### 2. Importaciones actualizadas — `panel_sales_local_app.py`

Se agregaron `calculate_consumed_resources` y `calculate_sheet_area_m2` al bloque de imports desde `legacy_panel_adapter`.

### 3. Lookup + cálculo en `_run_all_batches()` — `panel_sales_local_app.py`

Dentro de `_run_all_batches`, después de construir `first_input`:

- Se instancia `MaterialTable` y se busca la entrada que coincida con `first_input.material` + `first_input.thickness_mm`.
- Si no existe: `consumed_resources = None`, se genera un warning descriptivo.
- Si existe: se llama `calculate_consumed_resources()` por cada `item` en `all_result_items`.
- Cada dict en `all_resources` ahora incluye los campos `consumed_resources` y `consumed_resources_warning`.
- El warning de material faltante se agrega también a la lista `warnings` del `LegacyPanelServiceResult`.

---

## Formato de respuesta por item en `calculated_resources`

```json
{
  "name": "...",
  "material": "...",
  "thickness_mm": 2.0,
  "cut_length_mm": 3500.0,
  "pierce_count": 42,
  "consumed_resources": {
    "material_kg": 0.942,
    "machine_seconds": 63.0,
    "pierce_count": 42,
    "consumibles_used": 2.1
  },
  "consumed_resources_warning": null
}
```

Cuando el material no está en la tabla:

```json
{
  "consumed_resources": null,
  "consumed_resources_warning": "Material 'X' con espesor 3.0 mm no está en la tabla de materiales. Agregar la entrada en /admin para obtener recursos consumidos."
}
```

---

## Tests

- **58 tests pasaron** con `--basetemp` custom (el tmpdir de sistema tiene PermissionError preexistente en este entorno Windows, no relacionado con este cambio).
- Los 9 errores de configuración en la corrida anterior son todos `PermissionError: [WinError 5]` en `C:\Users\vendo\AppData\Local\Temp\pytest-of-vendo`, presentes antes de este cambio.
- No se introdujeron regresiones.

---

## Archivos modificados

- `apps/sistema_industrial/sistema_industrial/presets/legacy_panel_adapter.py` — nueva función `calculate_consumed_resources()`
- `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py` — imports extendidos + lógica de lookup+cálculo en `_run_all_batches()`
