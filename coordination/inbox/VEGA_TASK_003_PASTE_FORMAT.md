# VEGA_TASK_003 — Formato del bloque copy-paste: correcciones de columnas y texto

**Para:** Vega  
**De:** Nova  
**Fecha:** 2026-06-18  
**Prioridad:** Alta

---

## Problema

El bloque "Para el Presupuesto" generado por VEGA_TASK_002 tiene el formato incorrecto. Constantino mostró el before/after exacto.

---

## Formato ACTUAL (incorrecto)

```
1	Panel "Philo (convertido) 600.0x600.0" / 600.0 x 600.0 / en N°18			57123.03
2	Panel "Subte 650.0x800.0" / 650.0 x 800.0 / en N°18			65705.53
```

## Formato DESEADO

```
1	Panel Philo	600 x 600	en N°18	57,123.03
2	Panel Subte	605 x 800	en N°18	65,705.53
```

---

## Cambios requeridos

### 1. Nombre del patrón
- Sin comillas
- Sin el sufijo `(convertido)` ni ningún sufijo agregado por el motor
- Sin dimensiones en el nombre — solo el nombre limpio
- Formato: `Panel {nombre_limpio}`

### 2. Columnas separadas (no todo en una)
El bloque tab-separado ahora ocupa 4 columnas distintas al pegar en B25:

| Tab | Columna Excel | Contenido |
|---|---|---|
| 0 | B | cantidad (entero) |
| 1 | C | `Panel {nombre}` |
| 2 | D | `{ancho} x {alto}` |
| 3 | E | `en {material}` |
| 4 | F | precio formateado |

Antes se usaban 3 tabs vacíos para saltar D y E. Ahora D y E tienen contenido.

### 3. Dimensiones sin decimales
- `600.0 x 600.0` → `600 x 600`
- Usar enteros: `int(ancho) x int(alto)`

### 4. Precio con separador de miles
- `57123.03` → `57,123.03`
- Formato: `f"{precio:,.2f}"`

---

## Bloque OT — mismo ajuste

El bloque "Para la OT" aplica los mismos cambios de nombre y dimensiones:

```
1	Panel Philo	600 x 600	en N°18 / [Philo.dxf]
2	Panel Subte	605 x 800	en N°18 / [Subte.dxf]
```

---

## Archivo a modificar

`apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`  
Sección que genera los bloques copy-paste del resultado.

## Reporte

Dejar reporte en `coordination/reports/VEGA_TASK_003_REPORT.md` y mensaje en `coordination/channel/Nova/`.
