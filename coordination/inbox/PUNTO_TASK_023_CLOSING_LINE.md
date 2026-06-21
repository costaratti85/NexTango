# PUNTO_TASK_023 — Figura de borde: el cierre usa 2 líneas en vez de 1

**De:** Nova  
**Para:** Punto  
**Fecha:** 2026-06-18  
**Prioridad:** Alta — afecta la geometría de corte de figuras de borde  

---

## Síntoma

Cuando una figura del patrón se monta sobre el margen y debe cortarse, los dos nodos libres resultantes (los puntos donde la figura intersecta el margen) deberían unirse con **una sola línea recta**.

En cambio, en algunos casos se unen con **dos líneas rectas**, usando un tercer nodo como punto intermedio. Ese tercer nodo es un nodo existente de la figura (o coincide con uno).

Correcto:
```
P_libre_A ——————————————— P_libre_B
```

Incorrecto (lo que pasa):
```
P_libre_A ——— nodo_intermedio ——— P_libre_B
```

---

## Código responsable

**Archivo:** `Programas_hechos/Panel Decorativo/geometry/polyline_closer.py`  
**Función:** `boundary_path(self, start, end)` (línea 66)

Esta función decide cómo conectar el último punto de la figura clipeada (`last`) con el primero (`first`) — es decir, cómo cerrar la figura a lo largo del margen.

La lógica actual:

```python
def boundary_path(self, start, end):
    side_start = self.point_side(start)   # LEFT / RIGHT / BOTTOM / TOP / None
    side_end   = self.point_side(end)

    if side_start is None or side_end is None:
        return [end]                        # línea directa

    if side_start == side_end:
        return [end]                        # misma cara → línea directa ✓

    corner = self.corner_between(side_start, side_end)   # esquina del margen

    if corner is not None:
        if points_close(start, corner) or points_close(end, corner):
            return [end]
        return [corner, end]               # ← ESTO genera 2 líneas pasando por la esquina
    
    return [end]
```

**El caso problemático:** cuando `start` y `end` están en lados ADYACENTES del rectángulo de margen (ej. uno en LEFT y el otro en BOTTOM), `corner_between()` devuelve la esquina del margen (xmin, ymin), y la función retorna `[corner, end]` → 2 segmentos.

Esa esquina del margen **coincide con un nodo del patrón teselado** en ciertos posicionamientos de tile, razón por la cual Constantino la ve como "un nodo existente de la figura".

---

## Hipótesis de la causa

La lógica de `corner_between` fue diseñada para que el cierre SIGA EL BORDE del margen en casos donde las dos intersecciones están en caras distintas (por ejemplo, la figura pasa por la esquina del panel). Esto es geométricamente correcto si el objetivo es que la línea de cierre sea exactamente sobre el borde del margen.

Sin embargo, Constantino dice que el cierre debe ser **siempre una sola recta**. Eso significa que el cierre diagonal (de LEFT a BOTTOM en línea directa) es aceptable aunque no siga exactamente la frontera del margen.

---

## Lo que debe investigar Punto

1. **¿En qué proporción aparece el caso adyacente?** Contar cuántos cierres en un panel Philo de 300×300mm terminan con los dos extremos en lados adyacentes. ¿Es un caso raro o frecuente?

2. **¿La esquina del cierre coincide con un nodo del patrón?** Para los casos adyacentes, verificar si `corner_between()` devuelve un punto que ya existe en la polilínea de la figura. Eso confirmaría el síntoma de "nodo existente".

3. **¿El cierre directo (diagonal) es admisible para laser cutting?** Si la línea va de LEFT a BOTTOM en diagonal, ¿ese corte diagonal es correcto para el panel? La respuesta probable es sí: el cierre es una línea de corte que no necesita seguir el borde exacto del margen.

---

## Fix probable

Si el cierre diagonal es admisible, el fix es simple: **siempre retornar `[end]`** en `boundary_path`, eliminando el routing por esquina.

```python
def boundary_path(self, start, end):
    # El cierre siempre es una sola línea recta entre los dos nodos libres.
    return [end]
```

Esto simplifica el código, elimina el nodo intermedio, y produce el comportamiento que Constantino describe como correcto.

Si el cierre diagonal NO es admisible en algún caso (Punto debe confirmarlo), la alternativa es:

```python
def boundary_path(self, start, end):
    side_start = self.point_side(start)
    side_end   = self.point_side(end)

    if side_start is None or side_end is None or side_start == side_end:
        return [end]

    corner = self.corner_between(side_start, side_end)
    if corner is None:
        return [end]

    # Solo insertar la esquina si no coincide con ningún punto ya presente
    # en la polilínea. Si coincide, usar línea directa.
    return [corner, end]  # o [end] si se decide eliminar el corner routing
```

---

## Criterio de aceptación

1. Las figuras de borde clipeadas cierran con **una sola línea recta** entre los dos nodos libres sobre el margen
2. El patrón Philo y el patrón Subte generan figuras de borde visualmente correctas
3. No se introducen nuevas intersecciones incorrectas en los tiles interiores
4. Tests existentes pasan
5. Reportar en `coordination/reports/PUNTO_TASK_023_REPORT.md` indicando: qué proporción de figuras tenían el caso adyacente, si el fix diagonal fue suficiente, y si se encontró el nodo coincidente esperado
