# MSG_093 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino)
**Fecha:** 2026-07-11
**Asunto:** AVANCE — precio ya llega a Panel Decorativo (commit 0e662a8)

Seguimiento de MSG_092.

## Hecho (commit `0e662a8`, erpnext)

Corrección **(C)**: el endpoint `api/paneles.calcular()` ahora **devuelve el precio**.
Antes mandaba a la UI los segundos (`tiempo_laser_s`) pero descartaba el costo que el
motor ya calculaba. Ahora cada línea incluye:
`costo_material`, `costo_maquina`, `costo_total` (por panel) + `costo_total_linea`
(× cantidad) + `prices_missing`.

- Cambio **aditivo** (no toca campos existentes) → no rompe el front actual.
- Compila OK. No hay tests sobre el endpoint, así que no rompí ninguno.
- **Falta que Vega conecte estos campos en la pantalla** para ver el precio. Aviso aparte
  puede ir por su canal si querés.

## Frenado, esperando decisión de Constantino (de MSG_092)

- **(A) Sumar el tiempo de TRAVEL a los segundos**: al inspeccionarlo quedó acoplado —
  para patrones genéricos hay que calcular el recorrido entre agujeros, y hace falta la
  **velocidad de desplazamiento rápido (mm/s) de la máquina**. Sin ese dato no avanzo.
- **(D) Unificar la fuente del precio-por-segundo** (`precio_segundo_laser` doctype vs
  `precio_segundo_maquina` JSON).
- Confirmar que nos quedamos con el **modelo nominal** (no el físico calibrado) y validar
  la **tabla de velocidades**.

Con esas 4 respuestas cierro la fórmula de segundos completa. Mientras tanto, el precio ya
fluye end-to-end en el backend.

— Punto
