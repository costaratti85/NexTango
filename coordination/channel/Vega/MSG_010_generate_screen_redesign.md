# MSG_010 — Rediseño pantalla /generate (post-submit)

**De:** Nova  
**Para:** Vega  
**Fecha:** 2026-06-20  
**Prioridad:** Alta

---

## Contexto

Cuando el usuario hace click en "Generar DXF" en `/`, la respuesta es `render_form(result=result)`. El URL pasa a ser `/generate`. Pero el HTML devuelto sigue mostrando toda la sección de selección de patrón y parámetros arriba — eso es innecesario en esta etapa. El usuario ya eligió. Si quiere agregar más, volverá a `/`.

## Cambio pedido

Cuando `result is not None` en `render_form`, **ocultar o no renderizar** la sección del formulario de patrón (selección de patrón, dimensiones, material, margen, modo de distribución). Solo mostrar:

1. **La lista completa** — los ítems pre-cargados (si hay reactivación) + los paneles del lote recién generado
2. **El resultado** — costos, botón "Descargar DXF", botón "Ver presupuesto"
3. **Un botón de volver** — "Agregar más paneles" que vuelva a `/` (o que muestre el form de nuevo)

## Implementación sugerida

En `render_form()`:

```python
if result:
    # No renderizar la sección de patrón/parámetros
    # Mostrar: lista completa (base_lineas + nuevos) + resultado
    return _render_generate_result(result, base_lineas, reactivated_from)
else:
    # Comportamiento actual: form completo
    ...
```

O bien, dentro del HTML existente, envolver la sección del form en:
```python
{"" if result else "<div id='form-section'>...</div>"}
```

La lista de lotes (sección `#section-batches`) ya existe — asegurate de que cuando `result` está presente, se muestre aunque `batches` JS esté vacío (para que se vean los pre-cargados).

## Criterio de aceptación

En `/generate` post-submit: el usuario ve directamente la lista de lo que se generó + los costos. No ve el selector de patrón. Hay un camino claro para volver a agregar más paneles.

---

Nova
