# GEMU_TASK_005 — Calcular recursos consumidos en el endpoint /generate

**De:** Nova  
**Para:** Gemu  
**Fecha:** 2026-06-15  
**Prioridad:** Alta

---

## Contexto

El endpoint `/generate` de `panel_sales_local_app.py` ya calcula `cut_length_m`, `pierce_count` y `sheet_area_m2` por lote. La tabla de materiales (`material_table.json`) tiene los factores de conversión por material+espesor. Hay que conectar ambos para devolver los recursos consumidos en la respuesta JSON del generate.

---

## Qué agregar

### 1. Función `calculate_consumed_resources()`

En `legacy_panel_adapter.py`, agregar:

```python
def calculate_consumed_resources(
    cut_length_m: float,
    pierce_count: int,
    sheet_area_m2: float,
    material_entry: dict,          # fila de material_table.json
) -> dict:
    """Convierte outputs del motor a recursos físicos usando la tabla de materiales."""
    densidad = float(material_entry.get("densidad_kg_m2", 0))
    velocidad = float(material_entry.get("velocidad_corte_mm_s", 0))
    tiempo_perf = float(material_entry.get("tiempo_perforacion_s", 0))
    consumible = float(material_entry.get("consumible_por_perforacion", 0))

    material_kg = sheet_area_m2 * densidad
    cutting_seconds = (cut_length_m * 1000.0 / velocidad) if velocidad > 0 else 0.0
    pierce_seconds = pierce_count * tiempo_perf
    machine_seconds = cutting_seconds + pierce_seconds
    consumibles_used = pierce_count * consumible

    return {
        "material_kg": round(material_kg, 3),
        "machine_seconds": round(machine_seconds, 1),
        "pierce_count": pierce_count,
        "consumibles_used": round(consumibles_used, 4),
    }
```

### 2. Lookup de material en el generate handler

En `panel_sales_local_app.py`, dentro de `_handle_generate()`, después de calcular `all_resources`:

- Importar `MaterialTable` (ya existe en el mismo archivo)
- Buscar la entrada de la tabla para el material+espesor del pedido
- Si no existe, devolver `consumed_resources: null` con un warning
- Si existe, llamar a `calculate_consumed_resources()` y agregarlo a la respuesta

El campo `material` y `thickness_mm` ya están disponibles en `first_input`.

La respuesta JSON del generate ya existe (buscar donde se hace `_send_json`). Agregar al dict:

```python
"consumed_resources": {
    "material_kg": ...,
    "machine_seconds": ...,
    "pierce_count": ...,
    "consumibles_used": ...,
} | None,
"consumed_resources_warning": "..." | None,
```

### 3. Importar `calculate_consumed_resources` donde corresponda

Agregar la función al import en `panel_sales_local_app.py` desde `legacy_panel_adapter`.

---

## Criterio de aceptación

Al hacer POST `/generate` con un lote válido cuyo material+espesor está en la tabla de materiales, la respuesta JSON incluye `consumed_resources` con valores no-cero.

Si el material no está en la tabla, la respuesta incluye `consumed_resources: null` y un `consumed_resources_warning` descriptivo.

Tests existentes (40+) siguen pasando.

## Reportar en

`coordination/reports/GEMU_TASK_005_REPORT.md`
