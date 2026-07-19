# Relevamiento de los repositorios históricos (`costaratti85`)

**Autor:** Orbit (Build/Deploy) · **Fecha:** 2026-07-19
**Tipo:** SOLO LECTURA — relevamiento documental. Cero commits/PRs/cambios en ningún repo.
**Regla aplicada:** si el viejo contradice al nuevo, **manda `NexTango`**. Lo no contradicho se rescata; lo dudoso va como "a confirmar con Constantino".
**Secretos:** ✅ **Ninguno hallado** (barrido por GUID/api_key/api_secret/password/token/PRIVATE KEY en `.py/.md/.json/.env/.txt` de ambos repos viejos → sin coincidencias).

---

## 1. Identificación de los 3 repos

| Rol | Repo | URL | Creado (GitHub) | **1er commit** | Últ. commit | Commits |
|---|---|---|---|---|---|---|
| **ORIGINAL** | `Sistema-Industrial` | github.com/costaratti85/Sistema-Industrial | 2026-06-09 | **2026-05-13** | 2026-06-09 | 87 |
| **SEGUNDO** | `Sistema_Industrial_Nextango` | github.com/costaratti85/Sistema_Industrial_Nextango | 2026-06-06 | **2026-06-05** | 2026-06-05 | 1 |
| **ACTUAL** | `NexTango` (main+erpnext) | github.com/costaratti85/NexTango | 2026-07-19 | (jul) | — | canónico |

**Criterio de identificación (por 1er commit + contenido, NO por nombre ni fecha de creación del repo):**
- La **fecha de creación del repo en GitHub engaña**: `Sistema-Industrial` figura creado 06-09 (posterior a `Sistema_Industrial_Nextango` 06-06), pero su **primer commit es del 13-mayo** — es el más viejo por trabajo real.
- **ORIGINAL = `Sistema-Industrial`**: primer commit 13-mayo, 87 commits, descripción *"Industrial ERP + CAD/CAM + **Nesting** + MES platform"*, con ramas `codex/*` de nesting/CAM/DXF-adapter. Es el "programar todo desde cero" (CAD/nesting/CAM propios). Hacia su último commit (06-09) el README ya arranca el pivote — evolucionó dentro del mismo repo.
- **SEGUNDO = `Sistema_Industrial_Nextango`**: **1 solo commit** ("Initialize … architecture"), un **snapshot de arquitectura**. Su README se autodefine: *"local architecture **fork of the original SistemaIndustrial** repository … replacing the from-scratch ERP plan with an ERPNext-centered architecture"* (`README.md`). Es el pivote formal a **apoyarse en ERPNext + Tango**, modificando lo existente.
- **ACTUAL = `NexTango`**: el que trabajamos hoy. Canónico.

---

## 2. Inventario de documentación

Ambos repos son, en esencia, **repos de arquitectura y gobernanza de agentes autónomos (codex)** — mucho contrato de módulos y proceso, poco criterio de taller/fórmula concreto.

- **ORIGINAL** (`Sistema-Industrial`): **142 `.md`**. `README.md`, `AGENTS.md`, `docs/` (ARCHITECTURE_MASTER, ARCHITECTURE_CURRENT, ERPNext_TANGO_PIVOT no, ROADMAP, TANGO_INTEGRATION_DECISIONS, CAD_NESTING_CAM_CONTRACT_DRAFT, DXF_ADAPTER_EVALUATION, FRAPPE_APP_STRATEGY, MES_ARCHITECTURE_DRAFT), `coordination/` (CAD_DECISIONS, DECISION_LOG, CHANGELOG_GLOBAL, engineers/{gemu_linear_cutting, nido_nesting, punto_cad_geometry, atlas_backend_erpnext, lechu_mes_erpnext}), `tasks/`, `modules/{cad,linear_cutting,crm_tango,mes,backend,frontend}/`.
- **SEGUNDO** (`Sistema_Industrial_Nextango`): **150 `.md`** (en 1 commit). Mismo esqueleto + `docs/ERPNext_TANGO_PIVOT.md`, `docs/ARCHITECTURE_MASTER.md` ("no longer a full ERP from scratch").

**No leído exhaustivamente (aviso honesto):** de ~292 `.md` totales, prioricé identificación, arquitectura, decisiones y un barrido temático (precio/plegado/tolerancia/nesting/Tango/CypCut). **Quedó sin leer en detalle** el grueso de proceso autónomo (AUTONOMOUS_*, ISSUE_TEMPLATE, PROJECT_BOARD, SAFE_*_RULES, los NIDO_*_REVIEW/CONTOUR_DTO detallados) y los README por-módulo — son gobernanza/contratos DTO, bajo valor para "definiciones de negocio/taller perdidas". Si Constantino quiere, hago una 2ª pasada dirigida a un tema puntual.

---

## 3. Definiciones valiosas a preservar

### Dominio / criterios de taller (CAD-geometría) — **lo más rescatable**
- **Tolerancias CAD aprobadas** — `Sistema-Industrial` · `coordination/CAD_DECISIONS.md`:
  > "snap_tolerance = 0.01 mm · min_segment_length = 0.05 mm · max_gap_length = 0.10 mm · geometry_epsilon = 0.001 mm"
  *Valiosa:* son umbrales geométricos concretos y justificables para limpieza/healing de DXF. Hoy no hay un doc equivalente en `NexTango`.
- **Orientación de contornos** — mismo archivo:
  > "outer contours = CCW · holes = CW"
  *Valiosa:* convención de orientación (útil para el motor de patrones / export DXF).

