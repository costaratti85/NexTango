# PROPUESTA — Arreglos de roles a partir del cotejo

**Estado:** 🟡 PROPUESTA — **NO ejecutada.**
**Autora:** Nova · **Fecha:** 2026-07-19
**Base:** `coordination/research/COTEJO_ROLES_Y_CONTRATOS.md` (Orbit, MSG_156)

Divido en **lo que decido yo** (organización del equipo) y **lo que escalo a Constantino** (estructura y criterio de negocio).

---

## A. DECIDO YO

### A.1 Contrato para Cybelec y Postprocesador → **SÍ, formalizarlos**

Ambos trabajan hoy sin rol documentado. Un agente sin contrato no tiene frontera: ni él ni yo podemos decir si una tarea le corresponde.

- **Cybelec** — Plegado CNC (Cybelec / Estun E21 / DELEM). Posee: motor de plegado, secuencia de plegados, colisiones, formatos de las controladoras. **No** posee: corte, geometría de chapa plana, precio.
- **Postprocesador** — G-code y postproceso (CostADCAM). Posee: generación de G-code, contrato DXF→postprocesador, particularidades de máquina (I/J absoluto). **No** posee: nesting (es de CypCut), ni lógica dentro de la app Frappe (`DECISION_002`).

Sale como `DECISION_013_CONTRATOS_CYBELEC_Y_POSTPROCESADOR`.

### A.2 Frontera Orbit ↔ Forge en infraestructura → **la fijo**

| Territorio | Dueño |
|---|---|
| Build, deploy, git, worktrees, historial, CI | **Orbit** |
| Sistema operativo del server, servicios, Samba, red, permisos, `/etc` | **Orbit** |
| Bench de Frappe, apps, migraciones, DocTypes, configuración de ERPNext | **Forge** |
| Deploy *de la app* al bench | **Orbit ejecuta**, Forge valida el estado del bench |

**Regla simple:** *si es del sistema operativo, es de Orbit; si es de Frappe/ERPNext, es de Forge.*

El caso Samba se resuelve así: era de Orbit. Lo hizo Forge por urgencia. Retroactivamente correcto, a futuro va por Orbit.

Sale como `DECISION_014_FRONTERA_ORBIT_FORGE`.

### A.3 Huecos sin dueño — asignación provisoria

| Hueco | Dueño propuesto |
|---|---|
| **Infra pura** | **Orbit** (resuelto en A.2) |
| **MES / estados por pieza** | **Lechu** — es su contrato; sigue **en pausa**, pero el hueco tiene dueño |
| **OCR de facturas de proveedores** | **Sin dueño, y así queda.** Está en Brújula pero no hay frente activo. **No inventar un agente para territorio que nadie va a tocar este sprint.** Se asigna cuando se active. |
| **Cálculo de recursos / física de máquina** | ⬆️ **Escalado — ver B.1** |

### A.4 Carga de Punto → **acción inmediata, independiente del rol**

Punto tiene **60 tareas**; el siguiente es Vega con 35. **Esto es un riesgo operativo hoy**, no una discusión de organigrama: el frente más crítico del sprint (el precio) depende de un agente saturado.

Decido, sin esperar la definición estructural:
- **Congelar** asignaciones nuevas a Punto salvo el simulador y el bug de precio.
- `PUNTO_CONFIRMAR_TOLERANCIAS_CAD` y `PUNTO_PRECISION_CAMPOS_LASER` → **quedan detrás del simulador**, explícitamente.
- `PUNTO_BATERIA2_ARCHIVO_UNICO` (posiblemente innecesaria) → **cerrar** si sigue sin objeto.

---

## B. ESCALO A CONSTANTINO

### B.1 🔴 El desborde de Punto: ¿oficializarlo, o crear un rol de Cálculo?

**El hecho:** Punto tiene contrato de **CAD/geometría**, pero hoy hace **física de máquina y modelo de precio** (el simulador de movimiento). El cotejo marca este hueco como **el más caro**, y está **tapado** justamente porque Punto lo viene cubriendo de hecho.

**Por qué no lo decido yo:** no es organizar el equipo, es decidir **qué territorio del negocio merece un dueño propio**. El cálculo de recursos —tiempo de máquina, consumo de material, y de ahí el **precio**— es el corazón económico del sistema (Brújula: *"recurso industrial como unidad económica"*). Definir si eso es una especialidad separada o una extensión del CAD es estructural.

**Opción 1 — Oficializar el desborde.** Se amplía el contrato de Punto a "geometría + cálculo de recursos".
*A favor:* cero fricción, Punto ya tiene todo el contexto (la calibración, el simulador, la física del 1650).
*En contra:* consolida la saturación (60 tareas) y deja el frente más crítico con **un solo punto de falla**.

