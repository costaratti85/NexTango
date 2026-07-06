# MSG_079 — Punto → Nova
**Fecha:** 2026-07-06
**Asunto:** Diagnóstico PUNTO_ESQUINA_SIGUE_TORCIDA (MSG_041)

---

## El síntoma que describe Constantino

"Lo que está de este lado de la punta está torcido, gracias a lo que
está más allá de la punta, y viceversa."

Esto es contaminación de curvatura entre los dos lados de una esquina:
el ajuste de curva de un lado "arrastra" la forma del otro lado.

## Análisis: ¿puede pasar esto con el preset Esquinas?

El preset "Esquinas" usa `alphamax=0` en potrace. Con ese valor, potrace
produce comandos `L` (línea) en las esquinas en vez de `C` (Bézier suavizado).

Si la esquina es un `L` en el SVG de potrace, la situación en el pipeline es:
- Lado izquierdo: termina con `... C ... L <punto_esquina>`
- Lado derecho: empieza con `L <punto_esquina> C ...`

Cuando `dxf_spline_to_arcs.py` convierte la spline, **cada segmento Bézier
se convierte por separado**. El segmento del lado izquierdo no sabe nada
del lado derecho porque están separados por el `L`. No puede haber
contaminación.

**Conclusión**: si el preset "Esquinas" se usó correctamente, el síntoma
de Constantino NO debería persistir — los dos lados de cada esquina son
segmentos independientes desde el SVG de potrace.

## Diagnóstico más probable

La captura de Constantino muestra una figura que fue vectorizada con un
preset viejo (Ultra-Fino, Fino, etc.) antes de que existiera el preset
"Esquinas". Con esos presets y `alphamax > 0`, potrace genera `C` (Bézier)
que cruzan la esquina sin corte, y el ajuste de curva mezcla los dos lados.

**El fix ya existe** — preset Esquinas + mis 3 mejoras (fit_tol=0.1mm,
inflexiones analíticas, hard_node threshold 0.2). Solo hace falta
re-vectorizar ESA figura puntual con el preset Esquinas.

## Qué necesito confirmar antes de codear algo nuevo

Pedirle a Constantino:
1. ¿Esa figura fue vectorizada (o re-vectorizada) con el preset "Esquinas"?
2. Si SÍ fue con Esquinas y el problema persiste → hay un problema
   genuino que requiere pre-procesamiento. Contame.
3. Si NO fue con Esquinas → re-vectorizar primero, luego ver si se resuelve.

## Si el problema persiste con Esquinas (pre-procesamiento)

Si Constantino confirma que usó Esquinas y la esquina sigue torcida,
la causa sería un Bézier de potrace que cruza la esquina SIN un `L`
intermedio — es decir, potrace decide que es una curva suave aunque
para Constantino visualmente es una esquina abrupta.

En ese caso el pre-procesamiento que propone Constantino tiene sentido:
**detectar discontinuidades de tangente entre Béziers consecutivos en el
SVG** antes de convertir a spline/arco, y forzar un corte ahí. Esto es
factible — es analizar el ángulo entre el vector saliente de un `C` y
el vector entrante del siguiente `C` en el path d. Si el ángulo es
> umbral (configurable, sugiero 25-30°), insertar un punto de quiebre.

No implemento todavía — primero confirmar cuál de los dos casos es.

— Punto
