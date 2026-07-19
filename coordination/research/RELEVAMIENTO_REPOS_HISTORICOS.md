# Relevamiento de los repositorios históricos (`costaratti85`)

**Autor:** Orbit (Build/Deploy) · **Fecha:** 2026-07-19 (v2, ampliado con Brújula + Nova)
**Tipo:** SOLO LECTURA — relevamiento documental. Cero commits/PRs/cambios en ningún repo. Nada de código copiado.
**Regla aplicada:** si el viejo contradice al nuevo, **manda `NexTango`**. Lo no contradicho se rescata; lo dudoso va como "a confirmar con Constantino".
**Secretos:** ✅ **Ninguno hallado** (barrido GUID/api_key/api_secret/password/token/PRIVATE KEY en `.py/.md/.json/.env/.txt` de ambos repos viejos → sin coincidencias).

> **Objetivo (Constantino):** que Nova quede al tanto de TODA la documentación de los 3 repos, con foco especial en **Brújula** y **Nova**.

---

## 0. Hallazgo clave sobre "Brújula" (leer primero)

**Brújula NO existe en los 2 repos viejos.** Búsqueda exhaustiva de `brújula`/`brujula`/`compass` en **working tree + toda la historia git + todas las ramas** de ambos → **0 coincidencias**. El equipo de esos repos era: **Nova** (PM/Arquitectura), Atlas (Backend), Lechu (MES), Punto (CAD), Nido (Nesting), Gemu (Corte lineal). No hay "Brújula" ahí.

**Brújula vive en el repo ACTUAL (`NexTango`)** como el **documento fundacional**:
- `docs/00_BRUJULA_DOCUMENT_FUNDACIONAL.md` — *"el norte completo del proyecto a largo plazo… Ningún agente puede contradecirlo."*
- `docs/00_BRUJU_MESSAGE_TO_TEAM.md` — mensaje de Bruju al equipo.
- `docs/00_PROJECT_NORTH_STAR.md` — lo declara "documento de referencia vinculante".

Brújula es *"la conversación original **antes del equipo de agentes**"* (cita del propio doc) — es decir, la voz fundacional de Constantino/el proyecto, previa a los repos-de-agentes. Por eso Constantino la marca como lo más importante: **es la fuente del canon**. Le doy su sección completa abajo (§2).

---

## 1. Identificación de los 3 repos

| Rol | Repo | URL | Creado (GitHub) | **1er commit** | Últ. commit | Commits |
|---|---|---|---|---|---|---|
| **ORIGINAL** | `Sistema-Industrial` | github.com/costaratti85/Sistema-Industrial | 2026-06-09 | **2026-05-13** | 2026-06-09 | 87 |
| **SEGUNDO** | `Sistema_Industrial_Nextango` | github.com/costaratti85/Sistema_Industrial_Nextango | 2026-06-06 | **2026-06-05** | 2026-06-05 | 1 |
| **ACTUAL** | `NexTango` (main+erpnext) | github.com/costaratti85/NexTango | 2026-07-19 | (jul) | — | canónico |

**Criterio (1er commit + contenido, NO nombre ni fecha-de-creación):** la fecha de creación en GitHub engaña (`Sistema-Industrial` figura "creado 06-09" pero su **primer commit es 13-mayo** → es el más viejo por trabajo real).
- **ORIGINAL** = `Sistema-Industrial`: 13-mayo, 87 commits, "Industrial ERP + CAD/CAM + **Nesting** + MES", ramas `codex/*` de nesting/CAM/DXF — el "todo desde cero".
- **SEGUNDO** = `Sistema_Industrial_Nextango`: 1 commit (snapshot). README = *"local architecture **fork of the original SistemaIndustrial** repository … replacing the from-scratch ERP plan with an ERPNext-centered architecture"* — el pivote formal a ERPNext/Tango.
- **ACTUAL** = `NexTango`.

---

## 2. ⭐ BRÚJULA — documento fundacional (en `NexTango`, no en los viejos)

Fuente: `NexTango/docs/00_BRUJULA_DOCUMENT_FUNDACIONAL.md`, `00_BRUJU_MESSAGE_TO_TEAM.md`, `00_PROJECT_NORTH_STAR.md`.
Es **la base de todo el canon** (las DECISIONs derivan de acá). Definiciones textuales:

