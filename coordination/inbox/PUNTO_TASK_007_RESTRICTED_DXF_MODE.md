# PUNTO_TASK_007 — Patrones DXF con entidades no soportadas: modo restringido

**De:** Nova  
**Para:** Punto  
**Fecha:** 2026-06-13  
**Prioridad:** Alta — desbloquea patrones DXF reales que hoy se rechazan

---

## Decisión (viene de Constantino)

Los archivos DXF que contienen entidades no soportadas (SPLINE, ELLIPSE, etc.) ya **no se rechazan**. Se aceptan con una restricción automática de modo.

**Antes:** SPLINE detectado → error bloqueante → el patrón no se carga.  
**Ahora:** SPLINE detectado → el patrón se carga, pero queda marcado como "modo restringido".

---

## Qué cambia en comportamiento

### Modo restringido significa:
- ✅ Disponible: **"sin cortar / centrado"** — figuras completas, centradas en el panel, sin intersecciones
- ❌ Deshabilitado: **"cortar en borde"** — el motor no puede calcular intersecciones con splines/elipses

### El sistema debe advertirlo en dos momentos:
1. **Al cargar en el admin**: mensaje de advertencia visible (no error), ej: _"Patrón cargado con restricciones: contiene SPLINE. Solo disponible en modo centrado."_
2. **Al seleccionar en la UI principal**: cuando el vendedor elige este patrón, mostrar un aviso visible de que el modo de corte en borde no está disponible.

---

## Cambios técnicos

### 1. Almacenamiento — `pattern_library.json`

Agregar dos campos opcionales a cada entrada del patrón:

```json
{
  "name": "mi_patron",
  ...
  "restricted": true,
  "restricted_reason": "Contiene entidades no soportadas: SPLINE"
}
```

Los patrones existentes sin estos campos se tratan como `restricted: false`.

### 2. Validación DXF al cargar (`panel_sales_local_app.py`)

El código actual detecta entidades no soportadas y retorna un error HTTP. Cambiarlo para que:
- Detecte las entidades problemáticas (mantener la lógica existente de detección)
- En lugar de retornar error 400, retorne 200 con `"restricted": true` y `"restricted_reason": "Contiene entidades: SPLINE"`
- Guarde el patrón normalmente en la librería, con los dos campos nuevos

### 3. Admin (`/admin`) — aviso al listar patrones restringidos

En la tabla de patrones, mostrar una etiqueta o nota para los patrones con `restricted: true`. Algo simple: un badge naranja "Modo restringido" o una nota en el subtítulo de la fila. No hace falta nuevo endpoint — la info ya estará en `GET /api/patterns`.

### 4. UI principal (`/`) — al seleccionar patrón restringido

Cuando `selectPattern()` recibe un patrón con `restricted: true`:
- Mostrar un aviso visible al usuario (banner amarillo debajo de la grilla, similar al bloque `#tres-inline` pero no interactivo): _"Este patrón solo admite modo centrado — el corte en borde está deshabilitado."_
- Si la UI tiene algún control de modo "cortar en borde", deshabilitarlo/ocultarlo para este patrón.
- El aviso desaparece al seleccionar un patrón sin restricción.

---

## Criterio de aceptación

- Un DXF con SPLINE se puede cargar en el admin sin error
- El patrón aparece en la galería con una marca visible de restricción
- Al seleccionar ese patrón en la UI, aparece el aviso de modo limitado
- Un DXF sin entidades problemáticas sigue funcionando exactamente igual que antes
- Los tests existentes siguen pasando (40+)

## Reportar en

`coordination/reports/PUNTO_RESTRICTED_DXF_REPORT.md`
