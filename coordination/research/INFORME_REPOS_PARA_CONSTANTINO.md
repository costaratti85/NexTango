# Informe: qué encontramos en los 3 repositorios del proyecto

**Para:** Constantino · **De:** Nova · **Fecha:** 19 de julio de 2026

---

## Resumen en 10 líneas

Revisamos los 3 repositorios que guardan la historia del proyecto. Los dos viejos resultaron ser sobre todo **documentos de arquitectura**: mucho plan de cómo organizar el sistema, poco criterio de taller. **No tienen ninguna fórmula de precio ni de plegado** — el modelo de precio que estamos buscando no está ahí, y conviene que lo sepas para no esperar un rescate que no va a llegar.

El hallazgo importante fue otro, y estaba en el repo **actual**: el documento **Brújula**. Ahí está tu voz original, de antes de que existiera el equipo de agentes, y contiene **reglas concretas que el equipo estaba a punto de volver a inventar**: los 300/500 mm del archivo de corte, el 65% de la barra, los estados de una pieza. Estaban escritas desde el principio y nadie las estaba mirando.

Formalicé 5 reglas nuevas, corregí una decisión que estaba mal redactada y definí cómo tiene que funcionar la página de precios. Todo eso ya está bajando al equipo.

---

## 1. Los 3 repositorios y su evolución

| | Repositorio | Cuándo empezó | Qué era |
|---|---|---|---|
| **1º** | `Sistema-Industrial` | **13 de mayo** (87 cambios) | La etapa de **"programamos todo desde cero"**: ERP propio, CAD propio, nesting propio, CAM propio. |
| **2º** | `Sistema_Industrial_Nextango` | **5 de junio** (1 solo cambio) | Una **foto del cambio de rumbo**: apoyarse en ERPNext y Tango en vez de reinventarlos. Se define a sí mismo como *"un derivado del original, reemplazando el plan de ERP desde cero por una arquitectura centrada en ERPNext"*. |
| **3º** | **`NexTango`** | julio | **El actual.** Arrancado ya pensando en Tango + ERPNext + CypCut. Es el que manda. |

**Un detalle que vale la pena:** las fechas que muestra GitHub **engañaban**. El repositorio original figura como "creado después" del segundo. Orbit no se quedó con eso: los ordenó por la fecha del **primer trabajo real**, no por la etiqueta. Por eso la historia quedó bien contada.

**La evolución, en una frase:** de *"hagamos todo nosotros"* → *"apoyémonos en lo que ya funciona y construyamos el puente"* → *"empecemos limpio con esa idea desde el día uno"*.

---

## 2. Brújula: lo más valioso de todo

`docs/00_BRUJULA_DOCUMENT_FUNDACIONAL.md`, en el repo actual. Se presenta así:

> *"Este documento es el norte completo del proyecto a largo plazo. **Ningún agente puede contradecirlo.**"*

Es **la conversación original, anterior al equipo de agentes** — o sea, vos explicando el negocio antes de que hubiera nada construido. **De ahí sale todo el canon del proyecto**: las decisiones que fuimos tomando después son, casi todas, consecuencias de lo que ya estaba escrito ahí.

### Lo que aporta

**Las 13 reglas inamovibles.** Las cuatro que el equipo más olvida:
- El sistema **sugiere**, el **humano decide**, el sistema **audita**. Nada se impone sin poder forzarlo a mano.
- Toda acción importante es **trazable**: quién, cuándo, qué, desde qué rol.
- **No duplicar lógica** entre módulos.
- **La tecnología se adapta a la operación**, no al revés.

**Los 11 flujos completos** de punta a punta: comercial, panel decorativo, piezas paramétricas, biblioteca de cliente, corte lineal, lote de corte por espesor, guillotina, plegado, estados por pieza, producción por taller y OCR de facturas de proveedores.

**Y el norte:** *"El objetivo no es un programa. Es una plataforma que convierte la operación real en un flujo digital coherente."*

---

## 3. 🔴 Lo más importante: definiciones que ya estaban resueltas y el equipo re-derivaba

Esta es la parte del informe que más te conviene leer.

**Cuatro definiciones concretas ya estaban escritas en Brújula, y el equipo las estaba por inventar de nuevo:**

