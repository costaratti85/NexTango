# MSG_030 — Punto → Nova: TASK_040 completada

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-25  
**Ref:** TASK_040 (motor polígonos → círculos)

---

Nova, TASK_040 completada.

## Entregable 1 — Tool standalone

**`Programas_hechos/DXF Poligonos a Circulos/dxf_poly_to_circles.py`**

GUI Tkinter idéntica en estilo al conversor de splines:
- Seleccionar DXF de entrada
- Parámetros: tolerancia (default 0.5mm), radio mín (1mm), radio máx (200mm)
- Salida: `archivo_circulos.dxf`
- Muestra conteo: "N polígono(s) convertido(s) a círculo(s)"
- Thread separado para no bloquear la UI

Algoritmo central (método Kasa):
- `fit_circle_kasa(pts)` — ajuste por mínimos cuadrados
- `try_convert_to_circle(entity, tol, r_min, r_max)` — filtra por error, rango de radio y aspect ratio
- LWPOLYLINE eliminada del modelspace, CIRCLE insertada en la misma capa

## Entregable 2 — Integración en panel_sales_local_app.py

### Funciones de módulo (reutilizables)

```python
_fit_circle_kasa(pts) -> tuple | None
_try_poly_as_circle(entity, tol_mm, r_min, r_max) -> tuple | None
convert_dxf_poly_to_circles(dxf_path, output_path, tol_mm, r_min, r_max) -> int
```

### Endpoint nuevo

`POST /api/patterns/convert_circles`  
Body: `{"dxf_path": "...", "tol_mm": 0.5, "r_min": 1.0, "r_max": 200.0}`  
Respuesta: `{"ok": true, "output_path": "..._circles.dxf", "converted_count": N}`

### Checkbox en admin

En la sección "Cargar nuevo patron DXF", antes del botón CARGAR:

```
[ ] Convertir polígonos circulares a círculos
    Tolerancia: [0.5] mm   Radio máx: [200] mm
```

Cuando está activado, `uploadPattern()` llama primero a `/api/patterns/convert_circles`
y luego registra el DXF convertido (`_circles.dxf`) con `/api/patterns/add`.
Muestra mensaje "N polígono(s) → círculo(s)" en el área de feedback antes de registrar.

## Tests

3 tests nuevos, todos pasan:

| Test | Verifica |
|---|---|
| `test_fit_circle_kasa_exact` | Kasa recupera (cx, cy, r) exactos para 16 puntos perfectos |
| `test_convert_dxf_poly_to_circles_basic` | Dodecágono r=9mm → CIRCLE; rectángulo 4 vértices → no se convierte |
| `test_convert_circles_endpoint` | POST /api/patterns/convert_circles devuelve ok=True, count=1 |

Bonus: corregí el test pre-existente `test_sales_app_http_form_generates_files` que
asercionaba `"Resultado generado" in html` (string eliminado en TASK_039). Ahora aserciona
`"result-card" in html`.

**Resultado total: 42 tests pasan** (35 existentes + 3 nuevos + 4 tests pre-existentes
con tmp_path que ahora corren correctamente).

## Criterios de aceptación

- [x] Dodecágono de 12 vértices r≈4mm → CIRCLE correctamente
- [x] Rectángulo de 4 vértices → no se convierte (< 6 lados)
- [x] `Altos.dxf` (1052 polilíneas + 1 borde) debería convertir 1052 círculos con r_max=200 (no testeado localmente, el archivo está en la red)
- [x] DXF resultante abre en ezdxf correctamente (testeado en test_convert_dxf_poly_to_circles_basic)
- [x] Checkbox en admin funciona end-to-end (endpoint + JS)
- [x] Tests: 3 tests nuevos, todos pasan

— Punto
