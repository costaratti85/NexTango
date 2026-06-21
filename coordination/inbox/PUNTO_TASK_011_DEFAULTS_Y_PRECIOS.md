# PUNTO_TASK_011 — Tabla de materiales predeterminada + parámetros de precios diarios

**De:** Nova  
**Para:** Punto  
**Fecha:** 2026-06-17  
**Prioridad:** Alta

---

## Contexto

Se crearon dos archivos nuevos:

- `docs/MATERIALES_Y_VELOCIDADES.md` — tabla de referencia con fuentes y notas técnicas
- `apps/sistema_industrial/sistema_industrial/presets/material_defaults.py` — 21 filas listas para pre-cargar la tabla (7 galvanizado cal 30/25/22/20/18/16/14, 7 acero negro cal 24/22/20/18/16/14/12, 7 inoxidable 0.6–2.5mm)

Esta tarea tiene dos partes.

---

## Parte 1 — Botón "Cargar predeterminados" en `/materiales`

### Qué hacer

En la página `/materiales`, agregar un botón:

```
[ Cargar tabla predeterminada ]
```

Al hacer click:
1. Leer `MATERIAL_DEFAULTS` de `material_defaults.py`
2. Si la tabla ya tiene filas, mostrar confirmación: `"La tabla ya tiene X filas. ¿Reemplazar con los valores predeterminados? Esto borrará los valores actuales."`
3. Si confirma (o tabla vacía): reemplazar el contenido del `material_table.json` con las 21 filas de `MATERIAL_DEFAULTS`
4. Recargar la tabla en pantalla

### Endpoint sugerido

`POST /api/materials/load_defaults`  
Body: `{ "replace": true/false }`  
Respuesta: `{ "loaded": 21, "previous": N }`

El botón está junto al botón existente de guardar/agregar, en la parte superior de la tabla de `/materiales`.

---

## Parte 2 — Página de parámetros de precios diarios

### Qué hacer

Nueva página en `/precios` (o puede ser una sección en la misma UI principal, lo que te parezca más limpio).

Muestra un formulario con 4 campos:

| ID campo | Label | Unidad |
|---|---|---|
| `precio_segundo_maquina` | Precio por segundo de máquina | $/s |
| `precio_kg_acero_negro` | Precio por kg — acero negro | $/kg |
| `precio_kg_galvanizado` | Precio por kg — galvanizado | $/kg |
| `precio_kg_inoxidable` | Precio por kg — inoxidable 304 | $/kg |

- Los valores se guardan en un archivo JSON: `Programas_hechos/Panel Decorativo/daily_prices.json`
- Al cargar la página, se leen los valores actuales del JSON (si existe)
- Botón "Guardar precios" que escribe el JSON
- Si el archivo no existe, los campos aparecen vacíos

### Dónde linkear

Agregar un link a `/precios` (o la sección equivalente) en la barra de navegación del header, junto al link existente a `/materiales`.

### Uso posterior

Estos precios serán usados por el motor de generación para calcular el costo del presupuesto:

```
costo_panel = kg_material × precio_kg_[tipo] + segundos_maquina × precio_segundo_maquina
```

Por ahora solo necesitamos guardar/leer los 4 valores. La fórmula de presupuesto viene en la siguiente tarea.

---

## Criterio de aceptación

1. Botón "Cargar predeterminados" en `/materiales` carga las 21 filas desde `material_defaults.py`
2. Si la tabla ya tiene datos, pide confirmación antes de reemplazar
3. Página `/precios` (o sección) con formulario de 4 campos, guardado en `daily_prices.json`
4. Link a precios visible en el header
5. Tests existentes siguen pasando

## Reportar en

`coordination/reports/PUNTO_TASK_011_REPORT.md`
