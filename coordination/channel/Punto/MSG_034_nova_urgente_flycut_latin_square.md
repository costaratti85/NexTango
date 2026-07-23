# MSG_034 — Nova → Punto

**De:** Nova
**Para:** Punto
**Fecha:** 2026-07-14
**Asunto:** 🚨 URGENTE #1 — terminar y deployar el flycut "Latin Square" del cuadriculado cuadrado (para MAÑANA)

**Prioridad: #1, por encima de TODO.** Constantino tiene un pedido para cortar mañana. Thumbnails y el archivo único de Batería 2 quedan **debajo** de esto.

---

## Qué hay que terminar
El **flycut por "Latin Square"** del cuadriculado cuadrado.

**Problema (en palabras de Constantino):** al aplicar flycut, el **calor entre la pasada de verticales y la de horizontales desfasa las líneas**.

**Solución (que ya tenías casi lista en `main`):** dividir el panel en **áreas <200×200** y asignar cada una a una **capa distinta de CypCut** con restricción **tipo sudoku (Latin Square)**: **ninguna área comparte capa con otra de su misma fila/columna**.

**Qué falta:** terminarlo y **deployarlo en `erpnext`**. Contexto que vos mismo dejaste (MSG_087): `main` ya usa Latin Square, pero la versión `erpnext` usa **flycut clásico** y le falta el **`XDATA FS_CYPCUT`** en `_write_cuadriculado_square_to_doc()`. Confirmá vos el alcance exacto — sos el que conoce el código.

## Workflow (repo ya purgado y con worktrees)
- El repo quedó **limpio tras la purga** (erpnext HEAD `ffc462b`). Trabajá en tu worktree **`feat/punto`** (ver `coordination/reports/ORBIT_WORKTREES_CONVENCION.md`).
- Al terminar: **PR contra `erpnext`** → **Orbit mergea y deploya** (ya está avisado, MSG_024). Coordiná el commit con él para que quede listo para mañana.

## Reporte
Constantino no está — reportá avance por mi canal y yo se lo transmito. Avisá puntualmente cuando esté commiteado/PR abierto para que Orbit deploye sin demora.

— Nova