### 2.1 Reglas de negocio inamovibles (13) — `00_BRUJULA…`
> "1. ERPNext es columna operativa — Sistema Industrial vive como app Frappe sobre ERPNext. 2. Tango es dueño fiscal/contable — no reemplazar. 3. Excel se respeta como pricing humano. 4. Tango es maestro de precios finales — ERPNext sincroniza copia. 5. CypCut hace nesting — no reimplementar. 6. El postprocesador propio hace G-code — no reimplementar. 7. La tecnología se adapta a la operación, no al revés. 8. El sistema sugiere, el humano decide, el sistema audita. 9. Toda acción importante debe ser trazable (quién, cuándo, qué, desde qué rol). 10. No duplicar lógica entre módulos. 11. El estado por pieza es central. 12. Producción se organiza por lógica de taller (material, espesor, máquina, matriz, prioridad). 13. Cliente externo nunca ve datos ajenos."

### 2.2 Reglas/fórmulas concretas de dominio (**lo que se buscaba**)
- **Corte lineal (regla comercial):** > "si última barra supera ~65% del largo estándar, sugerir cobrar barra entera."
- **DXF de lote:** > "ordenado, **300mm entre piezas, 500mm entre filas de espesor**, etiquetas con espesor y cantidad."
- **Decisión de proceso:** > "rectángulo sin perforaciones → guillotina; espesor alto → oxicorte; general → láser/plasma."
- **Cálculos automáticos requeridos:** > "superficie de chapa, peso, perímetro de corte, metros de láser, cantidad de contornos, pliegues, tiempo estimado, barras, metros lineales, desperdicio, cortes."

### 2.3 Flujos completos definidos (11)
comercial · **panel decorativo** (medidas→reglas patrón: margen, offset X/Y, sin-cortar-centrado / cortar-en-borde → geometría → cálculo → cotización → DXF) · piezas paramétricas · biblioteca de cliente · corte lineal · lote de corte por espesor · guillotina · **plegado** ("plegador filtra por matriz/punzón/espesor, registra avance parcial/completo") · estados por pieza (14: *pedida→cotizada→aprobada→en lote→cortada parcial/completa→pendiente plegado→plegada parcial/completa→observada→lista→entregada*) · producción por taller (rol activo) · OCR proveedores.

### 2.4 Decisiones de diseño fundamentales
> "1. **Pedido ≠ Lote de corte** — el pedido pertenece a un cliente, el lote pertenece a producción y mezcla piezas de varios pedidos. 2. **Recurso industrial como unidad económica** — el sistema vende chapa, corte, plegado, metro lineal, tiempo de máquina. 3. Roles dinámicos. 4. Rebanadas finas de punta a punta. 5. Módulos con dueños (Atlas/Lechu/Punto/Nido/Gemu/Tango/Vega/Orbit/Forge)."

### 2.5 Mensaje al equipo (`00_BRUJU…`) — el "por qué"
> "Sistema Industrial debe ser una herramienta que ordene la fábrica sin violentarla. Ese es el norte." · "No reinventar lo que ya está resuelto… construir el puente inteligente entre pedido, cálculo industrial, DXF, producción, trazabilidad y facturación."

**Valor:** Brújula es la fuente primaria de negocio+dominio+reglas concretas. Ya está en el actual (no hay que portarla), pero **conviene que Nova la tenga como lectura obligatoria** — de acá salen DECISION_001/002/003/006 y varias reglas de taller aún no formalizadas (el 65% de barra, los espaciados de lote, la matriz de proceso).

---

## 3. ⭐ NOVA — sus contribuciones en los repos viejos

**Rol** (`SEGUNDO/coordination/engineers/nova_architecture_pm.md`): *"Nova ChatGPT — Project Management / System Architecture. Own architecture consistency, module boundaries, contract review, **source-of-truth decisions**, multi-agent coordination. **Nova does not replace Constantino approval for strategic decisions.**"* Es la **misma Nova coordinadora de hoy** (continuidad del rol PM/arquitectura). 80 menciones en ambos repos.

