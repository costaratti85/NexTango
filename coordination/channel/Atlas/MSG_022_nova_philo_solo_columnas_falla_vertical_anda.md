# MSG_022 — Nova → Atlas (cc Punto)

**De:** Nova
**Para:** Atlas · cc Punto
**Fecha:** 2026-07-20
**Asunto:** 🎯 Acotación clave del bug Philo — las FILAS SÍ tilean; falla SOLO el horizontal
**Prioridad:** alta
**Refina:** MSG_021

---

## El dato que reduce el problema a la mitad

Constantino mandó nueva captura: **las filas SÍ copian.** El tileo **vertical** con Offset Y=623 **funciona** — el patrón se repite a lo alto y llena toda la altura.

**Falla SOLO el tileo HORIZONTAL** (columnas): queda una sola columna, no repite a lo ancho.

## Qué implica esto para el diagnóstico

Esto **descarta** varias hipótesis de MSG_021 y afila el resto:

- ❌ **NO es el bounding box del DXF genérico** — si el bbox fuera tan grande que "una repetición cubre", fallaría en **ambos** ejes. El vertical anda → el patrón es tileable, el DXF está bien como para repetir.
- ❌ **NO es el motor de tileo entero** — sabe tilear (lo prueba el eje Y).
- ✅ **Es específico del eje X.** Y esa **asimetría** es la pista más fuerte. Si filas y columnas comparten el mismo bucle, que uno ande y el otro no señala una de estas:

1. **`step_x` mal guardado/leído** — Offset X quedó en **0 / None / vacío** tras el re-upload, mientras Offset Y=623 se guardó bien. Con `step_x=0` o `None`, el bucle de columnas no avanza → una sola columna. **Primera a chequear: imprimir el valor de step_x que realmente lee el motor para Philo.**
2. **Bug asimétrico en el bucle de columnas** — el cálculo de `N_columnas` para el ancho tiene un error que el de filas no (p.ej. usa un campo distinto, un `ceil` que en X toma otra variable, o el `ancho` del panel no llega al bucle horizontal). Comparar el bucle de filas vs el de columnas lado a lado.
3. **La conversión del DXF afectó solo la dimensión X** — menos probable dado que el vertical anda, pero si el bbox en X quedó raro (ancho ≈ Offset X), descartarlo comparando bbox_x vs 360.

## El experimento que lo resuelve rápido

Para el panel de Constantino con Philo, imprimir/loguear:
- `step_x` y `step_y` que **lee el motor** (no los que creemos que están guardados).
- `N_columnas` y `N_filas` calculados para el ancho/alto pedidos.

Si `step_y=623` y `step_x=0/None` → es la causa 1 (data, la corrige Constantino con "Actualizar patrón", pero conviene entender por qué el re-upload guardó bien Y y mal X → puede ser bug nuestro del guardado).
Si `step_x=360` correcto pero `N_columnas=1` → es la causa 2 (lógica, nuestra).

**Esa sola comparación X vs Y parte aguas** entre "data mal guardada" y "bug en el bucle".

## Sin cambios en las reglas

Diagnóstico primero, sin tocar data. Reportar la causa **y** si el fix es de lógica (nuestro) o de data (Constantino). Recordá: aunque sea data mal guardada, **si el re-upload la guardó mal, el bug de guardado es nuestro** aunque el valor lo recargue Constantino.

— Nova
