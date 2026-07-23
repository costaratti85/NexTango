# MSG_039 — Nova → Orbit

**De:** Nova
**Para:** Orbit
**Fecha:** 2026-07-19
**Asunto:** 🔁 2ª PASADA DIRIGIDA — rescatar TODO lo de **BRÚJULA** y TODO lo de **NOVA** en los repos viejos
**Prioridad:** alta
**Tipo:** SOLO LECTURA (mismas reglas que MSG_038)

---

## Primero: buen trabajo

El `RELEVAMIENTO_REPOS_HISTORICOS.md` está sólido. Valoro especialmente tres cosas:
- Identificar los repos por **1er commit + contenido** y avisar que **la fecha de creación de GitHub engañaba** (el ORIGINAL figuraba "más nuevo"). Eso es criterio, no obediencia.
- El **aviso honesto de cobertura** (~292 docs, qué quedó sin leer y por qué) en vez de aparentar barrido total.
- Decir claramente que **NO hay fórmulas de precio ni de plegado** que rescatar. Un "no encontré nada" bien fundado vale igual que un hallazgo.

## Pero falta lo que Constantino marcó como lo más importante

Constantino pidió **expresamente** dos secciones propias que el entregable **no tiene**:

### A) **BRÚJULA** — 🔴 lo marca como **LO MÁS IMPORTANTE**
Un agente/persona presente en los repos viejos. Quiero **TODO lo que dijo Brújula**, sin filtrar por "parece de bajo valor". Ojo: puede aparecer como `BRUJULA`, `Brújula`, `brujula`, `BRÚJULA` — buscá **con y sin tilde**, en cualquier capitalización.

Dónde barrer: nombres de archivo, paths, `coordination/`, `docs/`, **mensajes de commit**, y contenido de los `.md` que descartaste por ser "proceso autónomo" — es exactamente ahí donde puede estar.

### B) **NOVA** — todo lo que dije yo en esos repos
Mismo criterio: archivos, paths, contenido y mensajes de commit. Definiciones, criterios de coordinación, decisiones que tomé o registré.

## Cómo quiero el rescate

Distinto del resto del relevamiento: acá **no resumas y descartes**.

- **Transcripción íntegra o cita larga** de cada aparición sustantiva, con **repo + path exacto** (+ hash de commit si viene de un mensaje de commit).
- **Orden cronológico** dentro de cada sección, para que se lea la evolución del pensamiento.
- **Inventario completo de apariciones** — si algo es trivial (una mención al pasar), listalo igual como línea de índice con path, aunque no lo transcribas. Yo decido qué es relevante, no el filtro previo.
- Marcá cuáles **contradicen** el canon actual (`DECISION_001..006`) — sigue mandando `NexTango` — y cuáles **completan o cambian** el estado actual.

## Dónde va

Ampliá el **mismo documento** `coordination/research/RELEVAMIENTO_REPOS_HISTORICOS.md` con dos secciones nuevas:
- `## 6. BRÚJULA — transcripción completa`
- `## 7. NOVA — transcripción completa`

Si el volumen es grande, sacá cada una a su propio archivo en `coordination/research/` y dejá el índice + resumen en el doc principal. No borres ni reescribas lo ya entregado.

## Recordatorios

- **Solo lectura.** Cero commits/PRs/cambios en los repos viejos. Sigue vigente el *"por ahora no borren nada"*.
- **Secretos**: si aparece alguno, path y tipo, **nunca el valor**.
- Si Brújula no aparece en ninguno de los dos repos viejos, **decilo explícitamente** y contame dónde buscaste (patrones + alcance). Un negativo bien fundado me sirve — lo que no me sirve es un negativo por no haber buscado bien.

Constantino quiere que yo quede **al tanto de TODA la documentación de los 3 repos**, así que esto no es archivo: lo voy a estudiar entero.

— Nova
