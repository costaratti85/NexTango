# PUNTO_TASK_009 — Dropdowns de material/espesor + resumen de recursos

**De:** Nova  
**Para:** Punto  
**Fecha:** 2026-06-15  
**Prioridad:** Alta

---

## Contexto

Gemu acaba de completar GEMU_TASK_005: el endpoint `/generate` ahora devuelve `consumed_resources` con `material_kg`, `machine_seconds`, `pierce_count`, `consumibles_used` cuando el material+espesor está cargado en la tabla de materiales.

Esta tarea tiene dos partes relacionadas: los dropdowns que reemplazan los inputs libres, y el panel de resumen que muestra los resultados.

---

## Parte 1 — Dropdowns de material y espesor

### Situación actual

En el paso 3 de la UI principal (`/`), hay inputs de texto libre para material y espesor. El operario puede escribir cualquier cosa, lo que lleva a errores de lookup en la tabla de materiales.

### Nuevo comportamiento

Reemplazar los inputs de material y espesor por **un solo dropdown** que lista las combinaciones disponibles en la tabla de materiales.

**Formato de cada opción:** `"Acero negro — 2 mm"` (material + espesor en una sola línea)  
**Value de cada `<option>`:** JSON string `'{"material":"Acero negro","espesor_mm":2}'` (para parsear al enviar)  
**Fuente:** `GET /api/materials` al cargar la página (o cuando se abre el paso 3)

Si la tabla está vacía, mostrar una opción deshabilitada: `"— Cargá materiales en /materiales —"` y deshabilitar el botón Agregar Lote.

Al seleccionar una opción, rellenar automáticamente los campos hidden `material` y `espesor_mm` que el JS ya usa para construir el batch.

El dropdown reemplaza los dos inputs actuales. No hace falta dropdown en cascada (material → espesor separados) — un solo combo es más simple.

### Cuándo cargar las opciones

Al montar la página, hacer `fetch('/api/materials')` y llenar el dropdown. Si el usuario carga nuevos materiales en `/materiales` y vuelve, un botón "↺" al lado del dropdown refresca la lista sin recargar la página.

---

## Parte 2 — Panel de resumen post-generate

### Qué mostrar

Después de que el usuario hace click en "GENERAR DXF" y el servidor responde, mostrar un panel de resumen visible (no modal) con los recursos calculados.

Si `consumed_resources` está presente en la respuesta:

```
╔══════════════════════════════════════╗
║  Recursos consumidos                 ║
╠══════════════════════════════════════╣
║  Material      X.XX kg              ║
║  Tiempo máq.   X min XX s           ║
║  Perforaciones XXX                   ║
║  Consumible    X.XX u               ║
╚══════════════════════════════════════╝
```

El tiempo en minutos+segundos es más legible que segundos brutos.

Si la respuesta trae `consumed_resources: null` (material no en tabla), mostrar un aviso: _"Cargá los datos de [material] [espesor]mm en /materiales para ver los recursos."_ con link a `/materiales`.

Si hay múltiples lotes con distintos materiales, mostrar el total como suma de todos los lotes.

### Ubicación

Debajo del link de descarga del DXF, dentro del área de resultado que ya existe. No reemplaza el DXF — es información adicional.

---

## Criterio de aceptación

1. Los campos material/espesor en paso 3 son un dropdown poblado desde `/api/materials`
2. Si la tabla está vacía, el dropdown lo indica y el botón Agregar Lote está deshabilitado
3. Al generar con un material que está en la tabla, aparece el panel de recursos consumidos con valores reales
4. Al generar con material no en la tabla, aparece el aviso con link a `/materiales`
5. Tests existentes (58+) siguen pasando

## Reportar en

`coordination/reports/PUNTO_TASK_009_REPORT.md`
