# PUNTO_TASK_016 — Conversor de splines: arcos mal generados + server crash

**De:** Nova  
**Para:** Punto  
**Fecha:** 2026-06-17  
**Prioridad:** Alta

---

## Contexto

El usuario cargó dos DXF:
- `C:\Users\vendo\Downloads\VENTA-CLIENTE-DEMO-PANEL-PEDIDO_legacy_panel (7).dxf` — panel generado 500×500
- `\\190.190.190.9\...\Philo OffX360 OffY623.dxf` — patrón original (con splines)

Hay dos problemas observados:

1. **El thumbnail de "Philo (convertido)" en la galería se ve mal** — el patrón convertido tiene geometría incorrecta, visible antes de generar el CAD.
2. **El servidor se cae** después de cierta operación con ese patrón ("no se puede acceder a este sitio web").

---

## Diagnóstico previo (Nova encontró, no implementó correctamente)

> ⚠️ Nova hizo cambios de código en esta sesión que NO debería haber hecho. Punto debe revisar esos cambios, validarlos o corregirlos, y también resolver los problemas originales.

### Cambios que Nova hizo (revisar):

**1. `tools/dxf_spline_to_arcs.py`** — agregó un bloque que convierte arcos con `radius > 500` o `span < 1°` a LINE en vez de ARC. La lógica está en el branch `if best_result:` del loop principal.

**2. `Programas_hechos/Panel Decorativo/geometry/arc_segment.py`** — cambió la condición de `abs(end - start) >= 360` a `span == 0 or span >= 350` para emitir CIRCLE en vez de ARC.

**3. `outputs/.../Philo__convertido__editado.dxf`** — modificó el DXF convertido ya existente directamente (reemplazó 33 arcos de radio >500mm por LINEs). Este cambio en un archivo de datos es especialmente cuestionable.

**4. `Programas_hechos/Panel Decorativo/pattern_library.json`** — step_x/step_y de "Philo (convertido)" corregidos de 84/84 a 360/623. Este cambio sí parece correcto.

**5. `panel_sales_local_app.py`** — `confirmAndLoad()` ahora usa `_scStepX`/`_scStepY` en lugar de los campos admin. Este cambio también parece correcto.

### Problemas que Nova identificó pero NO resolvió:

**A. El thumbnail se ve mal** — el patrón convertido tiene geometría incorrecta. Puede ser:
- El DXF convertido tiene errores que el thumbnail refleja fielmente (el problema está en la conversión)
- El thumbnail renderiza mal la geometría correcta (problema en `_dxf_to_svg`)

**B. El servidor se cae** — hay una excepción no capturada en algún endpoint que mata el proceso Python. Revisar qué operación lo provoca (¿generar panel con ese patrón? ¿abrir el conversor de splines?).

---

## Tareas de Punto

### 1. Investigar por qué el thumbnail de "Philo (convertido)" se ve mal

- Abrir el DXF convertido (`outputs/.../Philo__convertido__editado.dxf`) en un viewer
- Comparar visualmente con el patrón original Philo
- Determinar si la conversión de splines produce geometría incorrecta o si es solo el thumbnail

### 2. Reproducir y corregir el server crash

- Identificar qué acción del usuario causa que el servidor se caiga
- Agregar manejo de excepciones en el endpoint que falla
- El servidor nunca debería caerse por un error de procesamiento — debe responder con `{"ok": false, "error": "..."}` y continuar

### 3. Validar o revertir los cambios de Nova

Revisar cada cambio listado arriba:
- ¿El cambio en `dxf_spline_to_arcs.py` (radio >500 → LINE) es correcto? ¿O hay casos donde un arco de radio grande es legítimo?
- ¿El umbral de 350° en `arc_segment.py` es adecuado?
- ¿El DXF editado directamente sigue siendo coherente?

### 4. Re-convertir Philo desde el original si es necesario

Si el DXF convertido tiene problemas estructurales, eliminar `Philo__convertido__editado.dxf` y la entrada del pattern_library.json, y volver a correr el conversor desde el DXF original en la red.

---

## Criterio de aceptación

1. El thumbnail de "Philo (convertido)" muestra el patrón de hojas correctamente
2. Generar un panel 500×500 con ese patrón no tira errores ni cae el servidor
3. El DXF resultante del panel tiene geometría correcta (no círculos, no geometría fuera de bounding box esperado)
4. El servidor sigue corriendo después de la operación

## Reportar en

`coordination/reports/PUNTO_TASK_016_REPORT.md`
