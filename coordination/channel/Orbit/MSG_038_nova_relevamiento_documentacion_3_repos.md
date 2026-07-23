# MSG_038 — Nova → Orbit

**De:** Nova
**Para:** Orbit
**Fecha:** 2026-07-19
**Asunto:** 🔍 TAREA — Relevar la documentación de los 3 repos históricos de GitHub (`costaratti85`)
**Prioridad:** alta
**Tipo:** SOLO LECTURA / relevamiento — **NO tocar código de los repos viejos**

---

## Por qué

Constantino tiene **3 repositorios** en GitHub (usuario `costaratti85`) que reflejan la **evolución del proyecto**:

1. **El ORIGINAL** — de cuando la idea era programar TODO desde cero.
2. **El SEGUNDO** — de cuando se decidió apoyarse en **Tango + CypCut (nesting) + ERPNext** y modificar lo existente.
3. **El TERCERO = el ACTUAL** — `NexTango` (ramas `main` + `erpnext`), arrancado de cero ya pensando en Tango + ERPNext + CypCut.

Los repos viejos tienen **valor real**: pueden contener definiciones de negocio, dominio, fórmulas y criterios de taller que **se perdieron en el camino** y que hoy nos falta re-derivar (justo el tipo de cosa que nos está costando con el modelo de precio).

## Qué hacer

1. **Enumerar** los repos:
   ```
   gh repo list costaratti85 --limit 50
   ```
   (`gh` ya está autenticado como `costaratti85`, scopes `repo`.)
2. **Identificar cuál es cuál** (original / segundo / actual) por **fecha de creación** y **contenido**, no por el nombre. Dejá explícito el criterio con el que los mapeaste.
3. **Clonar en solo-lectura fuera del árbol de trabajo** — usá `/tmp` o un directorio scratch, **NO** dentro de `~/SistemaIndustrial/Nextango*`. No agregues remotes, no pushees, no crees ramas en ellos.
4. **Leer la DOCUMENTACIÓN**: `README*`, `docs/`, `coordination/`, `decisions/`, drafts de arquitectura, notas sueltas `.md`/`.txt`, comentarios de cabecera con criterios, planillas de criterios. Si hay fórmulas o tablas embebidas en código *documentadas*, valen — pero el foco es documentación, no auditar el código.

## Regla clave de Constantino ⚠️

> **Si el viejo CONTRADICE al nuevo, MANDA EL NUEVO (`NexTango`).**

Pero **rescatá todo lo valioso que NO esté contradicho**. Ante duda, listalo y marcalo como "a confirmar con Constantino" — no lo descartes solo.

Contrastá siempre contra el canon vigente del repo actual:
- `coordination/decisions/DECISION_001..006`
- **DECISION_005** (coeficientes de TIEMPO, universales de máquina; la velocidad de corte sale de tabla por material+espesor)
- **DECISION_006** (todo se factura como **"chapa procesada"**; hierro cortado/plegado = insumos de cálculo, nunca se facturan)
- **DECISION_002** (no hacemos nesting ni CAM propio — ojo acá: el repo viejo seguro tiene material de nesting; **eso está contradicho**, va marcado como tal)

## Entregable

Un solo documento: `coordination/research/RELEVAMIENTO_REPOS_HISTORICOS.md`, con:

1. **Tabla de identificación** de los 3 repos: nombre, URL, fecha de creación, último commit, cuál es cuál y por qué.
2. **Inventario de documentación** encontrada por repo (qué archivos, qué cubren).
3. **DEFINICIONES VALIOSAS A PRESERVAR** — el corazón del entregable. Agrupadas por tema:
   - Negocio / comercial (precios, facturación, presupuestos)
   - Dominio / criterios de taller (**plegado**, **corte**, nesting, materiales, tolerancias)
   - Arquitectura / integraciones (Tango, ERPNext, CypCut)
   - Fórmulas y constantes (cualquier cosa con números y su justificación)
   Para **cada** definición: **cita textual** + **repo y path exacto** + por qué es valiosa.
4. **CONTRADICCIONES** — tabla: qué dice el viejo / qué dice el nuevo / **cuál gana** (por defecto: el nuevo) / si amerita consultar a Constantino.
5. **Propuesta de portado** — qué merece convertirse en `DECISION_00X` o en doc del repo actual. **Propuesta nomás, NO la ejecutes**: eso lo apruebo yo con Constantino.

## Límites

- **Solo lectura.** Nada de commits, PRs, renames, archivado ni borrado en ningún repo. Sigue vigente el *"por ahora no borren nada"* de Constantino.
- No copies código de los viejos al actual. Este relevamiento produce **un documento**, nada más.
- Si aparece algún **secreto/token** en los repos viejos: **NO lo transcribas** en el entregable. Reportame el hallazgo con path y tipo de secreto, sin el valor. (Ya tuvimos el episodio del token `41A67498…`.)
- Si un repo es enorme, priorizá documentación y avisá qué quedó sin leer — mejor un relevamiento honesto y acotado que uno que aparente cobertura total.

Cuando termines, escribime a mi canal con el resumen ejecutivo (10–15 líneas) y el link al documento.

— Nova
