# CYBELEC_RELEVAMIENTO_COLISIONES_TOPE_REPORT

**Agente:** Cybelec
**Tarea:** Relevamiento previo (sin tocar código) — (1) tope retráctil y (2) estado del chequeo de colisión "pieza ya plegada"
**Fecha:** 2026-07-19
**Estado:** RELEVAMIENTO COMPLETO — sin implementación, esperando decisión

---

## RESPUESTA CORTA

| Punto | Estado |
|---|---|
| **2. Bug "no chequea la pieza ya plegada"** | ✅ **YA RESUELTO.** Es el fix #8 (fin de carrera). Se hizo antes de la migración, **la migración lo borró**, y lo restauré el 2026-07-10 en el commit de re-sync. Hoy verifica **las dos** cosas. |
| **1. Tope retráctil** | ⚠️ **La premisa no coincide con el código.** Hoy el tope **no se simula como obstáculo** en ningún momento — ni quieto ni retirándose. No hay falsos choques chapa-vs-tope, porque esa colisión **nunca se testea**. |

---

## PUNTO 2 — Chequeo de la pieza ya plegada: YA ESTÁ

### Historia (por qué Constantino no estaba seguro)

Esto explica la duda perfectamente:

1. Se implementó antes de la migración (fix #8, "el cerebro simula el FIN DE CARRERA").
2. **La migración de máquina lo perdió**: el standalone quedó retrasado en el fix #6 y el commit del #8 desapareció del repo.
3. Lo restauré el 2026-07-10 portándolo desde la copia erpnext, en el commit `97f3e49` *"re-sync standalone — porta fixes #7 (keepOrder) y #8 (fin de carrera)"*.

O sea: **se alcanzó a hacer, se perdió, y volvió recién ahora.** Constantino tenía razón en las dos intuiciones (que se había hecho, y que había que verificarlo).

*(Nota: el hash del commit figura como `97f3e49` y no como el `26090e4` original — la historia fue reescrita por un rebase de trabajo concurrente del equipo. El contenido es el mismo; verificado.)*

### Qué chequea hoy, exactamente

El motor corre **5 chequeos de choque** en `clearCheck()`, en dos familias:

**A) La pieza ENTRANDO (antes del golpe)** — siempre estuvo:
1. Nodos de la pieza dentro del perfil de matriz/bancada → *"una parte de la pieza queda dentro de la matriz/bancada"*
2. Tramos que **atraviesan** matriz/bancada sin dejar nodo adentro → *"una parte de la pieza atraviesa la matriz o la bancada"* (fix #5)
3. Tramos ya plegados que chocan con el punzón → *"una parte ya plegada choca con el punzón"*

**B) La pieza YA PLEGADA, al fondo del golpe (fin de carrera)** — fix #8:
4. → *"al fondo del golpe una parte ya plegada barre contra el punzón"*
5. → *"al fondo del golpe la pieza barre contra la matriz"*

El bloque B simula la pieza con **los dos brazos levantados y el vértice metido en la V**, rotando la geometría alrededor del pliegue actual, con tolerancia de taller `TOL_PEN=2.5 mm` medida por penetración real (`penDepth`, por muestreo) — así una rozadura nominal no descarta la secuencia pero un barrido profundo sí.

### Verificación empírica (corrida hoy en preview)

Probé la caja 11/30/50/30/11 y, sobre todo, hice la **prueba decisiva**: correr el mismo caso anulando **solo** el bloque de fin de carrera (`pl.bi=null`) y comparar.

| Caso | Resultado |
|---|---|
| Con fin de carrera (como está hoy) | ❌ `"al fondo del golpe una parte ya plegada barre contra el punzón"` |
| **Mismo caso, sin el bloque de fin de carrera** | ✅ `{clear: true}` — **no detecta nada** |

**Esto es la prueba de que el bug era real y de que está arreglado:** los chequeos de entrada por sí solos dan "no choca"; únicamente el bloque de fin de carrera lo agarra.

También verifiqué que **la geometría de los pliegues ya hechos sí se refleja en la forma de entrada**: con `done=[true,true,false,true]` el perfil sale doblado (nodos en y=32, y=13) contra la chapa plana (todo en y=2). O sea, la familia A ya "ve" lo doblado previamente; el fix #8 agrega el estado **al fondo del golpe**, que es lo que faltaba.

### ⚠️ Salvedad importante — el tope NO entra

Constantino escribió *"chocando contra punzón/máquina/**tope**"*. Hay que ser preciso:

- El fin de carrera cubre **punzón y matriz/bancada**. ✅
- **NO cubre el tope.** ❌

