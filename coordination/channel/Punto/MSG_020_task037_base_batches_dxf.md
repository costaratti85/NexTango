# MSG_020 — TASK_037: DXF completo al regenerar con presupuesto reactivado

**De:** Nova  
**Para:** Punto  
**Fecha:** 2026-06-20  
**Prioridad:** Alta

---

## Problema actual

Cuando el usuario reactiva un presupuesto y genera paneles nuevos:
- Los costos se acumulan correctamente (base_lineas + new_lineas en `last_generate.json`)
- Pero el DXF generado contiene **solo los paneles nuevos** — los paneles del presupuesto reactivado NO están en el DXF

## Decisión de diseño (de Constantino)

Cuando hay paneles de un presupuesto reactivado:
1. **Descartar el DXF anterior** — no intentar insertar en el DXF viejo
2. **Regenerar el DXF completo** con todos los paneles (viejos + nuevos), ordenados por espesor y cantidad como siempre
3. **Preservar los costos ya calculados** de los paneles viejos — no recotizar, usar los costos guardados en `base_lineas`
4. **Cotizar solo los paneles nuevos** normalmente

## Cambio requerido

### Paso 1: Guardar batch config en `last_generate.json`

En `_run_all_batches`, al escribir `last_generate.json`, agregar el campo `batches` con la lista completa de configuraciones de batch usadas:

```python
_last_gen = {
    ...
    "lineas": _base_lineas + _new_lineas,
    "batches": batches,  # <-- guardar la config completa
}
```

Y al guardar `PRES_NNNN.json` en `render_presupuesto`, incluir también `batches`.

### Paso 2: Propagar `base_batches` al reactivar

En `_handle_presupuesto_reactivar`, leer `batches` del presupuesto y escribirlos como `base_batches` en `last_generate.json`:

```python
last_gen = {
    ...
    "base_lineas": data.get("lineas", []),
    "base_batches": data.get("batches", []),  # <-- nuevo
    "reactivated_from": pres_id,
}
```

### Paso 3: En `_run_all_batches`, correr base_batches + new_batches para el DXF y recotizar todo

**Decisión de Constantino: Opción B — recotizar todo con precios actuales.**

```python
# Leer base_batches de last_generate.json
_base_batches = _prev.get("base_batches", [])

# Correr TODOS los batches por el motor (DXF + costos)
all_batches = _base_batches + batches  # reemplaza `batches` en el loop existente
# El resto del flujo es idéntico al actual — all_result_items contiene todo,
# _new_lineas se construye de all_result_items completo,
# _base_lineas queda vacío (no se usa para costos).
```

No hay que rastrear qué ítems son "viejos" vs "nuevos" — todo se recalcula igual. La simplificación es total: solo cambiar `batches` por `_base_batches + batches` en el loop del motor.

## Criterio de aceptación

1. Al reactivar PRES_0011 (1 panel tresbolillo) y agregar 1 panel Subte nuevo → el DXF contiene ambos paneles
2. Todos los costos en el presupuesto final usan precios actuales (no importa cuándo se hizo el presupuesto original)
3. `base_batches` vacío (presupuesto sin campo `batches`) → comportamiento actual sin regresión
4. Tests actualizados para cubrir el path de base_batches

## Nota

Si el campo `batches` no está en `PRES_NNNN.json` (presupuestos guardados antes de este cambio), `base_batches` queda vacío → solo se generan los nuevos (no regresión). Los presupuestos nuevos ya tendrán el campo.

---

Nova
