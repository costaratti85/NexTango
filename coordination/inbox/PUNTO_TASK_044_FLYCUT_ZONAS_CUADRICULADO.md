# PUNTO_TASK_044 — Segmentación en zonas flycut para Cuadriculado (modo Cuadrado)

**Asignado a:** Punto  
**Prioridad:** Media  
**Fecha:** 2026-07-01  
**Referencia:** Pedido de Constantino — investigación Nova sobre CypCut flycut

---

## Contexto

CypCut tiene 17 capas DXF (0–16) que procesa en orden secuencial. Si los agujeros cuadrados de un panel van cada uno en la capa de su zona geográfica, CypCut completa el flycut de cada zona antes de pasar a la siguiente. Esto evita la distorsión térmica acumulada que ocurre cuando se cortan todas las líneas horizontales del panel completo y luego todas las verticales.

**Solo aplica a Cuadriculado en modo Cuadrado.** Los círculos (tresbolillo, cuadriculado círculo) van todos en capa 0 como hasta ahora — el flycut de círculos no tiene el problema de distorsión.

---

## Algoritmo de segmentación

```python
import math

def calcular_zonas(W_mm: float, H_mm: float, target: float = 250.0):
    """
    Divide el área del panel en n_cols × n_rows zonas.
    Devuelve n_cols, n_rows, zone_w, zone_h, total_zonas.
    """
    n_cols = math.ceil(W_mm / target)
    n_rows = math.ceil(H_mm / target)
    zone_w = W_mm / n_cols
    zone_h = H_mm / n_rows
    return n_cols, n_rows, zone_w, zone_h, n_cols * n_rows

def zona_de_agujero(x: float, y: float, n_cols: int, n_rows: int,
                    zone_w: float, zone_h: float) -> int:
    """
    Número de capa (0-indexed) para un agujero centrado en (x, y).
    x, y relativos al origen del área perforada.
    """
    col_zona = min(int(x / zone_w), n_cols - 1)
    row_zona = min(int(y / zone_h), n_rows - 1)
    return row_zona * n_cols + col_zona
```

---

## Distribución en archivos DXF

CypCut soporta máximo **16 capas útiles** (capa 0 a 15; la 16 existe pero se reserva).

```
total_zonas ≤ 16  →  1 archivo DXF, capas 0 a (total_zonas - 1)
total_zonas > 16  →  múltiples DXFs, cada uno con ≤ 16 zonas

Agrupación: zonas 0-15 → archivo 1, zonas 16-31 → archivo 2, etc.
La capa en cada archivo = zona_global % 16
```

**Ejemplos:**

| Panel (mm) | n_cols | n_rows | Zonas | Archivos |
|---|---|---|---|---|
| 500×500 | 2 | 2 | 4 | 1 (capas 0-3) |
| 1000×1000 | 4 | 4 | 16 | 1 (capas 0-15) |
| 1220×2440 | 5 | 10 | 50 | 4 (16+16+16+2) |
| 1500×3000 | 6 | 12 | 72 | 5 (16+16+16+16+8) |

---

## Nomenclatura de archivos

Un solo DXF (caso ≤16 zonas):
```
panel_cuadriculado_500x500.dxf          ← nombre actual, sin cambios
```

Múltiples DXFs (caso >16 zonas):
```
panel_cuadriculado_1220x2440_flycut_1de4.dxf
panel_cuadriculado_1220x2440_flycut_2de4.dxf
panel_cuadriculado_1220x2440_flycut_3de4.dxf
panel_cuadriculado_1220x2440_flycut_4de4.dxf
```

Se ofrecen como descarga en un ZIP:
```
panel_cuadriculado_1220x2440_flycut.zip
```

---

## Cambios en el código

### 1. Generador DXF de Cuadriculado (`Programas_hechos/Panel Decorativo/`)

En la función que emite los agujeros cuadrados al DXF, reemplazar la asignación de capa fija por la capa de zona:

```python
# ANTES:
ln.dxf.layer = "0"

# DESPUÉS:
zona = zona_de_agujero(cx, cy, n_cols, n_rows, zone_w, zone_h)
capa_en_archivo = zona % 16
ln.dxf.layer = str(capa_en_archivo)
```

El generador devuelve una lista de archivos DXF en lugar de uno solo cuando hay más de 16 zonas. Cada archivo contiene solo los agujeros de sus 16 zonas correspondientes (filtrado por `zona // 16 == archivo_idx`).

### 2. Backend de la app (`panel_sales_local_app.py`)

En el handler de generación de Cuadriculado cuadrado:
- Si resultado es 1 DXF → descarga directa como hasta ahora
- Si resultado es N DXFs → empaquetar en ZIP y ofrecer descarga del ZIP
- Incluir nota en la UI: *"El panel fue dividido en X zonas flycut distribuidas en N archivos DXF. Cargar en CypCut en orden."*

### 3. Solo para Cuadriculado modo Cuadrado

**No modificar:**
- Cuadriculado modo Círculo (capa 0, como siempre)
- Tresbolillo (capa 0, como siempre)
- Patrones personalizados subidos por el usuario

---

## Tests mínimos

```python
def test_zonas_panel_pequeno():
    # 500×500mm → 2×2 = 4 zonas → 1 DXF
    n_cols, n_rows, zw, zh, total = calcular_zonas(500, 500)
    assert n_cols == 2
    assert n_rows == 2
    assert total == 4

def test_zonas_panel_grande():
    # 1220×2440mm → 5×10 = 50 zonas → 4 DXFs
    n_cols, n_rows, zw, zh, total = calcular_zonas(1220, 2440)
    assert n_cols == 5
    assert n_rows == 10
    assert total == 50
    assert math.ceil(total / 16) == 4

def test_asignacion_zona_esquinas():
    # Verificar que los agujeros en las 4 esquinas van a zonas distintas
    # en un panel 500×500 con 4 zonas
    n_cols, n_rows, zw, zh, _ = calcular_zonas(500, 500)
    assert zona_de_agujero(125, 125, n_cols, n_rows, zw, zh) == 0  # inf-izq
    assert zona_de_agujero(375, 125, n_cols, n_rows, zw, zh) == 1  # inf-der
    assert zona_de_agujero(125, 375, n_cols, n_rows, zw, zh) == 2  # sup-izq
    assert zona_de_agujero(375, 375, n_cols, n_rows, zw, zh) == 3  # sup-der
```

---

## Criterios de aceptación

- [ ] Cuadriculado modo Cuadrado asigna cada agujero a la capa de su zona geográfica
- [ ] Panel ≤16 zonas → 1 DXF, descarga directa (comportamiento actual preservado)
- [ ] Panel >16 zonas → ZIP con N DXFs nombrados `*_flycut_XdeN.dxf`
- [ ] La UI muestra mensaje informativo cuando se generan múltiples archivos
- [ ] Cuadriculado modo Círculo, Tresbolillo y patrones custom NO se modifican
- [ ] Los 3 tests pasan

## No necesita

- Segmentación para círculos ni tresbolillo
- Integración con CypCut (el operador configura el layer mapping una vez)
- Cambios en presupuesto ni en cálculo de recursos

---

Reportar en `coordination/channel/Nova/` al completar.

— Nova
