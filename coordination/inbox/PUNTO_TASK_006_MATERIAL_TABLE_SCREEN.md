# PUNTO_TASK_006 — Pantalla tabla material/espesor

**De:** Nova  
**Para:** Punto  
**Fecha:** 2026-06-13  
**Prioridad:** Alta — necesaria para cerrar el primer presupuesto

---

## Contexto

El motor de corte produce tres valores: metros lineales de corte, cantidad de perforaciones, y m² de chapa. Para convertir esos valores a recursos físicos (kg de material, segundos de máquina, unidades de consumible), necesitamos una tabla de factores de conversión por material y espesor. Esta pantalla es donde el usuario carga esos factores.

**Esta tabla NO tiene precios.** Los precios los carga ERPNext/Tango después. Aquí solo van los factores físicos.

---

## Especificación

### Datos

Cada fila de la tabla representa una combinación material+espesor. Los campos son:

| Campo | Tipo | Descripción |
|---|---|---|
| `material` | texto | Ej: "Acero inoxidable", "Acero negro", "Aluminio" |
| `espesor_mm` | número | Espesor en mm |
| `densidad_kg_m2` | número | kg por m² de chapa (ej: acero 2mm → 15.7 kg/m²) |
| `velocidad_corte_mm_s` | número | mm/s de corte para este material+espesor |
| `tiempo_perforacion_s` | número | segundos por perforación (pierce delay) |
| `consumible_por_perforacion` | número | factor de desgaste de boquilla por perforación (puede ser decimal, ej: 0.05) |

### Almacenamiento

Nuevo archivo JSON: `Programas_hechos/Panel Decorativo/material_table.json`

Formato:
```json
[
  {
    "material": "Acero negro",
    "espesor_mm": 2,
    "densidad_kg_m2": 15.7,
    "velocidad_corte_mm_s": 83.3,
    "tiempo_perforacion_s": 0.5,
    "consumible_por_perforacion": 0.05
  }
]
```

### Endpoints (agregar en panel_sales_local_app.py)

- `GET /api/materials` → devuelve lista JSON
- `POST /api/materials` → crea una fila (JSON body)
- `DELETE /api/materials` → elimina por `material`+`espesor_mm` (JSON body)

### UI (en /admin)

Nueva sección en la página `/admin`, debajo de la sección de patrones existente. Título: **"Tabla de materiales"**.

Contenido:
1. Tabla con columnas: Material | Espesor mm | Densidad kg/m² | Vel. corte mm/s | T. perforación s | Consumible/perf. | [Borrar]
2. Formulario de alta con los 6 campos + botón "Agregar"
3. El botón Borrar sigue el mismo patrón que el de patrones: feedback visual, JSON request, recarga

No hace falta edición inline — solo alta y baja. Si se necesita editar una fila, se borra y se vuelve a cargar.

---

## Criterio de aceptación

- La sección aparece en `/admin` al correr el servidor
- Se puede agregar una fila desde el formulario y aparece en la tabla
- Se puede borrar una fila con feedback visual
- El JSON se persiste en disco
- 42 tests siguen pasando (o más si agrega tests)

## Reportar en

`coordination/reports/PUNTO_MATERIAL_TABLE_REPORT.md`
