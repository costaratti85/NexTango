# MSG_112 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino) + Dispatch
**Fecha:** 2026-07-13
**Asunto:** Punto 1 (formato capas) HECHO + diseño de división genérica y tresbolillo hexágonos

## 1) FORMATO DXF POR CAPAS — me adelanté (commit 4020f8d)

**Hallazgo:** mi generador asignaba el atributo `layer` a cada agujero (0–8, CONTORNO)
pero **NO declaraba esas capas en la tabla LAYER del DXF** — solo existían "0" y "Defpoints".
Es muy probable que ESE fuera el problema para que CypCut lea las capas de flycut.

**Corregido:** ahora se declaran las 9 capas (0–8) + CONTORNO en la tabla LAYER, cada una
con color distinto. Test que lo garantiza. Demo actualizado en
`\\190.190.190.20\planos\calibracion_laser\demo_latin_square_1000x2000.dxf`.

**PENDIENTE de validar con el DXF de referencia de Constantino** (cuando lo tengas, pasámelo):
- ¿Los **nombres** de capa correctos son "0".."8", o CypCut espera otro formato (ej. "Capa 1",
  o un prefijo)?
- **Duda clave:** ¿CypCut acepta la **capa "0"** como capa de flycut? En CAD la "0" es la capa
  por defecto y algunos sistemas la tratan especial. Si no la toma, remapeo a **1..9**
  (`capa = (col+fila)%9 + 1`) — es un cambio de una línea.
- ¿Colores/otros atributos que CypCut necesite por capa?
En cuanto tenga el DXF de referencia comparo campo por campo y ajusto antes del corte.

## 2) DIVISIÓN POR ÁREAS GENÉRICA (próxima tanda)

Buena noticia: **la lógica ya está casi desacoplada**. Hoy tengo piezas genéricas
(`calcular_zonas`, `zona_de_agujero`, `zona_a_capa`, `asegurar_capas_flycut`), solo que se
llaman inline dentro del generador de cuadriculado square.

**Refactor propuesto:** extraer un helper reutilizable, p.ej.
`capa_de_punto(cx, cy, sheet_w, sheet_h) -> int` (combina zonas + cuadrado latino) +
`asegurar_capas_flycut(doc)` (ya existe). Cualquier generador de patrón itera sus figuras y
hace `capa = capa_de_punto(cx, cy, W, H)`. La división por áreas queda independiente del patrón
(sirve para cuadriculado, tresbolillo hex, y lo que venga). Lo pondría en un módulo propio
`flycut_areas.py`.

## 3) TRESBOLILLO CON HEXÁGONOS (próxima tanda)

**Contexto técnico:** hoy el tresbolillo se genera con el **engine legacy** (dibuja círculos).
El cuadriculado square, en cambio, usa un **generador directo** (el que ya tiene latin square).

**Propuesta:** hacer un generador directo `_run_tresbolillo_hex` (espejo del de square):
1. Calcula las posiciones tresbolillo (grilla hexagonal: filas con offset de medio paso).
2. Dibuja un **hexágono** (LWPOLYLINE de 6 vértices) en cada posición.
3. Asigna capa por área con el helper genérico del punto 2 → el flycut de 3 pasadas
   (horizontales / inclinadas der / inclinadas izq) nunca corta áreas contiguas seguidas.
- Activación: `pattern_type=="tresbolillo" and hole_shape=="hexagon"` → nuevo generador
  (el circular sigue por el engine legacy, no lo toco).

**Dudas para Constantino (hexágonos):**
- **Orientación:** que menciones pasadas "horizontales + inclinadas der/izq" sugiere hexágono
  **flat-top** (dos lados horizontales arriba/abajo). ¿Confirmás flat-top, o pointy-top?
- **Tamaño:** el diámetro del hexágono, ¿se mide **entre caras planas** (across-flats) o
  **entre vértices** (across-corners)? Definí cuál usás en el taller.
- ¿El **espaciado** (distancia entre centros) sigue la misma lógica que el tresbolillo circular?

## Prioridad
- Punto 1: **hecho**, listo para el corte (falta solo tu DXF de referencia para validar el 100%).
- Puntos 2 y 3: próxima tanda, no urgente. Arranco cuando me actives y con tus respuestas a las dudas.

— Punto
