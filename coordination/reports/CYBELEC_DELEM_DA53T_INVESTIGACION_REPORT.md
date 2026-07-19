# CYBELEC_DELEM_DA53T_INVESTIGACION_REPORT

**Agente:** Cybelec
**Tarea:** Investigación del manual DELEM DA-53T (pedido de Constantino)
**Fecha:** 2026-07-18
**Estado:** COMPLETO — investigación, sin implementación

---

## Fuente

- **Documento:** DELEM DA-53T Reference Manual, Operation of Version 1.5 (manual V0817, 8087-921A).
- **Descarga:** OK (3,2 MB, 132 páginas). No hubo restricciones.
- **Naturaleza:** es un **manual de OPERACIÓN**, no una referencia técnica de ingeniería. No publica fórmulas: el desarrollo (bend allowance) y la fuerza se describen como "automatically computed" sin ecuaciones.
- Copia local de trabajo en scratchpad (no versionada).

---

## 1. Modelo de cálculo

**No hay fórmulas para copiar.** El manual no publica DIN 6935, factor K, ni la fórmula de tonelaje. Nuestra base de cálculo (DIN 6935 con k = 0.65 + 0.5·log10(ri/s), penetración (V/2)·tan((180−α)/2), tonelaje al aire) **no se modifica** por este documento.

Lo que sí aporta es **con qué datos alimenta el cálculo**:

### Modelo de material de 3 propiedades
DELEM define cada material con:
- **Tensile strength** (Rm) — lo tenemos (SIGMA del Cybelec).
- **E-module** — no lo tenemos.
- **Strain hardening exponent (n)** — no lo tenemos.

Cita textual del efecto de `n`: mejora el cálculo del **radio interno**, y de ahí "a more accurate bending depth and bend allowance calculation. In its turn a more accurate bend allowance will result in more accurate back gauge positions."

O sea la cadena es: `n` → radio interno → profundidad (Y) **y** desarrollo → posición X del tope. Es exactamente la cadena que nosotros resolvemos hoy con `ri` estimado.

**Tabla de materiales precargados (pág. 4.12):**

| Material | Tensile strength (N/mm²) | E-module (N/mm²) | n |
|---|---|---|---|
| Steel | 470 | 210.000 | 0.23 |
| Aluminium | 250 | 210.000 | 0.26 |
| Zinc | 200 | 94.000 | 0.20 |
| Stainless steel | 750 | 210.000 | 0.32 |

⚠ **Errata detectada en el manual:** el E-module del aluminio figura como 210.000 N/mm², que es el del acero. El aluminio real ronda **70.000 N/mm²**. Verifiqué contra la página original del PDF (no es un error de extracción): el manual lo imprime así. **No usar ese valor.** También hay una inconsistencia menor: en la sección "Calculate n" dice que un valor típico de acero dulce es 0.21, mientras la tabla pone 0.23.

### Radio interno = piso por el radio del punzón
Regla explícita en la definición del punzón: el radio de la punta "will be used as inner radius of the bend to make **when this radius value is bigger than the inner radius as will result from the bending process**".

Es decir: `ri_efectivo = max(radio_punta_punzón, ri_resultante_del_proceso)`. Nuestra app hoy usa `ri = V·0.10` por defecto si no se carga — más grosero.

### Auto-calibración "Calculate n"
Procedimiento de taller: se hace un plegado de prueba en modo Manual, se **mide el largo de ala resultante** y se ingresa. De la diferencia entre la X programada y el largo medido, el control deriva el **bend allowance y el exponente n**. Depende de la precisión del espesor, de los datos de herramienta y de la medición.

---

## 2. Correcciones — el hallazgo más valioso

### Base de datos de correcciones de ángulo
Las correcciones dejan de vivir en el programa de la pieza y pasan a una **base de datos persistente** que sirve para futuros trabajos. El control busca correcciones de plegados "similares" al activo, comparando:

- Material
- Espesor
- Apertura de V de la matriz
- Radio de la matriz
- Radio del punzón
- Ángulo

**Regla de coincidencia (bien diseñada, conservadora):**
- Las **primeras 5** propiedades deben coincidir **exactamente** para siquiera comparar.
- Si el **ángulo coincide** → ofrece la corrección guardada.
- Si el ángulo está a **≤10°** de dos plegados guardados adyacentes → **interpola** entre ellos.
- Si las correcciones de esos dos adyacentes difieren en **más de 5°** → **no ofrece nada** (demasiada incertidumbre).

Complementos: **initial angle correction** (capa de offset que no se visualiza, se suma), **general angle corrections** (por programa, no van a la base), y opción de guardar también las correcciones hechas en modo Manual.

**Convención de signo — coincide con la nuestra:** programado 90°, medido 92° → corrección **−2**. (Nuestro `angCorr` usa la misma convención.)

**Comparación con lo nuestro:** nuestro `state.angCorr` se indexa **solo por ángulo** y vive en la pieza/sesión. La corrección aprendida en un trabajo no se reutiliza en el siguiente.

---

## 3. Secuenciación, colisiones, backgauge

### Secuenciación: el DA-53T NO la hace automática
Confirmado leyendo la sección de edición de programa: el orden de plegados se cambia **a mano** con "Mark Bend" + "Move Bend" / "Swap Bends". No hay búsqueda automática de orden ni detección de choque pieza↔punzón/matriz.

