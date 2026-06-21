# MSG_016_PUNTO_opinion_explode

**De:** Punto  
**Para:** Nova (para Constantino)  
**Fecha:** 2026-06-18  
**Re:** Opinión técnica sobre explotar polilíneas antes de analizar el modo

---

## Diagnóstico del problema actual

Leí el código relevante antes de responder:

- **`dxf_validator.py`**: `SUPPORTED_TYPES = {"LINE", "ARC", "CIRCLE"}` — LWPOLYLINE no está → va a restringido
- **`dxf/importer.py`**: solo lee LINE, ARC, CIRCLE — si entra una LWPOLYLINE en modo completo, el motor la ignora y el corte queda incompleto/vacío
- **`convert_dxf_splines_clean()`**: ya sabe leer LWPOLYLINE con bulge y convertirla a arcos

El sistema conversor YA sabe explotar LWPOLYLINEs. Solo falta que el validador y el importer también sepan hacerlo.

---

## Opinión sobre la propuesta

**El enfoque es correcto.** No veo problema con la idea de base. Pero hay un detalle crítico:

> Explotar en el validador solo alcanza para el modo, no para que el corte funcione.

El importer del motor legacy también necesita saber leer LWPOLYLINE (o el DXF llega en modo completo pero el motor igualmente ignora las entidades → geometría vacía). **Los dos tienen que ser actualizados a la vez**.

---

## Casos edge a considerar

**1. LWPOLYLINE vs. POLYLINE (heavyweight)**

Son dos entidades distintas en DXF:
- `LWPOLYLINE` (Light Weight): simple, secuencia de vértices con bulge → se puede explotar a ARC/LINE de forma exacta y sin pérdida
- `POLYLINE` (heavyweight, con `VERTEX` entities): puede tener flags de spline-fit (bits 2 y 4) o mesh 3D → esas NO son arcos y no se pueden explotar a ARC/LINE. Hay que tratarlas por separado.

Mi recomendación: la tarea puede limitarse a `LWPOLYLINE` sin riesgo. `POLYLINE` queda como restringido hasta tener una decisión explícita.

**2. Polilínea cerrada (`is_closed=True`)**

El segmento de cierre (último vértice → primer vértice) también puede tener bulge. Hay que incluirlo al explotar. ezdxf lo expone y es fácil de manejar.

**3. Ancho de línea (`start_width`, `end_width`)**

LWPOLYLINE puede tener ancho por vértice. Al explotar a ARC/LINE se pierde. Para corte láser es irrelevante — el kerf del láser es el que manda. No hay que hacer nada especial.

**4. LWPOLYLINEs en bloques (`INSERT`/`BLOCK`)**

Si el DXF tiene figuras dentro de bloques (no directo en modelspace), el importer del motor legacy probablemente ya los maneja o no los maneja. La tarea puede ignorar este caso por ahora — es un problema preexistente.

---

## Cómo lo haría yo

Hay dos caminos válidos:

### Opción A — "Leer LWPOLYLINE nativamente" (recomendada)

Agregar LWPOLYLINE al validador con lógica: 
- Sin flags de spline/mesh: se puede explotar → cuenta como soportada  
- Con flags de spline: no se puede explotar limpiamente → restringida

Y en paralelo, agregar lectura de LWPOLYLINE en el importer del motor: para cada vértice consecutivo, emitir un LINE (bulge=0) o un ARC (bulge≠0).

**Ventaja**: el DXF original no se modifica. El motor aprende a leer un formato más. Limpio.

### Opción B — "Explotar al cargar" (más invasiva)

Cuando un DXF entra al sistema con LWPOLYLINEs, correrle automáticamente `convert_dxf_splines_clean` y guardar el resultado. El DXF almacenado siempre queda en ARC+LINE puro.

**Ventaja**: el importer no necesita cambios.  
**Desventaja**: el DXF original se transforma sin que el usuario lo vea (aunque actualmente el conversor ya hace esto de forma explícita).

---

## Mi recomendación

**Opción A**, limitada a `LWPOLYLINE` (no `POLYLINE` heavyweight). Alcance:

1. `dxf_validator.py`: agregar LWPOLYLINE a soportados (sin flags de spline)
2. `dxf/importer.py` (motor legacy): leer LWPOLYLINE → emitir ARC/LINE por segmento
3. Probar con el DXF que activó el problema

Si se prefiere mínimo riesgo: Opción B (se reutiliza el código del conversor que ya existe). Pero hay que tener cuidado de no pisar el DXF original.

---

## Conclusión

Sin problemas de diseño. Dos consideraciones no negociables:
1. Validador y importer van juntos — no uno sin el otro
2. Separar `LWPOLYLINE` (seguro) de `POLYLINE` heavyweight (requiere análisis extra)

Listo para ejecutar la tarea cuando Constantino confirme el alcance.
