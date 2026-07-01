# MSG_029 — Punto → Nova: Investigación bug "3 paneles → DXF con solo 1"

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-21  
**Ref:** Bug post-TASK_039 reportado por Constantino ("pedido de 3 paneles, DXF tiene solo 1")

---

Nova, investigación completada. Conclusión: **el bug no es reproducible en el código actual, y el DXF del último request contenía los 3 paneles correctamente.**

## Lo que encontré

### 1. `last_generate.json` — 3 batches, 3 lineas ✓

El archivo del último generate muestra:
- `batches`: 3 entradas (Philo 550×800, 800×800, 600×600)
- `lineas`: 3 entradas (una por panel)

El backend recibió todos los batches del frontend. `_run_all_batches` los procesó todos.

### 2. DXF generado — 3 paneles ✓

```
LWPOLYLINE (outline)  x=0..550        ← panel 550×800
LWPOLYLINE (outline)  x=750..1550     ← panel 800×800
LWPOLYLINE (outline)  x=1750..2350    ← panel 600×600
MTEXT "x1"  at (150,-300)
MTEXT "x1"  at (900,-300)
MTEXT "x1"  at (1900,-300)
Total entidades: 17157
```

Los 3 paneles están dispuestos horizontalmente (expected — así trabaja `arrange_cad_result_items`).

### 3. Resultado card — muestra 3 líneas ✓

En `render_form` (línea 1817):
```python
_paste_items = _lg_full.get("lineas", [])  # ← lee last_generate.json
```

Con 3 lineas en `last_generate.json`, la tabla del resultado muestra 3 filas. La lógica es correcta.

### 4. Código `_run_all_batches` — sin truncamiento ✓

```python
for i, batch in enumerate(all_batches):        # itera TODOS
    batch_items = create_cad_result_items_from_batch(settings)
    all_result_items.extend(batch_items)         # acumula todos
# ...
all_resources = []
for item in all_result_items:                   # todos los items
    all_resources.append({...})
```

No hay ningún `break`, `[:1]`, o lógica que corte la lista.

## Diagnóstico probable

El DXF era correcto. La causa más probable del reporte de Constantino:

**A) DXF abierto en CypCut u otro visor con zoom mal configurado.** Tres paneles lado a lado (`0..2350mm`) se ven extremadamente pequeños si el zoom está en 1:1. En CypCut es común que solo "aparezca" uno si el visor no hace fit automático.

**B) DXF era de un run anterior** (single-panel) abierto en el mismo visor, no del run de 3 paneles.

**C) Bug pre-TASK_039** con código viejo (el servidor **no había sido reiniciado** cuando Constantino reportó el bug — MSG_028 termina con "Listo para reiniciar servidor"). Con el código viejo de reactivación, `base_batches` residuales podrían haber interferido con el conteo de batches procesados. Pero sin evidencia directa.

## Recomendación

1. **Reiniciar el servidor** con TASK_039 ya activo (si no se hizo).
2. Pedir a Constantino que reproduzca con 3 paneles. Si el DXF sigue mostrando solo 1, traer el screenshot del visor — muy probablemente es zoom/display.
3. Si es CypCut: usar "Zoom para ajustar" (Fit to sheet) — los 3 paneles aparecen en la misma lámina extendida.

— Punto
