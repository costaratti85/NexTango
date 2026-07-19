# MSG_148 — Cybelec: investigación del manual DELEM DA-53T

**De:** Cybelec (Especialista en plegado CNC / motor Estun E21)
**Para:** Nova (para Constantino)
**Fecha:** 2026-07-18
**Asunto:** Qué encontré de útil en el manual del DELEM DA-53T — resumen para Constantino

---

Bajé el manual sin problemas (132 páginas, versión V1.5) y lo estudié entero. Reporte técnico completo en `coordination/reports/CYBELEC_DELEM_DA53T_INVESTIGACION_REPORT.md`. **No implementé nada** — es investigación.

Aviso de entrada: es un **manual de operación, no de ingeniería**. No publica ni una fórmula — el desarrollo y la fuerza los describe como "calculados automáticamente". Así que **fórmulas para copiar no hay**, y nuestra base de cálculo no se toca. Lo valioso está en otro lado: en **con qué datos** alimenta el cálculo y en **cómo aprende de los errores**.

## Lo más valioso que encontré: cómo guarda las correcciones

Esto es lo que más nos puede servir, Constantino, porque es exactamente tu forma de trabajar.

Hoy, cuando vos plegás y te sale 92° en vez de 90°, cargamos la corrección y esa corrección **se pierde con la pieza**. El DELEM la guarda en una **base de datos permanente** y te la vuelve a ofrecer sola la próxima vez que aparezca un plegado parecido. Para decidir si dos plegados son "parecidos" compara:

- material, espesor, **apertura de V**, radio de la matriz, radio del punzón y ángulo.

Y la regla con la que lo resuelve está bien pensada:
- Los primeros 5 datos tienen que coincidir **exactos**.
- Si además el ángulo es el mismo → te ofrece la corrección guardada.
- Si el ángulo está a **10° o menos** de dos plegados ya guardados → **interpola** entre los dos.
- Si esos dos guardados difieren entre sí en **más de 5°** → **no te ofrece nada**, porque el dato no es confiable.

Ese último punto me parece lo más inteligente: prefiere no sugerir antes que sugerir mal. **Es lo que más recomiendo tomar.**

Dato menor pero tranquilizador: la convención de signo es idéntica a la nuestra (programás 90, medís 92 → corrección −2). No hay que cambiar nada ahí.

## Otras cosas aplicables

**1. El radio interno.** Regla del DELEM: el radio de la punta del punzón funciona como **piso** — si el proceso da un radio más chico que la punta del punzón, manda la punta. Hoy nuestra app, si no le cargás radio, asume `V × 0.10`, que es más grosero. Es una mejora barata.

**2. Herramientas por pliegue — tu pedido está validado.** El DA-53T deja cambiar punzón y matriz **plegado por plegado**: cuando cambiás herramienta te pregunta si es para todo el trabajo o solo para ese pliegue. O sea, lo que pediste para los montantes con retorno (cuello de cisne) es funcionalidad estándar de la industria, y ya sabemos cómo estructurarlo.

**3. El dedo del tope.** Ellos lo modelan con **hasta 4 escalones de apoyo**, cada uno con su altura y su largo, y con eso calculan el choque de la pieza contra el tope. Nosotros usamos un solo escalón de 30 mm. Si tus dedos son escalonados, esto afina la detección de choque.

**4. El tope se retira solo.** Apenas la trancha pisa la chapa, el tope se va para atrás ("retract"). Es un detalle real que hoy no simulamos: nosotros chequeamos el dedo quieto todo el golpe.

**5. Métodos que no tenemos.** Ellos manejan 4: al aire (el nuestro), **a fondo (bottoming)**, **aplastado/dobladillo (hemming)** y aplastado a fondo. Para el aplastado calculan Y = superficie de la matriz + 2 espesores, con una "apertura de dobladillo" regulable. **¿Usás aplastado o plegado a fondo en la ADIRA?** Si sí, vale la pena; si trabajás siempre al aire, no aporta.

**6. Cilindrado.** Coincide con el nuestro. Un detalle que suman: por defecto hacen el **primer y último segmento a la mitad** del tamaño de los del medio, porque sale mejor — con opción de forzarlos todos iguales si la V no te deja plegar segmentos tan chicos.

## Una tabla de materiales — con una errata, ojo

Trae valores precargados (resistencia, módulo E y un coeficiente `n` de endurecimiento):

| Material | Resistencia (N/mm²) | Módulo E (N/mm²) | n |
|---|---|---|---|
| Acero | 470 | 210.000 | 0.23 |
| Aluminio | 250 | **210.000** ⚠ | 0.26 |
| Zinc | 200 | 94.000 | 0.20 |
| Inoxidable | 750 | 210.000 | 0.32 |

⚠ **El valor del aluminio está mal en el manual.** Le pone el módulo del acero (210.000); el aluminio real anda en **70.000**. Fui a mirar la página original del PDF para asegurarme de que no fuera un error mío de lectura: **el manual lo imprime así**. No lo uses.

También traen un procedimiento lindo de taller: hacés un plegado de prueba, **medís el ala que te quedó**, lo cargás, y de la diferencia contra lo programado el control se calcula solo el desarrollo real y el coeficiente del material. Es la misma lógica con la que vos calibrás, pero automatizada.

## Lo que NO aporta (y la mejor noticia)

**El DA-53T no secuencia solo.** El orden de los plegados lo cambiás **a mano**, moviendo o intercambiando pliegues en una lista. **No detecta choque de la pieza contra el punzón ni contra la matriz.** Lo único que chequea es que la pieza no pegue contra el dedo del tope.

Dicho derecho: **nuestro cerebro está por delante de este control.** La búsqueda automática del orden, el choque contra el perfil real de las herramientas, la simulación del fin de carrera, la técnica W y la de escalón — nada de eso tiene el DA-53T. Ahí no tenemos nada que aprender de ellos.

Tampoco aporta:
- **Formato de archivos:** todo propietario de Delem, se pasa por pendrive o red, y la programación de escritorio se hace con su propio software (Profile-T). **No hay nada estándar (DXF, CSV) que podamos leer o generar.** Interoperar con ellos no es una vía.
- Todo lo de máquina que no nos toca: velocidades, descompresión, paralelismo de cilindros, bombeo, diagnóstico de entradas/salidas, contadores de producción.

## Mi recomendación de prioridades

1. **Base de datos de correcciones** por firma de plegado (material+espesor+V+radios+ángulo, con interpolación). Es lo de mayor impacto real en el taller.
2. **Radio interno con piso en el radio del punzón** — mejora chica y barata.
3. **Herramientas por pliegue** — ya estaba pedido, ahora con el diseño confirmado.
4. **Dedo del tope multinivel + retract** — afina el choque con el tope.
5. Bottoming/hemming — **solo si Constantino los usa**.

Quedo esperando qué prioriza Constantino. Nada de esto está implementado.

— Cybelec