**a) El archivo de corte ya tenía sus medidas.** *"300 mm entre piezas, 500 mm entre filas de espesor, etiquetas con espesor y cantidad."* Nido iba a tener que decidir esos números desde cero.

**b) El 65% de la barra ya era regla.** *"Si la última barra supera ~65% del largo estándar, sugerir cobrar barra entera."* Es una regla **comercial**, concreta, y hoy no está en ninguna parte del sistema.

**c) La matriz de qué máquina usa cada pieza ya estaba.** *"Rectángulo sin perforaciones → guillotina; espesor alto → oxicorte; general → láser/plasma."* Con el detalle importante de que la pieza de guillotina **sale del lote de láser**.

**d) Y la más grande: cómo se organiza la producción.** Pusiste a Lechu (MES) y a Nido en pausa esperando *"que se cierre la rebanada, porque ahí se define cómo se genera un pedido"*. **Buena parte de esa definición ya estaba en Brújula desde el principio:**

- **"Pedido ≠ Lote de corte"** — el pedido es del cliente; el lote es de producción y **mezcla piezas de varios pedidos**. Son dos cosas distintas, no una adentro de la otra.
- **El estado va en la pieza, no en el pedido** — con los 14 estados listados uno por uno, incluidos los parciales (cortada parcial, plegada parcial, entregada parcial).

**La lección operativa:** el documento estaba, pero no era lectura obligatoria. Se perdió trabajo por eso. Ya lo corregí (punto 6).

---

## 4. Lo que documenté yo en los repos viejos

En aquellos repos yo era también PM/arquitectura — el mismo rol de hoy. Lo rescatable es una cosa:

**La "matriz de fuentes de verdad"**: una tabla que dice **quién es dueño de cada concepto**. Que el cliente, la cotización y el pedido viven en ERPNext; que **la factura, el asiento contable y el comportamiento fiscal son de Tango** y no se tocan sin tu aprobación; que el archivo CAD es de la app.

La rescaté, pero **le saqué las filas de nesting y CAM** — decían que eran nuestros, y eso ya está contradicho (CypCut hace el nesting).

Lo más útil no es la tabla sino **la regla que la acompañaba**: *si algún documento o instrucción contradice la matriz, el agente **para** y explica el conflicto, en vez de improvisar.* Le agregué una cláusula que no tenía: **vale también si la contradicción viene de mí**. Si le pido a un agente algo que rompe la matriz, tiene que frenarme.

Lo digo porque el error más caro que tuvimos no fue un bug: fue **avanzar sobre información desactualizada sin que nadie parara a chequear** (aquella tarea "pendiente" que en realidad era obsoleta y habría borrado trabajo bueno).

---

## 5. Qué decidí

Me delegaste la autoridad, así que decidí. Esto es lo que quedó.

### Reglas del canon, ahora formalizadas

| | Qué fija |
|---|---|
| **DECISION_007** | Corte lineal: última barra > ~65% → **sugerir cobrar barra entera**. Es sugerencia: se puede forzar a mano, y queda registrado. |
| **DECISION_008** | Archivo de lote: **300 / 500 mm** y etiquetas. Con una aclaración: **no se "optimiza" ese espaciado para ahorrar chapa** — eso sería hacer nesting, y el nesting es de CypCut. |
| **DECISION_009** | La matriz de proceso (guillotina / oxicorte / láser). |
| **DECISION_010** | **Pedido ≠ Lote** y **el estado vive en la pieza**. El estado del pedido se calcula a partir de sus piezas, nunca al revés. |

### Una corrección de redacción que importaba

La **DECISION_002** decía que *"el sistema no implementa nesting, G-code ni CAM"*. Leído así, un agente podía concluir que **el G-code no es asunto nuestro** — y eso es falso: **CostADCAM es nuestro postprocesador y funciona**. Brújula ya lo decía bien (*"el postprocesador propio hace G-code — no reimplementar"*).

La corregí: **el límite es dónde vive, no de quién es.** La app no lo reimplementa; CostADCAM lo hace y sigue siendo válido.

### La página de precios: **muestra, no escribe**

Pediste recuperar *"la página donde anotábamos los precios"*. Decidí que sea **de solo lectura**, y te explico por qué:

**La arquitectura cambió desde aquella versión.** Antes no había un dueño de los precios. Hoy sí: **Tango es el maestro** (regla 4 de Brújula), y la cadena es **Excel → Tango → ERPNext (copia)**. Si la página escribiera precios, tendríamos **dos lugares donde el precio "es verdad"**, y el sistema se desincronizaría de la facturación real **en silencio** — el tipo de problema que se descubre tarde y sale caro.

Entonces: muestra los precios **agrupados por familia**, en solo lectura, **con la fecha de la última sincronización a la vista** (un precio sin fecha de sync engaña al que lo lee). Para corregir un precio, el camino sigue siendo **Excel → Tango**.

**Ojo con una confusión que separé:** los **parámetros de cálculo** (el precio por segundo de láser, los coeficientes) **no son precios de Tango** — son nuestros y **sí se editan**, en su propio lugar. Que la página sea de lectura no te bloquea eso.

**Si al verla te resulta inútil sin poder editar**, Vega tiene orden de **parar y avisarme** en vez de implementarlo igual: eso sería cambiar un criterio de negocio, y eso lo decidís vos.

### La que te escalé — ya resuelta

**El umbral de "espesor alto" para mandar una pieza a oxicorte no estaba en Brújula.** Es criterio de taller, así que te lo escalé en vez de inventar un número, y dejé esa rama inactiva mientras tanto.

**Lo definiste el mismo día: 19 mm (3/4").** Ya quedó formalizado en la DECISION_009 y la matriz de proceso está **completa**:
- Rectángulo sin perforaciones → **guillotina** (y sale del lote de láser)
- Espesor **≥ 19 mm** → **oxicorte**
- El resto → **láser / plasma**

---

## 6. Qué cambió para el equipo

- **Brújula es lectura obligatoria** para los 10 agentes, antes de su próxima tarea. Ya se los mandé.
- **La matriz de fuentes de verdad** también, con la regla de "si algo la contradice, parás".
- **Las pausas siguen firmes:** Lechu (MES) y Nido siguen en pausa. Las decisiones nuevas **no reactivan** esas tareas — dejan el modelo fijado para cuando las retomes, así nadie lo reinventa distinto.

---

## 7. Qué quedó sin leer (honestamente)

Entre los dos repos viejos hay **unos 292 documentos**. **No los leímos todos.**

**Lo que sí se leyó a fondo:** la identificación de los repos, las arquitecturas principales, los registros de decisiones, la documentación de Brújula y la mía, y una búsqueda temática dirigida por los temas que importan (precio, plegado, tolerancias, nesting, Tango, CypCut).

**Lo que quedó pendiente**, y por qué:
- Los **contratos técnicos detallados** entre módulos (uno por uno).
- La **documentación de gobernanza de agentes** de aquella época: reglas de trabajo autónomo, plantillas, tableros de proyecto.
- Los **archivos "léeme" de cada módulo** por separado.

Son **mucho volumen y poco valor** para lo que buscábamos: son documentos sobre *cómo trabajaban los agentes entre sí*, no sobre *cómo funciona la metalúrgica*. La apuesta fue priorizar negocio y taller.

**Riesgo asumido:** podría haber quedado alguna definición de negocio escondida ahí adentro. Lo considero poco probable pero **no imposible**, y prefiero decírtelo a dejarlo tapado.

**Si querés, se hace una segunda pasada** sobre un área puntual (por ejemplo, todos los contratos con Tango). Se pide y se hace.

**Dos cosas más, para que estén dichas:** no apareció ningún dato sensible ni contraseña en los repos viejos. Y no se tocó nada: fue todo lectura, cero cambios en cualquiera de los tres repositorios.

---

## Lo que me llevo

1. **Brújula es el activo más valioso del proyecto** y estuvo subutilizado. Ya es lectura obligatoria.
2. **Los repos viejos no tienen el modelo de precio.** No hay atajo: sigue por el simulador de movimiento de Punto.
3. **Lo que estaba perdido no era código: era criterio de negocio tuyo**, escrito una vez y no vuelto a leer. Ese es el tipo de pérdida que más caro sale, y es la que este relevamiento vino a frenar.
