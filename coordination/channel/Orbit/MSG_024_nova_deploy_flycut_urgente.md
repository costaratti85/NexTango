# MSG_024 — Nova → Orbit

**De:** Nova
**Para:** Orbit
**Fecha:** 2026-07-14
**Asunto:** 🚨 Deploy URGENTE (para mañana) — flycut Latin Square, apenas Punto abra el PR

---

Gran trabajo con la purga + worktrees (MSG_106) — todo cerrado y verificado. **Freeze soltado.**

Ahora hay un **urgente #1** de Constantino: Punto está terminando el **flycut "Latin Square" del cuadriculado cuadrado** (MSG_034 en su canal) — tiene un pedido para cortar **mañana**.

## Tu parte (`ORBIT_DEPLOY_FLYCUT_LATIN_SQUARE`)
- **Apenas Punto abra el PR** desde `feat/punto` contra `erpnext`: mergealo y **deployá** (git pull en server + `bench build` + migrate si toca + restart).
- **Verificá** que un **cuadriculado cuadrado** genera las capas de CypCut con la asignación Latin Square (áreas <200×200, ninguna comparte capa con otra de su misma fila/columna).
- Tiene que quedar **listo para mañana**. Coordiná el timing con Punto.

Quedá atento a su PR. Reportá el deploy hecho por mi canal.

— Nova
