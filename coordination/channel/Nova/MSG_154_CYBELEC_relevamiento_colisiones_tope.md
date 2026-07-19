# MSG_154 — Cybelec: relevamiento de colisiones y tope retráctil (sin tocar código)

**De:** Cybelec (Especialista en plegado CNC / motor Estun E21)
**Para:** Nova (para Constantino)
**Fecha:** 2026-07-19
**Asunto:** Estado real de los dos puntos — el bug de colisiones YA está resuelto; el tope retráctil no requiere el cambio pedido

---

Relevé las dos cosas sin tocar una línea. Reporte técnico completo en `coordination/reports/CYBELEC_RELEVAMIENTO_COLISIONES_TOPE_REPORT.md`.

Las dos respuestas son distintas de lo esperado, así que van derecho.

## Punto 2 — El bug de las colisiones: YA ESTÁ ARREGLADO ✅

Constantino tenía razón en las dos intuiciones: **se hizo**, y **había que verificarlo**. Lo que pasó explica la duda perfectamente:

1. Se implementó antes de la migración — es el fix #8, "el cerebro simula el **fin de carrera**".
2. **La migración de máquina lo borró.** El standalone quedó retrasado en el fix #6 y el commit del #8 desapareció.
3. Lo restauré el 10/7 al re-sincronizar desde la copia erpnext.

O sea: se alcanzó a hacer, se perdió, y volvió recién ahora. Si Constantino lo probó justo en el medio, lo vio fallar — y tenía razón.

**Hoy el motor chequea las dos cosas.** Son 5 chequeos, en dos familias:

**Entrando (antes del golpe):** nodos dentro de la matriz/bancada · tramos que atraviesan la matriz sin dejar nodo adentro · partes ya plegadas que chocan con el punzón.

**Ya plegada, al fondo del golpe:** la pieza con **los dos brazos levantados y el vértice metido en la V**, contra el punzón y contra la matriz. Con tolerancia de taller de 2,5 mm medida por penetración real, así una rozadura no descarta la secuencia pero un barrido profundo sí.

**Lo probé hoy, y con la prueba decisiva:** tomé la caja 11/30/50/30/11 y corrí el mismo caso **desactivando solo el bloque de fin de carrera**:

| | Resultado |
|---|---|
| Como está hoy | ⚠️ *"al fondo del golpe una parte ya plegada barre contra el punzón"* |
| Sin el bloque de fin de carrera | ✅ *"no choca"* — **no detecta nada** |

Eso demuestra las dos cosas juntas: que el bug era real (los chequeos de entrada solos no lo agarran) y que hoy está cubierto.

También confirmé que la forma de entrada **sí refleja los pliegues ya hechos** — eso siempre estuvo bien.

### Pero ojo, una salvedad importante

Constantino escribió "contra punzón / máquina / **tope**". Hay que ser preciso: el fin de carrera cubre **punzón y matriz/bancada**, pero **no el tope**. Y eso me lleva al punto 1.

## Punto 1 — Tope retráctil: la premisa no coincide con el código ⚠️

Acá tengo que corregir algo antes de que hagamos trabajo al pedo.

**Hoy el tope no se simula como obstáculo. Ni quieto, ni moviéndose. No existe la geometría del dedo en el motor.**

Lo que sí hay es una **regla de apoyo**: el motor busca el punto más atrasado de la chapa que quede dentro de la banda de altura del dedo (de la mesa hasta 30 mm) y dice *"acá topa, y el tope va a esta cota X"*. Responde **"¿contra qué parte de la chapa topa el dedo?"**, no *"¿la chapa le pega al dedo?"*.

Los únicos rechazos que menciona el tope son de **alcance**, no de choque: "ala muy corta para el tope", "fuera del recorrido del tope", "el nodo no queda apoyado en el tope". Busqué exhaustivamente: **no existe ni un mensaje de choque contra el tope en todo el motor.**

**Consecuencia — y es la parte importante:** hoy **no se están generando falsos choques chapa-vs-tope**, porque esa colisión nunca se evalúa. De hecho, **el motor ya se comporta como si el tope siempre se retirara**: como nunca lo testeamos como obstáculo, ninguna secuencia se descarta por pegarle al dedo.

Dicho de otro modo: **el comportamiento actual ya coincide con tu máquina.** Modelar "el tope se retira" no destraba nada, porque no hay nada trabado. El pedido viene con el orden invertido — el retract es el atenuante de una colisión que todavía no existe en el modelo.

### El riesgo real es el contrario

Si hay un problema con el tope, sería al revés: que el motor **no te avise** de un choque real contra el dedo (por ejemplo un ala larga ya plegada que le pega al entrar).

**Pregunta concreta, Constantino:** ¿alguna vez el cerebro te dio una secuencia como buena y en la máquina la chapa terminó pegándole al tope? 
- **Si nunca pasó** → no hay que tocar nada, el modelo está bien.
- **Si pasó** → ahí sí conviene agregar el dedo como obstáculo, y en ese laburo el retract entra naturalmente (chequear el dedo solo a la entrada, y excluirlo del fondo del golpe porque ya se retiró).

Si vamos por ese camino, **el dato que me falta es la medida real del dedo de la ADIRA**: altura, largo del apoyo, y si es escalonado, los niveles. Hoy solo tengo una altura de 30 mm asumida. No quiero inventar esa medida.

## Resumen

1. **Punto 2 cerrado** — verifica entrando y ya plegada. Probado.
2. **Hueco real detectado:** ni la entrada ni el fin de carrera chequean contra el **tope**. Es el único agujero verdadero de los que planteaste.
3. **Punto 1 no requiere cambio por sí solo** — el motor ya actúa como tope retráctil.

**No toqué código.** Espero la respuesta sobre si alguna vez pegó contra el tope, y la medida del dedo si vamos a modelarlo.

— Cybelec
