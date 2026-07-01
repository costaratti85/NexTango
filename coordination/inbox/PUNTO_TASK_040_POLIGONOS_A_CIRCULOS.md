# PUNTO_TASK_040 — Motor: polígonos aproximados → círculos reales

**Asignado a:** Punto  
**Prioridad:** Media  
**Fecha:** 2026-06-25  
**Referencia:** archivo de muestra analizado por Nova

---

## Contexto

Cuando un dibujo se escanea, se convierte a imagen y luego se vectoriza, los
círculos originales quedan representados como polilíneas cerradas de N vértices
(dodecágonos, hexadecágonos, etc.). El motor de corte los trata como polígonos,
no como círculos — mayor cantidad de entidades, peor calidad de corte, archivos
más pesados.

Nova analizó el archivo de muestra `Altos.dxf` (red: `\\190.190.190.9\ventas\...\Paneles Decorativos\Altos.dxf`):

```
1053 LWPOLYLINE cerradas
  386 × 12 vértices  → radio ~4mm
  666 × 16 vértices  → radio ~6mm
    1 × 4 vértices   → rectángulo borde (descartar por radio > umbral)

Error de ajuste: máx 0.27mm, promedio 0.21mm
```

El ajuste de círculo por mínimos cuadrados (método Kasa) recupera los círculos
originales con error sub-milimétrico.

---

## Entregables

### 1. Tool standalone: `Programas_hechos/DXF Polígonos a Círculos/dxf_poly_to_circles.py`

GUI Tkinter similar al conversor de splines. Flujo:
- Seleccionar DXF de entrada
- Parámetros: tolerancia de ajuste (default 0.5mm), radio mínimo (default 1mm), radio máximo (default 200mm)
- Convertir: detecta polilíneas cerradas que ajustan a círculo dentro de tolerancia → las reemplaza por entidades CIRCLE
- Guardar DXF de salida
- Mostrar conteo: "N polígonos → N círculos"

El algoritmo central:

```python
def fit_circle_kasa(pts):
    """Least-squares circle fit (Kasa method). Returns (cx, cy, r, max_error)."""
    n = len(pts)
    sx=sy=sxx=syy=sxy=sx3=sy3=sxxy=sxyy = 0
    for x, y in pts:
        sx+=x; sy+=y; sxx+=x*x; syy+=y*y; sxy+=x*y
        sx3+=x**3; sy3+=y**3; sxxy+=x*x*y; sxyy+=x*y*y
    A = 2*(sx*sx - n*sxx)
    B = 2*(sx*sy - n*sxy)
    C = 2*(sy*sy - n*syy)
    D = sx*sxx - n*sx3 + sx*syy - n*sxyy
    E = sy*sxx - n*sxxy + sy*syy - n*sy3
    det = A*C - B*B
    if abs(det) < 1e-10:
        return None
    cx = (D*C - B*E) / det
    cy = (A*E - B*D) / det
    r = math.sqrt(sum((x-cx)**2 + (y-cy)**2 for x,y in pts) / n)
    max_err = max(abs(math.sqrt((x-cx)**2 + (y-cy)**2) - r) for x,y in pts)
    return cx, cy, r, max_err

def try_convert_to_circle(lwpolyline, tol_mm, r_min, r_max):
    """Returns (cx, cy, r) if the polyline fits a circle, else None."""
    if not lwpolyline.closed:
        return None
    pts = [(v[0], v[1]) for v in lwpolyline.vertices()]
    if len(pts) < 6:   # menos de 6 lados → no es un círculo approximado
        return None
    res = fit_circle_kasa(pts)
    if res is None:
        return None
    cx, cy, r, max_err = res
    if max_err > tol_mm:
        return None
    if r < r_min or r > r_max:
        return None
    # Verificar que sea razonablemente redondo (no un rectángulo con esquinas redondeadas)
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    w = max(xs) - min(xs); h = max(ys) - min(ys)
    if min(w, h) < 0.5 * max(w, h):   # aspect ratio muy alejado de 1:1
        return None
    return cx, cy, r
```

Al convertir: eliminar la LWPOLYLINE y agregar `msp.add_circle(center=(cx,cy,0), radius=r)` en la misma capa.

### 2. Integración en el cargador de patrones (`panel_sales_local_app.py`)

En la pantalla de admin "Cargar nuevo patrón DXF", agregar un checkbox:

```
[ ] Convertir polígonos circulares a círculos
    Tolerancia: [0.5] mm   Radio máx: [200] mm
```

Cuando está activado, al guardar el patrón el backend corre el mismo algoritmo
sobre el DXF antes de almacenarlo en `uploaded_patterns/`.

El handler de upload ya existe (`_handle_pattern_upload` o similar) — agregar el
paso de conversión ahí, condicional al checkbox.

---

## Criterios de aceptación

- El archivo `Altos.dxf` de muestra se convierte: 1052 LWPOLYLINE → 1052 CIRCLE
  (la polilínea del borde queda intacta por tener radio > 200mm)
- El DXF resultante abre correctamente en un visor (LibreCAD, ezdxf, etc.)
- Los círculos convertidos tienen el centro y radio correctos (error < tolerancia)
- La GUI muestra el conteo de conversiones
- El checkbox en el cargador de patrones funciona end-to-end
- Tests: al menos uno que verifique que una LWPOLYLINE de 12 vértices que aproxima
  un círculo de radio 9mm se convierte correctamente

---

## No necesita

- No tocar el motor de paneles decorativos
- No integrar con ERPNext
- No modificar archivos de cotización ni de presupuesto

---

Reporte en `coordination/channel/Nova/` al completar.

— Nova
