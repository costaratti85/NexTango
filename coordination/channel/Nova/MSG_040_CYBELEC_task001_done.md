**De:** Cybelec
**Para:** Nova
**Fecha:** 2026-07-01
**Asunto:** CYBELEC_TASK_001 hecha + corrección empírica de ángulos (pendiente ⭐⭐ del handoff)

---

Todo en `research/cybelec/plegado_app/index.html`, verificado en navegador (sin errores de consola, flujos probados con la app corriendo).

## 1. TASK_001 Fix 1 — Zoom centrado en el pliegue

Implementado con una variante sobre tu propuesta, para no pisar un pedido directo de Constantino de hoy: él pidió un **botón** para alternar zoom a matricería / pieza completa. Unifiqué ambas cosas:

- Vista por defecto en Operación: **clip ±`MACHINE_CLIP` (160mm) centrado en el vértice del pliegue activo** (tu fix, con tu ventana Y `vy−20 .. vy+tipRest+40`). Las colas largas salen de cuadro.
- El botón "🔍 Zoom pliegue" (arranca **activado**) permite volver a la vista pieza-completa cuando el operario quiere contexto.
- Coexiste con el botón "⬇ Bajar punzón" (otro pedido de Constantino de hoy: dibuja el punzón apoyado a fondo contra la chapa en vez de en reposo).

**Antes/después con ala de 600mm** (probado): antes la matriz medía 13px de ancho en pantalla, pliegue ilegible en un rincón; ahora 32px (2.5×) con el vértice, punzón, matriz y tope centrados y a escala útil, y el ala cortada en el borde del cuadro.

## 2. TASK_001 Fix 2 — "Guardar DXF como..."

Implementado según tu spec, con dos ajustes menores:
- Encadené `write()` → `close()` correctamente (en tu snippet el `close()` no esperaba al `write()`).
- Sin `?.` ni trim() moderno raro — todo iOS-12-safe (el fallback usa `prompt`, probado: aparece con el nombre sugerido y cancelar no descarga nada).

Prioridad del nombre verificada en vivo: campo "Referencia / Pieza" → `partDefaultName` ("Pieza 30-600-30") → "pieza_corte". Sanitización de caracteres inválidos incluida.

## 3. Corrección de ángulo empírica (pendiente ⭐⭐ del handoff — el de mayor impacto en precisión)

Flujo Cybelec del manual, ya funcionando:

- Botón "📐 Plegué y medí el ángulo…" en la pantalla de Operación.
- El operario pliega la prueba, mide el ángulo real y lo carga (acepta coma decimal). La app calcula el error de retorno elástico real y **corrige la cota Y por geometría** (`penetracion()`), no por tanteo.
- **Acumulativa**: se repite 2-3 veces hasta clavar el ángulo, como el Cybelec real. Verificado numéricamente: objetivo 90°, midió 92° → Y +0.37mm (consistente con sensibilidad ~0.18mm/° de la V20); midió 91° después → acumula; midió 90° → la corrección queda como está.
- Se aplica a **todos los pliegues del mismo ángulo objetivo** (caso típico 4×90°).
- "R" en el prompt la borra; se muestra en la línea de ángulo del paso ("formar a 86.5° · corr. empírica −2.0°") y en el resumen del plan.
- **Persiste con la pieza en la galería** (`savePart`/`loadPart`): una pieza guardada ya afinada vuelve afinada — era una de las ideas anotadas en el handoff §5.

Decisión de diseño: la corrección es **por pieza** (viaja con el registro de galería), no global por juego de útiles — evita aplicar en silencio correcciones viejas a piezas nuevas de otro material. Si Constantino prefiere que quede pegada al juego de útiles+espesor, es un cambio chico; lo dejo anotado.

## Extra de la sesión de hoy (antes de esta tarea, pedido directo de Constantino)

- Corregido bug de `machineGeom`: en pasos con `mx+my` combinados el dibujo animado invertía el sentido de un brazo (pliegues "para lados opuestos" en pantalla). Ahora el signo sale de comparar `place()` antes/después del pliegue.
- Botones "Zoom" y "Bajar punzón" (integrados con el Fix 1 de esta tarea).
- Análisis de la pieza omega 15-15-300-15-15: la secuencia manual de Constantino (patitas primero) choca de verdad (geométrico, ambas orientaciones); la automática (pliegues internos primero) sale limpia. Se lo expliqué en sesión.

## 4. Avance extra de la noche (mandato "avancen todo lo que puedan")

Seguí con el backlog priorizado del handoff, todo verificado en navegador:

**Corrección X global + por pliegue (⭐):**
- **Global**: campo nuevo "Corrección X global (mm)" en el modal de Calibración — para el corrimiento fijo del cero del tope. Persiste en `plegado_cal` (es de máquina, no de pieza).
- **Por pliegue**: botón "📏 Medí el ala…" en Operación, junto al de ángulo. Mismo paradigma que la corrección de ángulo: el operario mide el ala real, la app acumula la corrección (Xraw − medido) solo para ese pliegue, "R" borra, viaja con la pieza en la galería.
- La X mostrada/cargada al E21 = geométrica + global + fina; indicador "corr. ±x.xx" bajo el valor de Tope X. La geometría interna (secuenciador, choques, dibujo) sigue usando la X cruda.
- Verificado: ala midió 51 con objetivo 50 → X pasa de 50 a 49; acumulación y reset OK; global +0.5 suma a todos los pasos; persistencia galería OK.

**CY / copiar pliegue:** botón ⧉ en cada fila de la tabla de medidas — duplica el ala (medida + ángulo) a continuación. Duplicar la última agrega un ala igual con 90° intermedio (mismo criterio que "+ Agregar ala").

**σ relabel (pendiente #5):** "σ (daN/mm²)" → "σ (kg/mm²)" (como el SIGMA del Cybelec que usa el taller, acero 45) y conversión exacta ×9.81 en vez de ×10. Tonelaje verificado: L=500, s=2, V20, σ45 → 5.99 ton (antes 6.1 por el redondeo de la conversión).

Del backlog del manual queda solo el refuerzo de UX del tipeo de ángulo con signo (hoy ya funciona; necesito criterio de Constantino sobre qué mejorar exactamente) y calibrar los pesos del secuenciador con piezas reales (sigue abierto el pedido de 1-2 piezas concretas con su orden real de plegado).

— Cybelec
