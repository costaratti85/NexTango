# GEMU_TASK_002 — Tabla de propiedades de materiales

**Asignado a:** Gemu  
**Depende de:** GEMU_TASK_001 (recursos consumidos)  
**Fecha:** 2026-06-13  
**Prioridad:** Media — iniciar después de GEMU_TASK_001

---

## Qué es esto

Una tabla editable donde el administrador registra, por cada combinación material+espesor:
- Peso por metro cuadrado (kg/m²)
- Velocidad de corte (mm/s)
- Tiempo de perforado (segundos por perforación)

Con estos datos + los recursos calculados en TASK_001, el sistema puede producir:
- Kg de material consumido
- Segundos de máquina estimados
- Cantidad de perforaciones (ya sale de TASK_001)

**Importante**: por ahora solo generar los recursos consumidos, NO calcular precios en dinero. El precio por kg, por hora de máquina, y el margen comercial son una etapa posterior.

---

## Forma de los datos

Archivo JSON editable en `fixtures/material_properties.json`:

```json
{
  "Acero 1mm": { "kg_m2": 7.85, "cut_speed_mm_s": 50.0, "pierce_time_s": 0.5 },
  "Acero 2mm": { "kg_m2": 15.7, "cut_speed_mm_s": 35.0, "pierce_time_s": 0.8 },
  "Acero 3mm": { "kg_m2": 23.55, "cut_speed_mm_s": 25.0, "pierce_time_s": 1.2 },
  "Inox 1.5mm": { "kg_m2": 11.8, "cut_speed_mm_s": 30.0, "pierce_time_s": 0.9 }
}
```

La clave es `"{Material} {Espesor}mm"` — debe coincidir con lo que ingresa el usuario en el formulario de ventas.

---

## Interfaz de administración

En `/admin` (la página de admin existente), agregar una segunda sección debajo de "Patrones registrados":

**Tabla de materiales** — lista editable con columnas: Material/Espesor | kg/m² | Vel. corte (mm/s) | T. perforado (s/perf) | Acciones (editar/borrar)

Con un formulario para agregar filas nuevas.

Endpoints a agregar:
- `GET /api/materials` → lista completa
- `POST /api/materials/add` → `{key, kg_m2, cut_speed_mm_s, pierce_time_s}`
- `POST /api/materials/delete` → `{key}`

---

## Cálculos a exponer (como función, no como UI todavía)

```python
def calculate_consumed_resources(
    cut_length_m: float,
    pierce_count: int,
    sheet_area_m2: float,
    material_key: str,
) -> dict:
    """
    Returns:
      kg_material: float
      machine_seconds: float
      pierce_count: int  (passthrough)
    """
```

Esta función se llama desde el servicio de ventas cuando el material_key existe en la tabla.
Si no existe, los campos quedan en None (el sistema igual genera el DXF, solo faltan los recursos).

---

## Reporte esperado

`coordination/reports/GEMU_TABLA_MATERIALES_REPORT.md` con ejemplo concreto de cálculo end-to-end.