### Arquitectura / integraciones — **alineado con el canon (confirmatorio)**
- **Backbone** — `Sistema_Industrial_Nextango` · `docs/ERPNext_TANGO_PIVOT.md`:
  > "ERPNext provides standard operational ERP workflows. Tango Gestion provides protected accounting and fiscal workflows. Sistema_Industrial_Nextango provides industrial specialization and integration."
  *Valiosa (no contradice):* es exactamente la línea de `DECISION_001`. Confirma que el pivote a "app sobre ERPNext, Tango como frontera fiscal" ya estaba razonado.
- **Rol de la app** — `Sistema-Industrial` · `docs/FRAPPE_APP_STRATEGY.md`:
  > "ERPNext owns operational flow: quotations, orders, users, roles, stock and warehouses. SistemaIndustrial adds industrial logic: presets, resource calculations, cutting batches, Tango sync, OCR routing and pricing sync."
  *Valiosa:* buena definición de frontera app/ERPNext (alineada con el canon).

### Negocio / comercial
- **Excel como pricing** — implícito en "pricing sync" (FRAPPE_APP_STRATEGY) → **coincide** con `DECISION_003` ("Excel sigue siendo herramienta humana de pricing; Excel → Tango precios maestros → cache"). Confirmatorio, no aporta fórmula nueva.
- ⚠️ **No encontré fórmulas de precio/presupuesto ni de plegado concretas** en ninguno de los dos viejos. Eran repos de arquitectura previos al criterio de taller real (que aportó Constantino ya en `NexTango`). El "modelo de precio perdido" que se buscaba **no está** en estos repos.

### Roles de dominio (referencia, no definiciones)
- `Sistema_Industrial_Nextango` · `coordination/engineers/` define misiones por ingeniero: `gemu_linear_cutting` ("linear stock planning, bar/profile optimization, remnant handling, linear cutting output contracts"), `nido_nesting`, `punto_cad_geometry`. Útil como mapa histórico de responsabilidades; sin fórmulas.

---

## 4. Contradicciones (manda `NexTango`)

| Tema | Viejo dice | Nuevo (`NexTango`) dice | Gana | ¿Consultar a Constantino? |
|---|---|---|---|---|
| **Nesting / CAM** | Módulos propios: `modules/nesting`, `modules/cam`, rol **Nido nesting**, `CAD_TO_NESTING_HANDOFF`, `CAM_HANDOFF`, ContourDTO "for nesting compatibility" | `DECISION_002`: "no implementa nesting, G-code ni CAM … el output son DXF; lo que sigue es de herramientas externas" | **NUEVO** | No — contradicción clara y ya decidida |
| **ERP desde cero** | ORIGINAL arrancó "Industrial ERP … platform" from-scratch (CAD/CAM/MES propios) | `DECISION_001`: app Frappe sobre ERPNext, no ERP-core propio | **NUEVO** | No |
| **CAM / G-code / toolpaths** | `CAD_NESTING_CAM_CONTRACT_DRAFT`, `CAM_HANDOFF_REVIEW` | `DECISION_002`: sin toolpaths ni G-code | **NUEVO** | No |
| **Motor CAD propio con `ezdxf` tras adapter** | `CAD_DECISIONS`: `ezdxf` solo detrás de `modules/cad/dxf/adapters/ezdxf_adapter.py`; "no other module may depend on ezdxf" | `NexTango` usa `ezdxf` directo en el motor de patrones / thumbnails | **NUEVO** (de hecho) | ⚠️ Menor — la *convención de aislar ezdxf* podría ser buena práctica; a confirmar si vale re-adoptarla |

---

## 5. Propuesta de portado (NO ejecutada — la aprueban Constantino y Nova)

1. **Tolerancias CAD y orientación de contornos** → candidatas a un **doc de referencia geométrica** en `NexTango` (o `DECISION_007_TOLERANCIAS_CAD`), citando el origen. Valor: umbrales concretos para healing/validación de DXF que hoy no están documentados. *A confirmar con Constantino que siguen vigentes para el motor actual.*
2. **Frontera app/ERPNext/Tango** (ERPNext_TANGO_PIVOT + FRAPPE_APP_STRATEGY) → **no portar como nueva decisión** (ya cubierto por DECISION_001/003); sí vale **enlazarlos como antecedente histórico** del "por qué" del pivote.
3. **Convención de aislar `ezdxf` tras un adapter** → **a confirmar con Constantino**: es buena práctica de ingeniería pero contradice el uso directo actual; no urgente.
4. **Todo lo de nesting/CAM/G-code** → **NO portar** (contradicho por DECISION_002). Queda como historia.
5. **Fórmulas de precio/plegado** → **no hay nada que portar**: no existen en estos repos. El re-derivado del modelo de precio **no se resuelve** con estos históricos.

---

## Resumen ejecutivo

Los dos repos viejos son **arquitectura y gobernanza de agentes** (CAD/nesting/CAM/MES), previos al criterio de taller real. **ORIGINAL** = `Sistema-Industrial` (from-scratch, 1er commit 13-mayo); **SEGUNDO** = `Sistema_Industrial_Nextango` (fork-pivote a ERPNext, 1 commit). **Lo único concretamente rescatable** son las **tolerancias CAD + orientación de contornos** (CAD_DECISIONS). El resto es o **confirmatorio** del canon (ERPNext/Tango/Excel-pricing) o **contradicho** (nesting/CAM propio → DECISION_002 gana). **No hay fórmulas de precio ni de plegado** que rescatar — el "modelo perdido" no vive acá. Sin secretos. ~292 docs: leí lo de valor y avisé lo omitido (proceso autónomo/DTOs).