Y no es que falte solo en el fin de carrera: **no existe ningún chequeo de choque contra el tope en ningún punto del motor** (ver Punto 1).

---

## PUNTO 1 — Tope retráctil: relevamiento y alcance

### Cómo está modelado el tope hoy

El tope **no es un cuerpo físico** en la simulación. No hay geometría del dedo, ni polígono, ni segmentos, ni test de intersección contra él. Está modelado como una **regla de selección** en `feasible()`:

```
Buscar el nodo más atrasado (mayor x) de la chapa que caiga dentro de la
banda de altura [ -1.5 , mesa + FINGER_H ]   (FINGER_H = 30 mm)
→ ese nodo es el punto de apoyo, y su x es la cota X del tope.
```

Es decir: el modelo responde **"¿contra qué parte de la chapa topa el dedo y a qué X queda?"**, no *"¿la chapa le pega al dedo?"*.

Los únicos rechazos relacionados con el tope son **de alcance, no de choque**:
- `"ala muy corta para el tope"` (X < X_MIN = 5)
- `"fuera del recorrido del tope"` (X > X_MAX = 600)
- `"el nodo N no queda apoyado en el tope para este pliegue"` (el nodo cae fuera de la banda de altura)

Y el fix #6 agregó que un nodo **colgando por debajo de la mesa** no puede topear (banda inferior −1.5).

**Confirmado por búsqueda exhaustiva:** no hay ni un mensaje de choque contra el tope en todo el motor. El único match textual de "contra el tope" es un cartel de la UI de calibración (*"¿Cuánto midió el ala contra el tope?"*).

### Consecuencia — y esto es lo importante

**Hoy NO se están generando falsos choques chapa-vs-tope, porque esa colisión nunca se evalúa.**

De hecho, el motor **ya se comporta como si el tope siempre se retirara**: como nunca lo testeamos como obstáculo, ninguna secuencia se descarta por pegarle al dedo. Es decir, el comportamiento actual **ya está alineado** con la máquina real de Constantino.

Por eso: **modelar "el tope se retira" no destraba nada por sí solo — no hay nada que corregir.** El pedido tiene el orden invertido: el retract es un *atenuante* de una colisión que todavía no existe en el modelo. Primero habría que agregar la geometría del dedo como obstáculo, y **recién ahí** el retract tendría sentido (para no marcar choques falsos durante el golpe).

### El riesgo real es el opuesto

Si hay un problema hoy con el tope, sería un **falso negativo**, no un falso positivo: el motor **no avisaría** de un choque real contra el dedo (por ejemplo, si el tope no llega a retirarse a tiempo, o si un ala larga ya plegada le pega al dedo al entrar).

**Pregunta para Constantino:** ¿alguna vez el cerebro te dio una secuencia buena y en la máquina la chapa terminó pegándole al tope? Si nunca pasó, el modelo actual está bien y no hay que tocar nada. Si pasó, ahí sí conviene agregar geometría del dedo.

### Alcance de cada opción

**Opción A — no tocar nada (recomendada si nunca hubo choques reales contra el tope).**
Costo cero. El motor ya se comporta como tope retráctil.

**Opción B — agregar geometría del dedo + retract (solo si Constantino vio choques reales).**
Alcance estimado:
1. Definir el perfil del dedo (hoy solo existe `FINGER_H=30` como altura de banda). Con el DELEM como referencia: altura del dedo, largo del apoyo, y hasta 4 niveles escalonados. **Requiere que Constantino mida el dedo real de la ADIRA.**
2. Agregar el dedo como obstáculo en `clearCheck()`, posicionado en la X calculada del paso.
3. Aplicar el retract: chequear el dedo **solo en la entrada** (antes de que la trancha pise) y **excluirlo del fin de carrera** (ya se retiró).
4. Recalibrar: puede cambiar secuencias que hoy salen buenas.

Son cambios acotados y localizados (`clearCheck` + constantes de geometría), pero **el dato que falta es la medida real del dedo**, y no tiene sentido inventarla.

---

## Resumen para decidir

1. **Punto 2 está cerrado.** El motor verifica las dos: entrando y ya plegada al fondo del golpe. Probado empíricamente. Fue el fix #8, perdido en la migración y restaurado.
2. **Falta genuina:** ni la entrada ni el fin de carrera chequean contra el **tope**. Es el único hueco real de los que planteó Constantino.
3. **Punto 1 no requiere cambio por sí solo.** El motor ya actúa como si el tope se retirara. Modelar el retract sin antes modelar el dedo no cambia ningún resultado.

**No toqué código.** Espero definición de Constantino sobre la Opción A/B y, si elige B, la medida del dedo real.

— Cybelec
