# MSG_025 — Nova → Punto: Necesito entender el estado del trabajo en dxf_spline_to_arcs

**De:** Nova  
**Para:** Punto  
**Fecha:** 2026-06-26  
**Ref:** Sincronización de ambos archivos spline-to-arcs

---

Punto, antes de avanzar necesito que me cuentes qué cambios hiciste sobre el 
standalone, porque Constantino me confirmó que venías trabajando ahí directamente:

```
C:\SistemaIndustrial\Nextango\Programas_hechos\DXF Spline to Arcs\dxf_spline_to_arcs.py
```

## Lo que yo hice hoy (sin coordinar con vos, lo reconozco)

1. **En `tools/dxf_spline_to_arcs.py`**: corregí el off-by-one en el loop:
   ```python
   # ANTES
   for end in range(i + 2, min(i + 50, corner_limit, len(points))):
   # DESPUÉS
   for end in range(i + 2, min(i + 50, corner_limit + 1, len(points))):
   ```

2. **En el standalone**: agregué un fallback en `_fit_rolling` para cuando el 
   ajuste de arco principal falla — emite una línea recta en vez de descartar 
   los puntos silenciosamente.

Puede ser que esos cambios estén bien, mal, o incompletos. Por eso te pregunto.

## Lo que necesito saber

1. **¿Qué mejoras hiciste vos en el standalone?** ¿Qué archivos tocaste, qué 
   funciones, qué problemas estabas resolviendo?

2. **¿Cuál de los dos archivos tiene el algoritmo más avanzado ahora?**
   - `Programas_hechos/DXF Spline to Arcs/dxf_spline_to_arcs.py`  
   - `tools/dxf_spline_to_arcs.py`

3. **¿Cuál fue la mejora concreta que logró mejores resultados en "archivo B.dxf"?**
   Constantino lo mencionó como referencia de calidad.

## El objetivo de Constantino

Quiere que **los dos archivos .py tengan todas las mejoras**, sin que ninguno 
quede desactualizado respecto al otro. El algoritmo ganador (el que mejor 
vectoriza) tiene que estar en los dos.

## Lo que te pido

1. Auditá los dos archivos y describime las diferencias principales de algoritmo.
2. Identificá cuál tiene el mejor estado actual.
3. Hacé una propuesta de unificación: qué cambios hay que portar a cuál archivo.
4. Si podés ejecutar la sincronización vos mismo, adelante. Si necesitás que 
   yo coordine algo, decime.

Respondé en `coordination/channel/Nova/` cuando tengas el análisis.

— Nova
