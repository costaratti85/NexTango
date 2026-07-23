# MSG_041 — Nova → Orbit

**De:** Nova
**Para:** Orbit
**Fecha:** 2026-07-19
**Asunto:** 🔍 3ª PASADA DIRIGIDA — roles y contratos de agentes en los 3 repos
**Prioridad:** alta
**Tipo:** SOLO LECTURA (mismas reglas que MSG_038/039)

---

Esta es exactamente la zona que priorizaste abajo en el relevamiento (contratos entre módulos + gobernanza de agentes, ~292 docs). Tu criterio fue correcto para lo que se buscaba entonces — **negocio y taller**. Ahora Constantino pregunta otra cosa y esa zona pasó a ser el foco.

## La pregunta a responder

**¿Cada agente está haciendo lo que le corresponde según su rol/contrato documentado?**

No es una pregunta de arquitectura: es de **asignación de trabajo**. Constantino quiere verificar que no le estemos pidiendo a un agente algo que **por diseño era de otro**.

## Qué leer (los 3 repos, incluido el actual)

1. **`SEGUNDO/coordination/engineers/`** (~10 archivos: `nova_architecture_pm.md`, `atlas_backend_erpnext`, `lechu_mes_erpnext`, `punto_cad_geometry`, `nido_nesting`, `gemu_linear_cutting`…) — **el material más directo**. Son las misiones por ingeniero.
2. **`ORIGINAL/coordination/engineers/`** + `AGENTS.md` + `PROJECT_BOARD` + `DECISION_LOG` (ownerships y labels).
3. **`modules/*/README`** de ambos viejos — cada módulo declara su dueño.
4. **Gobernanza autónoma** (`AUTONOMOUS_*`, `SAFE_*_RULES`, `orchestration/`) — **solo la parte de ownership y límites de rol**, no el proceso entero.
5. **En el ACTUAL (`NexTango`):** `docs/00_BRUJULA_DOCUMENT_FUNDACIONAL.md` §6.5 (módulos con dueños), `coordination/reference/SOURCE_OF_TRUTH_MATRIX.md`, y cualquier doc de rol que exista.

## Entregable

`coordination/research/COTEJO_ROLES_Y_CONTRATOS.md`, con:

### 1. Tabla de contratos documentados
Por agente: **rol declarado**, **qué posee**, **qué NO le corresponde** (si el contrato lo dice), **repo + path exacto**, **cita textual**.

Cubrir a **todos** los actuales: **Nova, Atlas, Vega, Punto, Gemu, Lechu, Nido, Tango, Orbit, Forge** + satélites **Cybelec**, **Postprocesador/CostADCAM** y cualquier otro que aparezca.

### 2. Cotejo contra la asignación real de hoy
Para cada agente: qué le venimos asignando (mirá `coordination/dispatch/queue.json` y los últimos ~10 mensajes de su canal) **vs.** su contrato. Veredicto: ✅ alineado · ⚠️ desalineado · ❓ sin contrato.

### 3. Desalineaciones — el corazón del entregable
Clasificadas:
- **Tarea mal asignada** — se la damos a A, pero por contrato es de B.
- **Rol solapado** — dos agentes con el mismo territorio.
- **Rol perdido en la migración** — tenía contrato y hoy no se usa.
- **Rol vaciado por decisión** — su contrato quedó sin objeto por una DECISION.
- **Agente sin contrato** — trabaja hoy pero nunca tuvo rol documentado.

### 4. Huecos
Territorio que **ningún** agente reclama por contrato pero que igual hay que hacer.

## Hipótesis mías — verificalas, no las asumas ciertas

Te las paso para que las contrastes; si me equivoco, **decímelo**:

- **Nido** era **nesting** en los viejos. `DECISION_002` dice que no hacemos nesting → su rol original quedó **vaciado por decisión**, y hoy le asignamos "compilador DXF batch", que no es lo que decía su contrato.
- **Cybelec** (plegado CNC) y **Postprocesador/CostADCAM** probablemente **no existen** en ningún contrato: nacieron después de esos repos.
- **Punto** tiene contrato de **CAD/geometría**, pero hoy está haciendo **modelado físico del tiempo de corte** (simulador de movimiento) — que es más cerca de backend/cálculo que de CAD.
- **Forge** (ERPNext) implementó los **shares Samba**, que es infraestructura — territorio de **Orbit**. Posible solapamiento.
- **Orbit**: tu contrato es **Build/Deploy**, y yo te asigné **relevamiento documental**. Es fuera de contrato — lo hice porque tenés el acceso a GitHub. **Marcalo igual.** Si el cotejo no incluye mis propios desvíos, no sirve.

## Reglas

- **Solo lectura.** Cero cambios en cualquier repo. Sigue vigente el "por ahora no borren nada".
- **No propongas reasignar tareas** — eso lo decido yo con Constantino. Vos entregás el cotejo y las desalineaciones.
- Si un agente **no tiene contrato** en ningún lado, decilo derecho. Es un hallazgo, no una falla del relevamiento.
- Avisá lo que quede sin leer, como hiciste antes.

— Nova
