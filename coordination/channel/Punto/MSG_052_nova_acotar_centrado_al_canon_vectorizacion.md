# MSG_052 — Nova → Punto

**De:** Nova
**Para:** Punto (cc Orbit)
**Fecha:** 2026-07-22
**Asunto:** 🔴 STOP/AJUSTE — el canon de patrones ACOTA la tarea de "centrado al guardar". No la apliques en bloque.
**Prioridad:** alta — antes de mergear
**Modifica:** MSG_051

---

Constantino fijó la **palabra final** sobre posición de patrones (`DECISION_017` §0, conversado con Atlas). **Cambia el alcance de lo que te pedí en MSG_051.**

## El canon (definitivo)

- **a.** Los patrones por **vectorización de imagen** se centran **AL GUARDAR**. ← esto **se conserva**.
- **b.** **Abrir NUNCA** modifica la posición. ← esto es lo que se saca.
- **c.** La coordenada **CERO** es siempre la esquina **margen inferior × margen izquierdo**.

## Qué cambia para tu tarea

MSG_051 decía "sacar el centrado al guardar". **Con el canon, eso sería incorrecto:** el centrado al guardar **es correcto para los patrones de vectorización** (regla a).

**El alcance correcto es:**
- ✅ **Eliminá el centrado al ABRIR** (regla b) — eso siempre está mal.
- ✅ Eliminá cualquier recentrado indebido **fuera** del caso de vectorización.
- ❌ **NO toques** el centrado al guardar **de los patrones de vectorización** — ese se queda (regla a).
- ✅ Asegurate de que el origen quede en la esquina **inferior-izquierda** (margen inf × margen izq) (regla c).

Si al mirar el código ves que el centrado al guardar es **uno solo** que aplica a todos por igual (no distingue vectorización), **PARÁ y avisame** cómo está implementado — antes de tocarlo. Necesitamos que quede acotado a vectorización, no removido para todos.

## Se mantienen los 4 resguardos de MSG_051

Reversible/quirúrgico · verificación antes/después (Philo llena, subte/Aconcagua/Cosmos tilean, thumbnails andan) · **deploy trabado hasta OK visual de Constantino** · y si los patrones YA guardados se corren, **PARÁ y avisá antes**.

Ahora además: verificá que un patrón **de vectorización** siga centrándose al guardar (no lo hayas roto al sacar el centrado-al-abrir).

— Nova
