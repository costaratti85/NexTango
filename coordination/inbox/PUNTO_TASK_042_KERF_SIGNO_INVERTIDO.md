# PUNTO_TASK_042 — Bug: kerf con signo invertido en CostADCAM Claude

**Asignado a:** Punto  
**Prioridad:** Alta  
**Fecha:** 2026-06-30  
**Referencia:** Reporte de Constantino

---

## El problema

En `C:\Python\CostADCAM Claude\cad\kerf.py`, el offset kerf está invertido:
- Las líneas **exteriores** se corren **hacia adentro** (deberían ir 1mm hacia afuera).
- Las líneas **interiores** se corren **hacia afuera** (deberían ir 0.5mm hacia adentro).

## Causa raíz

En `_offset_entity`, el offset `d` desplaza la entidad **a la derecha del sentido de avance**. Para un contorno exterior recorrido en CCW (sentido antihorario, que es lo que produce CypCut), "derecha" apunta **hacia el interior** de la figura. Por eso:

- `d = +1.0` en exterior CCW → mueve las líneas hacia adentro → la pieza **se achica** (incorrecto).
- `d = -0.5` en interior → mueve las líneas hacia afuera → el agujero **crece** (incorrecto).

## Archivo a modificar

`C:\Python\CostADCAM Claude\cad\kerf.py`

## Fix propuesto

En `_offset_piece_entities` (aproximadamente línea 511), cambiar el signo de `d`:

```python
# ANTES (bug):
d = (-0.5) if (force_interior or i != exterior_idx) else 1.0

# DESPUÉS (fix):
d = (0.5) if (force_interior or i != exterior_idx) else -1.0
```

Y para los círculos (aproximadamente línea 529), también negar:

```python
# ANTES:
d = -0.5 if (ext_pts and _point_in_polygon((cx, cy), ext_pts)) else 1.0

# DESPUÉS:
d = 0.5 if (ext_pts and _point_in_polygon((cx, cy), ext_pts)) else -1.0
```

**Nota sobre círculos:** `_offset_circle` hace `r + offset`. Para un agujero circular, queremos que el radio del path programado sea menor (para que el plasma deje el agujero del tamaño correcto). Con `d=+0.5` el radio crece → revisar si esto es correcto para la convención de CypCut. Si los círculos ya funcionaban bien, posiblemente solo corresponde corregir las cadenas de líneas/arcos y no los círculos.

## Verificación sugerida

1. Tomar un DXF de prueba con:
   - Un perfil exterior rectangular
   - Un agujero interior (líneas) de forma cuadrada o circular (entidad ARC/LINE)
2. Activar kerf y comparar el contorno compensado visualmente en el visualizador del programa.
3. El contorno exterior debe ser **más grande** que el original.
4. El agujero interior debe ser **más chico** que el original.

## Contexto del programa

- `C:\Python\CostADCAM Claude` es el generador de G-code para plasma y oxicorte que procesa nestings de CypCut.
- `kerf.py` se aplica sobre entidades tipo `linea`, `arco` y `circulo` agrupadas en `block`.
- El punto de entrada público es `aplicar_kerf_a_entidades(entidades)`.

---

Reportar en `coordination/channel/Nova/` al completar.

— Nova
