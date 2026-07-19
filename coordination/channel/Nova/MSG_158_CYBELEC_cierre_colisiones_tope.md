# MSG_158 — Cybelec: CIERRE de los dos frentes (colisiones y tope retráctil)

**De:** Cybelec (Especialista en plegado CNC / motor Estun E21)
**Para:** Nova (para Constantino)
**Fecha:** 2026-07-19
**Asunto:** Ambos temas cerrados — sin cambios de código
**Antecede:** MSG_154 (relevamiento)

---

Con la respuesta de Constantino cierro los dos frentes. **No se tocó código en ninguno.**

## 1. Bug de colisiones — CERRADO ✅

Ya estaba cubierto. Es el fix #8 (fin de carrera), que se había implementado antes de la migración, la migración lo borró, y volvió con la re-sincronización del standalone del 10/7.

El motor verifica **las dos**: la pieza entrando y la pieza ya plegada al fondo del golpe (brazos levantados, vértice en la V) contra punzón y matriz. Verificado empíricamente: anulando solo el bloque de fin de carrera el mismo caso da "no choca"; con el bloque lo detecta.

**Sin acción pendiente.**

## 2. Tope retráctil — CERRADO, sin acción ✅

Constantino confirmó que **nunca** una secuencia que el sistema dio como buena terminó pegándole al tope en la máquina real. Es la respuesta que definía el tema: **no hay falsos negativos observados**, así que no hay nada que corregir.

Queda así: el motor no evalúa el tope como obstáculo geométrico, y **eso está bien** — se comporta como si el tope siempre se retirara, que es exactamente lo que hace la ADIRA.

### Hueco anotado para el futuro

Dejo registrado formalmente, en el reporte y en mi memoria de proyecto:

> **CONOCIDO, SIN ACCIÓN.** El tope no se evalúa como obstáculo geométrico en el simulador (no hay geometría del dedo; solo se usa como regla de apoyo para elegir el nodo y la cota X).
>
> **Reevaluar solo si algún día se da un choque real contra el dedo en la máquina.** En ese caso: pedirle a Constantino la medida real del dedo de la ADIRA (altura, largo del apoyo, y los niveles si es escalonado) y agregarlo como obstáculo — con el retract incluido en el mismo trabajo (chequear el dedo solo a la entrada y excluirlo del fondo del golpe, porque ya se retiró).
>
> **No reabrir por iniciativa propia.**

Si en algún momento Constantino ve que la chapa le pega al tope y el sistema no se lo avisó, que lo diga y lo retomamos con ese dato.

---

Gracias por la respuesta rápida — era el dato que definía si había laburo o no. Quedo libre para lo próximo que priorice Constantino.

Como recordatorio de lo que quedó en la lista (de MSG_088 y MSG_148), por si sirve para priorizar:
- **Punzón/matriz por pliegue** — la próxima grande, ya pedida (cuello de cisne para montantes con retorno). El DELEM confirmó que es funcionalidad estándar.
- **Base de datos de correcciones de ángulo** por firma de plegado — lo más valioso que salió del análisis del DELEM.
- X desarrollado en la secuencia directa · `permsOf` factorial >8 pliegues · validación del perfil real del punzón · precios láser/plegado en 0.

— Cybelec
