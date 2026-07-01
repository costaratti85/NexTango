# PUNTO_TASK_043 — Nueva página: Plegados Preseteados (primer preset: Bandeja)

**Asignado a:** Punto  
**Prioridad:** Alta  
**Fecha:** 2026-06-30  
**Referencia:** Pedido de Constantino

---

## Contexto

El sistema va a tener múltiples páginas de productos (paneles, plegados, caños, etc.).
La página de **Plegados Preseteados** es la segunda página que se construye, después de Paneles Decorativos.

La app local es transitoria — el destino final es ERPNext. No sobre-ingenierizar.

Cada preset de plegado puede tener una `cara_principal` definida. Esto es un campo de datos
por ahora; la integración con Paneles Decorativos (para usarlo como contorno exterior) es futura.

---

## Qué construir

### 1. Motor de geometría: `Programas_hechos/Plegados/bandeja.py` — NUEVO

```python
"""
Desarrollo plano de una bandeja (cajón de 4 lados plegados).

Parámetros de entrada (todos en mm):
    ancho_int   — ancho interior de la bandeja terminada
    largo_int   — largo interior de la bandeja terminada
    alto        — altura de los lados
    espesor     — espesor de chapa

Fórmulas:
    blank_ancho = ancho_int + 2 * alto - 4 * espesor
    blank_largo = largo_int + 2 * alto - 4 * espesor
    despunte    = alto - espesor          ← lado del cuadrado cortado en cada punta
"""
```

#### Geometría del blank (12 vértices, CCW, centrado en origen)

```
Sean BW = blank_ancho, BL = blank_largo, D = despunte

Vértices en orden CCW:
  1. (-BW/2,       -BL/2 + D)
  2. (-BW/2 + D,   -BL/2 + D)   ← esquina interior inf-izq
  3. (-BW/2 + D,   -BL/2      )
  4. ( BW/2 - D,   -BL/2      )
  5. ( BW/2 - D,   -BL/2 + D  )  ← esquina interior inf-der
  6. ( BW/2,       -BL/2 + D  )
  7. ( BW/2,        BL/2 - D  )
  8. ( BW/2 - D,    BL/2 - D  )  ← esquina interior sup-der
  9. ( BW/2 - D,    BL/2      )
 10. (-BW/2 + D,    BL/2      )
 11. (-BW/2 + D,    BL/2 - D  )  ← esquina interior sup-izq
 12. (-BW/2,        BL/2 - D  )
  → volver a 1
```

#### Función pública

```python
def calcular_bandeja(ancho_int, largo_int, alto, espesor):
    """
    Devuelve un dict con:
      blank_ancho, blank_largo, despunte,
      vertices: list of (x, y) — 12 puntos CCW,
      cara_principal: {"ancho": ancho_int, "largo": largo_int}  ← para uso futuro
    """
```

#### DXF

Generar un archivo DXF con la polilínea cerrada de 12 vértices en capa `"CORTE"`.
Mismo patrón que el exportador de paneles (`dxf/exporter.py`).

---

### 2. Cálculo de recursos

```python
def calcular_recursos_bandeja(ancho_int, largo_int, alto, espesor, material_row):
    """
    material_row: fila de MATERIAL_DEFAULTS (tiene densidad_kg_m2, velocidad_corte_mm_s)

    Retorna:
      kg_chapa          — float
      tiempo_laser_s    — float (segundos)
      perforaciones     — int (siempre 0 para bandeja sin perforar)
      plegados          — int (siempre 4)
    """
    BW = ancho_int + 2*alto - 4*espesor
    BL = largo_int + 2*alto - 4*espesor
    D  = alto - espesor

    # Área del blank (mm²) = rectángulo menos 4 cuadrados de esquina
    area_mm2 = BW * BL - 4 * D * D

    # Kg de chapa
    kg_chapa = (area_mm2 / 1_000_000) * material_row["densidad_kg_m2"]

    # Perímetro del contorno de 12 lados
    # Matemáticamente igual a 2*(BW+BL) — los despuntes no cambian el perímetro total
    perimetro_mm = 2 * (BW + BL)

    # Tiempo de laser
    tiempo_laser_s = perimetro_mm / material_row["velocidad_corte_mm_s"]

    return {
        "kg_chapa": round(kg_chapa, 3),
        "tiempo_laser_s": round(tiempo_laser_s, 1),
        "perforaciones": 0,
        "plegados": 4,
    }
```

