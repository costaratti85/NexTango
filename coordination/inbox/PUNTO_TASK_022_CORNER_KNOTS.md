# PUNTO_TASK_022 — Conversor splines: detectar esquinas y no generar arcos espurios

**De:** Nova  
**Para:** Punto  
**Fecha:** 2026-06-17  
**Prioridad:** Media — mejora al conversor, no bloquea el sprint actual  

---

## Problema

En nodos donde la spline tiene una discontinuidad de tangente (esquinas o cúspides), el conversor genera círculos/arcos espurios. El algoritmo de fitting no sabe que hay un salto de dirección y fitea un arco que cruza el nodo, produciendo geometría inválida.

---

## Contexto técnico

**Archivo:** `tools/dxf_spline_to_arcs.py`  
**Función principal:** `discretize_and_convert_spline()` (línea ~103)

El algoritmo actual:
1. Llama `spline_entity.flattening(tolerance)` → lista plana de puntos, sin metadata sobre continuidad
2. Para cada posición `i`, prueba extender el segmento hasta `i+50` buscando el tramo más largo que entra en `tolerance` con `fit_arc_to_points()`
3. **El problema está en el paso 2:** el sliding window no sabe que algunos puntos son nodos de "esquina" donde la tangente salta. Puntos a ambos lados de una esquina pueden quedar casualmente sobre un mismo círculo (especialmente si la esquina es leve), y el fitter los acepta como arco válido.

**Dónde está la ventana de fitting:**
```python
# línea ~141-153
i = 0
while i < len(points) - 2:
    best_end = i + 2
    best_result = None
    
    for end in range(i + 2, min(i + 50, len(points))):
        segment = points[i:end+1]
        result = fit_arc_to_points(segment, tolerance)
        if result:
            best_result = result
            best_end = end
        else:
            if end == i + 2:
                break
```

---

## Solución propuesta

### Paso 1: Pre-detectar esquinas en la lista de puntos

Antes del loop de fitting, recorrer los puntos y detectar aquellos donde el ángulo entre la cuerda entrante y la cuerda saliente supera un umbral:

```python
def _find_corner_indices(points, corner_threshold_deg=20.0):
    """
    Devuelve un set de índices donde hay un cambio brusco de dirección.
    Un índice i es esquina si el ángulo entre (p[i]-p[i-1]) y (p[i+1]-p[i]) 
    supera corner_threshold_deg.
    """
    corners = set()
    for i in range(1, len(points) - 1):
        dx1 = points[i].x - points[i-1].x
        dy1 = points[i].y - points[i-1].y
        dx2 = points[i+1].x - points[i].x
        dy2 = points[i+1].y - points[i].y
        len1 = math.sqrt(dx1*dx1 + dy1*dy1)
        len2 = math.sqrt(dx2*dx2 + dy2*dy2)
        if len1 < 1e-9 or len2 < 1e-9:
            continue
        cos_a = (dx1*dx2 + dy1*dy2) / (len1 * len2)
        cos_a = max(-1.0, min(1.0, cos_a))
        angle = math.degrees(math.acos(cos_a))
        if angle > corner_threshold_deg:
            corners.add(i)
    return corners
```

### Paso 2: Limitar la ventana de fitting

En el loop de fitting, calcular `max_end` como el índice de la próxima esquina a partir de `i`. El segmento `points[i:end+1]` nunca debe cruzar un índice de esquina:

```python
corners = _find_corner_indices(points)

# Precomputar para cada posición i el próximo límite de esquina
# (la primera esquina con índice > i)
def _next_corner_limit(i, corners, n):
    """Devuelve el índice máximo (exclusive) hasta donde se puede extender desde i."""
    for c in sorted(corners):
        if c > i:
            return c  # no incluir el punto de esquina en el arco
    return n

i = 0
while i < len(points) - 2:
    corner_limit = _next_corner_limit(i, corners, len(points))
    
    best_end = i + 2
    best_result = None
    
    for end in range(i + 2, min(i + 50, corner_limit, len(points))):
        segment = points[i:end+1]
        result = fit_arc_to_points(segment, tolerance)
        if result:
            best_result = result
            best_end = end
        else:
            if end == i + 2:
                break
    
    if best_result:
        # ... lógica existente ...
        i = best_end
    else:
        # ... lógica existente (emitir LINE) ...
        i += 1
    
    # Si el siguiente punto es una esquina, avanzar sin intentar fitting
    if i in corners and i < len(points) - 1:
        # Emitir LINE hasta el punto de esquina (ya se emitió hasta i-1)
        # El loop normal se encarga; solo asegurarse de no intentar fitting cruzando
        pass
```

### Nota sobre el umbral

`corner_threshold_deg=20.0` es un valor de partida razonable. Ángulos menores de 20° son transiciones suaves que el arco puede absorber dentro de la tolerancia normal. Si en pruebas aparecen falsos positivos (esquinas detectadas donde no hay discontinuidad visible), aumentar a 30°. Si se generan arcos espurios en ángulos pequeños, bajar a 10°.

---

## Criterio de aceptación

1. Un DXF con splines que tengan esquinas explícitas (polígono redondeado, letra con vértices, o arco+línea+arco) genera arcos que no cruzan las esquinas — los arcos terminan antes de la esquina y la siguiente entidad empieza después
2. Una spline continua sin esquinas (Philo, Subte) sigue generando el mismo resultado que antes
3. No se requiere cambiar la interfaz gráfica ni los tests de integración
4. Reportar en `coordination/reports/PUNTO_TASK_022_REPORT.md` con: umbral elegido, casos de prueba usados, antes/después de la cantidad de arcos espurios

---

## Alternativa más precisa (opcional)

Si la spline es un NURBS y Punto tiene acceso a `spline_entity.knots` y `spline_entity.degree`, los nodos de esquina se pueden detectar por multiplicidad de knot = degree. Esto es matemáticamente exacto pero más complejo de implementar. La detección por ángulo de cuerdas es suficiente para los archivos que maneja el sistema.
