# PUNTO_TASK_038 — Grilla Subte no centrada en el rectángulo

**Asignado a:** Punto  
**Prioridad:** Alta — bug visual en producción  
**Fecha:** 2026-06-20  
**Reportado por:** Constantino

---

## Bug

En el presupuesto PRES_0026, el panel Subte tiene la grilla de agujeros desplazada respecto al centro del rectángulo. Los agujeros no quedan centrados dentro del panel.

## Datos del panel afectado

```
Patrón:           Subte
Dimensiones:      555 × 444 mm
Margen:           20 mm
Step X/Y:         84 mm
cut_partial:      false
Material:         Chapa galvanizada 0.7mm
```

Área útil (descontando márgenes):
- Ancho: 555 - 2×20 = **515 mm**
- Alto:  444 - 2×20 = **404 mm**

Cantidad de repeticiones que entran:
- Columnas: floor(515 / 84) = **6** → ocupan 504 mm → sobran 11 mm
- Filas:    floor(404 / 84) = **4** → ocupan 336 mm → sobran 68 mm

Para centrado correcto, el offset de inicio de la grilla debería ser:
- Offset X adicional: (515 - 6×84) / 2 = **5.5 mm**
- Offset Y adicional: (404 - 4×84) / 2 = **34 mm**

Si el motor arranca la grilla en `(margin, margin)` sin sumar estos offsets, la grilla queda pegada al borde superior-izquierdo.

## DXF para inspección

```
C:\SistemaIndustrial\Nextango\outputs\panel_sales_demo\VENTA-CLIENTE-DEMO-PANEL-PEDIDO_legacy_panel.dxf
```

Contiene dos paneles: Subte (555×444) y Philo (335×550). Inspeccionar el panel Subte.

Patrón fuente Subte:
```
//190.190.190.9/Ventas/Users/Pantografia/Hierros Ratti/LLLLAAAAASSSSEEEERRRRR PAPA/Paneles Decorativos/Patrones/subte Offx84 Offy84.dxf
```

## Hipótesis principal

En el código que genera la grilla de patrones DXF (`dxf_pattern_grid` mode), el punto de inicio de la primera repetición probablemente es:

```python
x_start = margin_mm          # debería ser margin_mm + offset_x_centrado
y_start = margin_mm          # debería ser margin_mm + offset_y_centrado
```

El fix esperado:
```python
n_cols = floor(ancho_util / step_x)
n_filas = floor(alto_util / step_y)
offset_x = (ancho_util - n_cols * step_x) / 2
offset_y = (alto_util - n_filas * step_y) / 2
x_start = margin_mm + offset_x
y_start = margin_mm + offset_y
```

## Entregable

1. Confirmar la causa raíz inspeccionando el DXF y el código del motor de grilla
2. Corregir el centrado
3. Test que verifique que con los datos del panel Subte de PRES_0026 la grilla queda centrada
4. Verificar que Philo (cut_partial=true) no se ve afectado
5. 56 tests deben seguir pasando
6. Reporte en `coordination/channel/Nova/`

---

Nova