Las únicas colisiones que computa son:
1. **Pieza ↔ dedo del tope**, a partir de las dimensiones del dedo (sección 8.4).
2. **Seguridad de ejes** (posiciones seguras temporales de X y R para que no choquen durante el movimiento).

**Nuestro cerebro está por delante del DA-53T en esto:** búsqueda automática de orden, colisión contra el perfil real de punzón y matriz, simulación de fin de carrera, técnica W y de escalón. Nada de eso está en este control.

### Geometría del dedo del tope (sí es más rica que la nuestra)
El dedo se modela con **hasta 4 posiciones de apoyo (gauge positions)**, cada una con:
- **Finger height (FH)** — altura/espesor de la punta del dedo
- **Finger length (FL)** — largo del primer nivel de apoyo
- **Gauge height (H1)** — altura del primer nivel de apoyo

Más: **Gauge R offset** (eje R, altura del tope), **Z-distance** (distancia del borde del dedo a la esquina de la chapa), **Finger width**, y **Layon** (apoyar sobre el dedo o no).

Nosotros usamos una sola banda `[-1.5, mesa + FINGER_H]` con `FINGER_H=30`. El modelo de DELEM es escalonado multinivel.

### Backgauge retract
"The backgauge retract is started when the beam is pinching the sheet" — el tope **se retira** una vez que la trancha pisa la chapa. Es un mecanismo real que afecta la colisión: el dedo se escapa mientras el ala sube. Nuestro chequeo del dedo es estático.

---

## 4. Métodos de plegado que no tenemos

El DA-53T soporta 4 métodos; nosotros solo el primero:

| Método | Cómo calcula Y |
|---|---|
| **Air bend** (el nuestro) | Y para llegar al ángulo programado |
| **Bottoming** | Y = fondo de la matriz. Fuerza = fuerza al aire × *bottoming force factor* |
| **Hemming** (aplastado) | Y = superficie de la matriz + **2× espesor**, ajustable con *hem opening* |
| **Hemming & bottoming** | Igual pero tomando el tope de la matriz |

También: **V bottom** de la matriz configurable (punta viva / redondo con radio interior / plano con ancho de fondo) y **Support type** del punzón (head vs shoulder mounted, corrige el cálculo de Y).

### Cilindrado (bumping)
Coincide con lo nuestro en el concepto (radio dividido en N segmentos, N+1 plegados). Detalle que aporta: por defecto el **primer y último segmento son de medio tamaño** para mejor resultado, con opción de forzar segmentos iguales si la V no permite plegar segmentos tan chicos.

---

## 5. Herramientas por pliegue — valida el pedido de Constantino

El DA-53T permite **cambiar punzón y matriz por plegado individual**: al usar "Change Tools" el control pregunta si el cambio es para **todo el setup o solo para ese plegado**.

Esto confirma que la pendiente que Constantino ya había pedido (punzón/matriz por pliegue, para cuello de cisne en montantes con retorno) es **funcionalidad estándar de la industria**, y muestra la estructura: herramientas a nivel programa, con override por pliegue.

---

## 6. Formatos de archivo / interoperabilidad — sin ganancia

- Formatos **propietarios de Delem**. Se menciona el **DLC-file format** solo para restaurar productos/herramientas de controles viejos.
- Productos y herramientas se guardan como archivos en **USB o red**; backup/restore por pantalla.
- La programación offline se hace con el software propio de Delem, **Profile-T**.
- **No hay import/export DXF, CSV ni XML documentado.** No hay nada estándar que podamos consumir ni generar para interoperar.

---

## 7. Lo que NO aporta

- Fórmulas de cálculo (no las publica).
- Secuenciación automática y colisión con herramientas (no las tiene; nosotros sí).
- Formato de intercambio de archivos (propietario).
- Todo lo específico de máquina que no nos aplica: velocidades, punto de mute, descompresión, dwell time, paralelismo Y1/Y2, bombeo (crowning), diagnóstico de I/O, contadores de stock y producción, mantenimiento.
- Función **Connect** (encadenar dos programas para piezas 3D plegadas en dos direcciones): es una muleta de un control 2D; nuestro modelo de pieza ya es geométrico.

---

## Recomendación de prioridades (para que decida Constantino)

1. **Base de datos de correcciones por firma de plegado** (material+espesor+V+radios+ángulo, con interpolación ≤10° y corte por dispersión >5°). Es lo que más impacto tiene en precisión real de taller y es directamente portable a nuestro modelo.
2. **Radio interno = max(radio punzón, radio del proceso)** — mejora barata sobre el `ri = V·0.10` actual.
3. **Herramientas por pliegue** — ya estaba pedido; el DA-53T confirma el diseño.
4. **Dedo del tope multinivel + retract** — refina nuestra detección de choque con el tope.
5. **Métodos bottoming / hemming** — solo si Constantino los usa en la ADIRA.
6. Material con `n` y E-module + "Calculate n": atractivo, pero **requiere que Constantino valide** si quiere meter un modelo de radio basado en propiedades del material o prefiere seguir con `ri` cargado a mano.

**Nada de esto fue implementado.** Es investigación.

— Cybelec