### 3.1 DECISION_LOG (decisiones de proceso que fijó Nova) — `ORIGINAL/coordination/DECISION_LOG.md`
> "**GitHub becomes official source of truth** — Todo el proyecto usará GitHub como fuente oficial de documentación, arquitectura, workflow y versionado." · "**Workflow Fase 1 approved** — revisión humana; **sin merges automáticos**; Issues oficiales; **PRs obligatorios**; ownerships definidos; labels oficiales."

### 3.2 Source of Truth Matrix (el aporte más valioso de Nova) — `modules/shared/contracts/erpnext_tango/SOURCE_OF_TRUTH_MATRIX.md`
Define **qué sistema es dueño de cada concepto** (frontera ERPNext/Tango en detalle):
> "Operational customer, Lead/opportunity, **Quotation/presupuesto**, Sales order/pedido, Item master, BOM, Work order, **Operational stock** → **ERPNext**. **Official invoice, Accounting entry, Tax-sensitive behavior** → **Tango** (requires Constantino approval). CAD file, Normalized geometry → SistemaIndustrial CAD."
> Regla de conflicto: "If any document conflicts with this matrix, the engineer must **stop and produce a decision pack**." · Cambiarla requiere "**Nova review + Constantino approval**."
- ⚠️ La matrix aún lista "**Nesting plan → SistemaIndustrial Nesting**" y "**CAM output/GCode → SistemaIndustrial CAM**" como propios → **contradicho** (ver §6).

### 3.3 Sync Events ERPNext↔Tango — `.../SYNC_EVENTS.md`
Nova como *architecture reviewer*; eventos borrador `erpnext.customer.mapping_requested / mapping_validated`, ownership Tango (integración) + Atlas (adapter).

**Valor:** la **Source of Truth Matrix** es lo más portable de Nova — es una definición explícita y ordenada de la frontera ERPNext/Tango que hoy vive dispersa. Candidata a doc de referencia (§7), quitando las filas de nesting/CAM.

---

## 4. Inventario de documentación (ordenado, para absorber)

Ambos repos ≈ **arquitectura + gobernanza de agentes**. Distribución por carpeta:

**ORIGINAL (`Sistema-Industrial`, 142 `.md`):**
- `modules/shared/` (36) — **contratos**: `erpnext_tango/{SOURCE_OF_TRUTH_MATRIX, SYNC_EVENTS, CONTRACT_INDEX}`, `auth/`, `events/EVENT_BUS_STRATEGY`, `inventory/`, `erpnext/{STOCK_FLOW, API_ADAPTER_STRATEGY}`.
- `modules/{crm_tango, cad, mes, devops, backend, nesting, linear_cutting, frontend}/` — READMEs + arquitecturas draft por módulo.
- `docs/` — ARCHITECTURE_MASTER/CURRENT, ROADMAP, TANGO_INTEGRATION_DECISIONS, FRAPPE_APP_STRATEGY, CAD_NESTING_CAM_CONTRACT_DRAFT, DXF_ADAPTER_EVALUATION, MES_ARCHITECTURE.
- `coordination/` — CAD_DECISIONS, DECISION_LOG, CHANGELOG_GLOBAL, PROJECT_BOARD, QUESTIONS_INBOX, NIDO_*_REVIEW.
- `tasks/`, `.github/ISSUE_TEMPLATE/`, `tools/validation/`.

**SEGUNDO (`Sistema_Industrial_Nextango`, 150 `.md`):** mismo esqueleto (más denso en `modules/shared/` = 54) + `coordination/engineers/` (10: nova/atlas/lechu/punto/nido/gemu…) + `docs/ERPNext_TANGO_PIVOT.md`, `orchestration/` (N8N autónomo), `tasks/` de gobernanza autónoma.

**No leído en detalle (aviso honesto):** de ~292 `.md`, leí Brújula (actual), Nova, identificación, arquitectura, decisiones y barrido temático. **Quedó sin leer a fondo:** la mayoría de `modules/shared/contracts/*` DTO por-DTO, los `NIDO_*_REVIEW`/`CONTOUR_DTO`, gobernanza autónoma (AUTONOMOUS_*, SAFE_*_RULES, N8N, orchestration/) e ISSUE/PR templates — **alto volumen, bajo valor** para negocio/dominio. Si Nova quiere absorción total de un área puntual (p.ej. todos los contratos Tango), hago 2ª pasada dirigida.