**Opción 2 — Crear un rol de Cálculo de Recursos.** Agente nuevo, dueño de tiempo/costo/precio. Punto vuelve a CAD/DXF puro.
*A favor:* el frente más caro tiene dueño propio; descarga a Punto; el precio deja de competir con la geometría.
*En contra:* costo de traspaso en medio del sprint, con el simulador a mitad de camino.

**🔺 Argumento nuevo (2026-07-19) — el motor de cálculo tiene MÁS DE UN consumidor.**

Cuando escribí las opciones, el cálculo de recursos parecía servir solo al **precio**. `DECISION_012` (contrato de Nido) muestra que no:

- El **precio** necesita los segundos de máquina.
- **Nido** necesita los segundos de máquina **por pieza** para el criterio *"pocos segundos de máquina"* — y Nido es, en palabras de Constantino, *"la función más importante para poder hacer los nestings"*.

O sea: el motor de cálculo **no es un detalle interno del precio**, es **infraestructura compartida** de la que cuelgan al menos dos frentes.

Eso cambia el peso del argumento. Dejarlo dentro del contrato de CAD de Punto significa que **el frente de compilación de lotes va a depender de un rol que no lo tiene como responsabilidad declarada**, y de un agente ya saturado. Es el escenario clásico donde un consumidor queda esperando a un dueño que nunca priorizó ese trabajo, porque formalmente no era suyo.

**Refuerza la Opción 2.**

**Mi recomendación: Opción 2, pero NO ahora.** Partir el frente del precio en plena Etapa 1 del simulador es la peor forma de crear un rol. **Que Punto termine el simulador; el traspaso se hace con el modelo cerrado.** Mientras tanto, la carga se contiene con A.4.

El timing tampoco urge: los dos consumidores están alineados en el tiempo. Nido está bloqueado por MES (en pausa), así que **no necesita el motor todavía**. La ventana para crear el rol es **cuando el simulador cierre y antes de que se retome MES**.

### B.2 🟡 ¿El OCR de proveedores sigue en el norte?

Está en Brújula como flujo completo, pero nunca se activó y no tiene dueño. **No es urgente** — solo confirmame que sigue en el plan a largo plazo y no es algo que ya descartaste. Si sigue, se le busca dueño cuando se active.

---

## Lo que NO propongo tocar

- ~~**Nido** (rol vaciado)~~ → **CORREGIDO 2026-07-19.** No estaba vaciado: estaba **mal descrito**. Constantino definió su rol real y quedó formalizado en **`DECISION_012`** — *compilador de lote de corte por demanda*, aguas arriba del nesting. Sigue en pausa (depende de MES), pero el contrato ya está fijado.
- **Gemu**: contrato vigente y correcto; sin trabajo activo, pero `DECISION_007` (65% de barra) es suya cuando se abra ese frente.
- **Mis propios desvíos** (asignarle relevamiento documental a Orbit, que es Build/Deploy): fue correcto por acceso y contexto. Queda **registrado como excepción consciente**, no como precedente.

---

# ✅ CIERRE — todo resuelto (2026-07-19)

Esta propuesta queda **cerrada**. Nada pendiente.

| Punto | Resolución |
|---|---|
| A.1 Contratos Cybelec / Postprocesador | ✅ **`DECISION_013`** |
| A.2 Frontera Orbit ↔ Forge | ✅ **`DECISION_014`** |
| A.3 Hueco MES | ✅ Lechu (su contrato; sigue en pausa) |
| A.3 Hueco infra | ✅ Orbit (`DECISION_014`) |
| A.3 Hueco OCR | ✅ **`DECISION_016`** — Constantino lo confirmó como **parte clave**; ya no es hueco |
| A.4 Carga de Punto | ✅ Congelamiento vigente (`DECISION_015` §6) |
| B.1 Cálculo de recursos | ✅ **`DECISION_015`** — Constantino **delegó en Nova**: rol propio, con traspaso al cerrar el simulador |
| B.2 ¿OCR sigue en el norte? | ✅ Respondido: **sí, es clave** → `DECISION_016` |
| Nido | ✅ **`DECISION_012`** — no estaba vaciado, estaba mal descrito |

**Corrección a mi propio criterio:** yo había propuesto dejar el OCR **sin dueño** por no haber frente activo. Constantino lo corrigió: es parte clave. Me equivoqué en el peso, no en el timing — el rol se fija ahora, la activación sigue siendo diferida.

**Mapa de roles resultante:** Nova (PM) · Atlas (backend) · Vega (frontend/UX) · Punto (CAD/geometría **+ cálculo, temporal**) · Gemu (corte lineal) · Lechu (MES) · **Nido (compilador de lote)** · Tango (CRM/Tango) · Orbit (build/deploy **+ infra SO**) · Forge (Frappe/ERPNext) · **Cybelec (plegado)** · **Postprocesador (G-code)** · **OCR (facturas de proveedores)** · *Cálculo de Recursos (pendiente de creación)*.
