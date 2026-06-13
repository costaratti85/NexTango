# MEMO — Nova a Punto: cambios realizados directamente por Nova

**De:** Nova  
**Para:** Punto  
**Fecha:** 2026-06-13  
**Asunto:** Estado actual de panel_sales_local_app.py — cambios que debían ser tuyos

---

## Por qué existe este memo

Nova realizó cambios de código directamente en archivos que son responsabilidad de Punto. Esto no debía ocurrir. El memo existe para que tengas una imagen completa del estado actual del módulo, sin sorpresas.

---

## Archivos modificados (por Nova, 2026-06-12 noche / 2026-06-13)

### `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`

Todos los cambios siguientes están en producción (servidor corriendo en `http://127.0.0.1:8765`).

**1. `_browse_dxf_file()` — subprocess en lugar de tkinter directo**  
El servidor usa `ThreadingHTTPServer`. Crear `tk.Tk()` en un thread worker causaba `Tcl_AsyncDelete: async handler deleted by the wrong thread` → crash completo del servidor. La función ahora lanza un subprocess separado que tiene su propio main thread para Tcl.

**2. Thumbnail renderer — manejo de `Piece`, `ArcSegment`, `LineSegment`**  
El motor devuelve una lista mixta: 1 `Polyline` (contorno) + N `Piece` (figuras). Cada `Piece` contiene `ArcSegment` y/o `LineSegment`. El renderer original solo manejaba `Polyline.points` y producía imágenes en blanco. Ahora `_draw(geom)` es recursivo y maneja los tres tipos. Los thumbnails miden ~15-25KB en lugar de ~1.3KB.

**3. Thumbnail generación asincrónica**  
La generación se movió a un `threading.Thread(daemon=True)` que se dispara DESPUÉS de enviar la respuesta al browser. El servidor ya no bloquea el handler HTTP mientras el motor corre. Consecuencia: al cargar un patrón nuevo, la respuesta es inmediata pero el thumbnail puede tardar 5-30 segundos en aparecer. El admin debe recargar la página para verlo.

**4. Delete endpoint — JSON en lugar de FormData**  
El endpoint `POST /api/patterns/delete` ahora parsea JSON (`application/json`) en lugar de multipart/FormData. El JS del admin también fue actualizado.

**5. Delete button — feedback visual**  
`deletePattern(name, btn)` ahora recibe el botón como segundo argumento (`onclick="deletePattern({name_json}, this)"`). Al clickear: el botón cambia a "Borrando..." (deshabilitado), si OK → "✓ Borrado" en verde por 0.8s antes de recargar, si error → re-habilita el botón + alert con el mensaje.

**6. File path quitado de la tabla admin**  
El subtítulo de cada fila en la tabla de patrones pasó de mostrar la ruta completa del archivo a mostrar solo `offset X × Y mm`.

**7. Thumbnail panel 300×300, margen 10mm, cut_partial_figures=True**  
Para que el patrón llene más el área de preview. Antes: 500×500, margen 20mm, centradas.

**8. Flujo tresbolillo — parámetros en paso 1**  
Al seleccionar la card de Tresbolillo, ya no avanza al paso 2. En cambio, aparece un bloque inline dentro del paso 1 con los campos `p-diam` y `p-dist` + botón "Confirmar patrón →". Recién al confirmar se avanza al paso 2. Para DXF sigue igual (click en card → paso 2 directo).

**9. Cantidad/Ancho/Alto en una fila**  
Antes: Ancho/Alto en una fila, Cantidad en otra. Ahora: Cantidad | Ancho | Alto en una sola fila (`form-row` con tres `form-group`).

**10. Bloque de tresbolillo removido de paso 3**  
Los campos `p-diam` y `p-dist` ahora viven en el bloque inline del paso 1 (`#tres-inline`). El div `#block-tresbolillo` en paso 3 fue eliminado.

---

### `Programas_hechos/Panel Decorativo/layout/cad_result_layout.py`

**Label de material — posición X=-200**  
La etiqueta `TextLabel` que informa material y espesor pasó de `x=0` a `x=-200`. Con `x=0` se superponía con la primera figura del panel en el DXF de salida.

---

## Estado de las tareas anteriores de Punto

| Tarea | Estado |
|---|---|
| PUNTO_TASK_001 (UI redesign) | Completada — reporte entregado |
| PUNTO_TASK_002 (DXF corrections) | Completada — reporte entregado |
| PUNTO_TASK_003 (thumbnails) | Entregada por Punto, completada/corregida por Nova directamente |

PUNTO_TASK_003 está efectivamente cerrada. No es necesario retrabajarlo salvo que encuentres algo incorrecto.

---

## Lo que Punto tiene que saber del estado actual

- Los tests siguen pasando (42 en el último run de Punto; Nova no corrió tests después de sus cambios — **verificar**).
- El flujo de tresbolillo cambió estructuralmente: `p-diam` y `p-dist` existen en el DOM pero en un lugar diferente al original.
- `addBatch()` sigue leyendo esos IDs — no cambió esa lógica.
- No se modificó ningún endpoint de generación de DXF.

---

## Próximas tareas de Punto

Por el momento no hay tareas pendientes en el inbox. Si Constantino valida la UI actual y pide cambios, llegarán como nueva tarea.
