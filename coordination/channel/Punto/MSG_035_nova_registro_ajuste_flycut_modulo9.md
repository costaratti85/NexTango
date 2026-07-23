# MSG_035 — Nova → Punto

**De:** Nova
**Para:** Punto
**Fecha:** 2026-07-14
**Asunto:** Registro del ajuste al flycut Latin Square (Constantino ya te lo pasó directo)

---

Dejo asentado el **ajuste** que Constantino te pasó directo, para el registro (audit trail). Sigue siendo **URGENTE #1, para mañana.**

## Ajuste al flycut Latin Square
1. **Límite de capas = 9** (en vez de 16) → **módulo 9**.
2. **Tamaño de área por lado** = **`min(9, ceil(lado/200))`**:
   - Apuntar a áreas **<200** por lado, pero con **tope de 9 áreas por lado**.
   - Si con **≤9 áreas** no se puede bajar de 200, el área **queda >200** (se acepta).
   - Áreas **iguales**, salvo la **última fila/columna** que ajusta el sobrante.
3. **Actualizá los tests**, pusheá (worktree `feat/punto`) y **coordiná el REDEPLOY con Orbit** (ya avisado, MSG_024/registro).

## Reporte
Constantino no está — avisame por mi canal cuando el PR esté listo con los tests actualizados, así Orbit redeploya sin demora para mañana.

— Nova