---

## 5. Otras definiciones valiosas (fuera de Brújula/Nova)

- **Tolerancias CAD** — `ORIGINAL/coordination/CAD_DECISIONS.md`: > "snap_tolerance=0.01mm · min_segment_length=0.05mm · max_gap_length=0.10mm · geometry_epsilon=0.001mm" + "outer contours=CCW · holes=CW". *Umbrales geométricos concretos; hoy no hay doc equivalente en NexTango.*
- **Aislar `ezdxf` tras adapter** — mismo archivo: "ezdxf solo detrás de `modules/cad/dxf/adapters/ezdxf_adapter.py`; no other module may depend on ezdxf." *(contradice el uso directo actual; ver §6).*
- **Frontera app/ERPNext** — `FRAPPE_APP_STRATEGY.md`: "ERPNext owns quotations, orders, users, roles, stock; SistemaIndustrial adds presets, resource calculations, cutting batches, Tango sync, OCR, pricing sync." *(confirmatorio de DECISION_001).*

---

## 6. Contradicciones (manda `NexTango`)

| Tema | Viejo dice | Nuevo dice | Gana | ¿Consultar? |
|---|---|---|---|---|
| **Nesting/CAM propio** | ORIGINAL/SEGUNDO: `modules/nesting`, `modules/cam`, rol Nido, y la **Source of Truth Matrix de Nova** lista "Nesting/CAM output" como propios | `DECISION_002` + Brújula reglas 5/6: CypCut nesting y postprocesador G-code son **externos, no reimplementar** | **NUEVO** | No — decidido |
| **ERP desde cero** | ORIGINAL: "Industrial ERP platform" from-scratch | `DECISION_001` + Brújula regla 1: app Frappe sobre ERPNext | **NUEVO** | No |
| **`ezdxf` solo tras adapter** | CAD_DECISIONS: prohíbe depender de ezdxf directo | NexTango usa ezdxf directo en el motor/thumbnails | **NUEVO** (de hecho) | ⚠️ Menor — ¿re-adoptar el aislamiento como buena práctica? |

---

## 7. Propuesta de portado (NO ejecutada — la aprueban Constantino + Nova)

1. **Brújula ya está en el actual** → no portar; **sí volverla lectura obligatoria de Nova/agentes** y **formalizar sus reglas de taller aún no-DECISION**: el "**65% de barra → cobrar entera**" (corte lineal), los **espaciados de lote (300/500mm)** y la **matriz de decisión de proceso** (guillotina/oxicorte/láser). Candidatos a `DECISION_007+`.
2. **Source of Truth Matrix de Nova** → candidata a doc de referencia en NexTango (frontera ERPNext/Tango explícita), **quitando las filas de nesting/CAM**. *A confirmar.*
3. **Tolerancias CAD + orientación de contornos** → doc de referencia geométrica / `DECISION_00X`. *A confirmar vigencia con el motor actual.*
4. **Aislar `ezdxf` tras adapter** → a confirmar (buena práctica vs. uso directo actual). No urgente.
5. **Nesting/CAM/ERP-desde-cero** → **NO portar** (contradicho).

---

## Resumen ejecutivo

**Brújula** no está en los repos viejos: es el **documento fundacional de `NexTango`** (`docs/00_BRUJULA_*`), la voz original de Constantino y **fuente de todo el canon** — con reglas de dominio concretas que aún no son DECISION (65% de barra, espaciados de lote 300/500mm, matriz de proceso, 14 estados por pieza). **Nova** en los viejos era la PM/arquitecta; su aporte más rescatable es la **Source of Truth Matrix** (frontera ERPNext/Tango). Los dos repos viejos son arquitectura/gobernanza de agentes (CAD/nesting/CAM); lo concreto rescatable son tolerancias CAD; el resto es confirmatorio (ERPNext/Tango/Excel) o **contradicho** (nesting/CAM propio → DECISION_002 gana). **No hay fórmulas de precio** en los viejos — el modelo de precio no vive ahí. Sin secretos. ~292 docs viejos: leí lo de valor + Brújula/Nova; avisado lo omitido (contratos DTO / gobernanza autónoma).