---

### 3. Página en `panel_sales_local_app.py`

Agregar una nueva sección/página "Plegados" dentro de la misma app Flask.
Nueva ruta: `/plegados` (o navegación interna similar a la de paneles).

#### 3a. Galería de presets

Por ahora un solo card: **Bandeja**.
Thumbnail: SVG inline que muestre la silueta de 12 lados (cruz/aspa).

#### 3b. Formulario de la bandeja

```
Material:       [dropdown — misma tabla que paneles]
Espesor:        [dropdown — filtrado por material]

Ancho interior: [número, mm]
Largo interior: [número, mm]
Alto lados:     [número, mm]
Cantidad:       [entero]
```

Al confirmar, mostrar resumen de recursos calculados:

```
Blank:            XXX × YYY mm
Despunte:         Z mm
─────────────────────────────────────────────────
Kg de chapa:      X.XXX kg
Tiempo de laser:  X.X s  (= X.X min)
Perforaciones:    0
Plegados:         4
```

#### 3c. Sección de costos y precio

Pre-cargar desde configuración admin (ver §4). Editable por el vendedor:

```
Costo chapa:    $ ___ / kg          × X.XXX kg     = $ ___
Costo laser:    $ ___ / min         × X.X min       = $ ___
Costo plegado:  $ ___ / doblez      × 4 dobleces    = $ ___
                                            ─────────
                                    SUBTOTAL  = $ ___
                                    × cantidad
                                    TOTAL     = $ ___
```

#### 3d. Botón "Generar DXF"

Descarga el DXF del desarrollo plano.
Nombre sugerido: `Bandeja_{ancho}x{largo}x{alto}_{material}_{calibre}.dxf`

---

### 4. Admin: nuevos costos para plegados

En la sección admin existente de `panel_sales_local_app.py`, agregar:

```
Costo por doblez de plegadora:   $ ___ / doblez
```

(Los costos de chapa y laser ya existen — reutilizar los mismos.)

---

### 5. Tests mínimos

Al menos 2 tests en `tests/`:

```python
def test_calcular_bandeja_dimensiones():
    # Bandeja 300×200×50mm, espesor 1.25mm
    # blank_ancho = 300 + 100 - 5 = 395mm
    # blank_largo = 200 + 100 - 5 = 295mm
    # despunte = 50 - 1.25 = 48.75mm

def test_calcular_recursos_bandeja_kg():
    # Verificar kg_chapa con un material conocido de MATERIAL_DEFAULTS
```

---

## Concepto `cara_principal` (para uso futuro — solo guardar el dato)

Cada preset de plegado tiene una `cara_principal` que define el área perforable.
Para la bandeja: `{"ancho": ancho_int, "largo": largo_int}` — el rectángulo base.

No implementar la integración con paneles ahora. Solo asegurarse de que el dict
devuelto por `calcular_bandeja()` incluya el campo `cara_principal`.

---

## Criterios de aceptación

- [ ] `/plegados` muestra la galería con la card de Bandeja
- [ ] El formulario calcula y muestra los 4 recursos correctamente
- [ ] Los costos se pre-cargan desde admin y son editables
- [ ] El total se calcula correctamente (recursos × costos × cantidad)
- [ ] Botón "Generar DXF" descarga el desarrollo plano correcto
- [ ] Al menos 2 tests pasan
- [ ] No se rompen los tests existentes de paneles

## No necesita

- Integración con ERPNext
- Perforaciones en la bandeja (eso es futuro, cuando se conecte con paneles)
- Otros presets además de Bandeja

---

Reportar en `coordination/channel/Nova/` al completar.

— Nova
