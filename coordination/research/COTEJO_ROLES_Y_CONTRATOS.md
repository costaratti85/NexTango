# Cotejo de roles/contratos de agentes vs. asignación real

**Autor:** Orbit (Build/Deploy) · **Fecha:** 2026-07-19
**Tipo:** SOLO LECTURA — diagnóstico. NO propone reasignaciones (eso lo deciden Constantino y Nova).
**Fuentes de contrato:** `Sistema_Industrial_Nextango/coordination/engineers/*.md` (SEGUNDO); `Sistema-Industrial/docs/agents/FORGE_ROLE_CONTRACT.md` (ORIGINAL); `NexTango/docs/00_BRUJULA_DOCUMENT_FUNDACIONAL.md` §6.5 (dueños de módulos, actual).
**Asignación real:** `coordination/dispatch/queue.json` (tareas por agente) + últimos mensajes por canal.

---

## 1. Contratos documentados (cita + path)

| Agente | Rol declarado | Posee | Fuente |
|---|---|---|---|
| **Nova** | PM / System Architecture | "architecture consistency, module boundaries, contract review, **source-of-truth decisions**, multi-agent coordination. **No reemplaza la aprobación de Constantino**." | SEGUNDO `engineers/nova_architecture_pm.md` |
| **Atlas** | Backend/ERPNext | "backend integration boundaries around ERPNext, service orchestration, **adapter design**, permissions, **API-facing contracts**." | SEGUNDO `engineers/atlas_backend_erpnext.md` |
| **Punto** | CAD / Geometry | "CAD, DXF ingestion, **geometry normalization**, geometry validation, CAD→Nesting handoff." | SEGUNDO `engineers/punto_cad_geometry.md` |
| **Nido** | **Nesting** | "**nesting** input preparation, placement strategy, sheet planning, nesting output contracts." | SEGUNDO `engineers/nido_nesting.md` |
| **Gemu** | Linear Cutting | "linear stock planning, **bar/profile optimization**, remnant handling, linear cutting output contracts." | SEGUNDO `engineers/gemu_linear_cutting.md` |
| **Lechu** | MES / Producción | "MES and production execution extensions around ERPNext manufacturing (work orders, job cards)." | SEGUNDO `engineers/lechu_mes_erpnext.md` |
| **Tango** | Tango/Contable | "protected Tango integration, accounting sync, fiscal handoff, invoice sync, **reconciliation**." | SEGUNDO `engineers/tango_accounting_integration.md` |
| **Vega** | UX / Frontend | "UX for industrial layer, ERPNext desk/web extensions, **operator-facing screens**, frontend integration." | SEGUNDO `engineers/vega_erpnext_ux_frontend.md` |
| **Orbit** | DevOps / Runtime | "ERPNext/Frappe **runtime, environments, deployment, backups, workers, CI, validation automation, operational reliability**." | SEGUNDO `engineers/orbit_devops_erpnext_runtime.md` |
| **Forge** | ERP Systems Integration | "**working ERPNext operational model for the ferreteria** business line… make ERPNext usable **sin redefinir la arquitectura**." | ORIGINAL `docs/agents/FORGE_ROLE_CONTRACT.md` |
| **Cybelec** | — | **SIN CONTRATO** (no aparece en ningún repo viejo) | — |
| **Postprocesador / CostADCAM** | — | **SIN CONTRATO** como agente (Brújula regla 6 menciona "postprocesador propio hace G-code", pero como herramienta externa, no como rol) | — |

Brújula §6.5 (actual) confirma la repartición y **separa Orbit=Build de Forge=ERPNext**:
> "Backend Core (Atlas), Production/MES (Lechu), CAD/DXF (Punto/Nido), Corte lineal (Gemu), CRM/Tango (Tango), Frontend/UX (Vega), **Build (Orbit), ERPNext (Forge)**."

---

## 2. Cotejo contra la asignación real (queue.json + canales)

| Agente | Le asignamos hoy (real) | Carga (tareas) | Veredicto |
|---|---|---|---|
| **Nova** | Coordinación/despacho (PM) | 1 propia (despacha todo) | ✅ alineado |
| **Atlas** | RENOMBRAR_APP_INSTANCE_ID, BACKEND_ACTUALIZAR_PATRON (endpoints/API) | 11 | ✅ alineado |
| **Vega** | UI: precio, galería, actualizar-patrón, calibración, navegación teclado | 35 | ✅ alineado |
| **Tango** | Integración Tango, token, sync clientes, SI_TANGO_ID | 9 | ✅ alineado |
| **Gemu** | Corte-barras (ya **entregado**); solo broadcasts recientes | 9 (viejas) | ⚠️ rol vigente, **sin trabajo activo** |
| **Lechu** | `LECHU_MES_RETOMAR` (MES no arrancó); solo broadcasts | 2 | ⚠️ contrato válido, **casi sin uso** |
| **Nido** | `NIDO_COMPILADOR_DXF_BATCH` — **en pausa** hasta cerrar rebanada 1 | 1 | ⚠️ **rol vaciado** + reasignado (ver §3) |
| **Punto** | CAD/geometría **+ flycut + calibración láser (modelado físico de tiempo) + fórmula de precio** | **60** | ⚠️ **desborde** (ver §3) |
| **Orbit** | Deploys, purga token, consolidación infra **+ relevamiento documental** | 34 | ⚠️ mayormente alineado, **1 desvío** (ver §3/§6) |
| **Forge** | version stamp, **Samba shares, env/tokens del server, conectividad** + sync clientes | 18 | ⚠️ **solape con Orbit en infra** (ver §3) |
| **Cybelec** | Plegado CNC standalone (satélite) | 2 | ❓ **sin contrato** |
| **Postprocesador** | Contrato DXF plasma/oxicorte (con Punto) | 1 | ❓ **sin contrato** |

---

## 3. Desalineaciones (clasificadas)

### Rol vaciado por decisión
- **Nido** — contrato = **nesting**; `DECISION_002` ("no nesting, no CAM") lo dejó **sin objeto**. Se le reasignó `NIDO_COMPILADOR_DXF_BATCH` (compilar el DXF por material/espesor que va a CypCut) — que **no es nesting** sino el output que Brújula define. Es un rol **nuevo de facto**, hoy **en pausa**. *(Confirma la hipótesis de Nova.)*

### Rol solapado
- **Forge ↔ Orbit (infra)** — Forge hizo **Samba shares, variables de entorno del server, rotación de token en env, conectividad**. Eso es **infraestructura**, que el contrato de **Orbit** reclama ("environments, backups, operational reliability") y Brújula asigna a **Build (Orbit)**. El contrato de Forge es "modelo operativo ERPNext ferretería", **no infra**. → solape real: Forge se corrió a territorio de Orbit. *(Confirma la hipótesis, con matiz: Forge SÍ tiene contrato, pero la infra que hizo no es la suya.)*

### Rol desbordado
- **Punto** — contrato = **CAD/geometría/DXF**. Hoy además hace **modelado físico del tiempo de corte** (calibración láser, `T=α·cut+β·travel+γ·pierce+δ`, simulador de velocidad de esquina) y la **fórmula de precio** — que es **cálculo/backend**, no CAD. Con **60 tareas** es el más cargado y absorbió el "cálculo de recursos" que ningún rol posee. *(Confirma la hipótesis.)*

### Agente sin contrato (trabaja hoy, nunca tuvo rol)
- **Cybelec** (plegado CNC Cybelec/Estun E21) — nació después de los repos viejos. Sin contrato.
- **Postprocesador / CostADCAM** (G-code plasma/oxicorte) — sin contrato de agente (solo mención de la *herramienta* en Brújula).
- *(Ambos confirman la hipótesis.)*

### Rol vigente sin trabajo
- **Gemu** (linear cutting) — corte-barras entregado; sin tareas nuevas. Contrato válido, ocioso. *(Confirma la hipótesis.)*
- **Lechu** (MES) — MES nunca arrancó (`LECHU_MES_RETOMAR` pendiente). Contrato válido, casi sin uso.

---

## 4. Huecos (territorio que nadie reclama por contrato)

1. **Cálculo de recursos / modelado físico de máquina** (tiempo de corte, fórmula de precio, velocidad) — hoy lo tapa **Punto por desborde**; ningún contrato lo posee. Es el hueco más caro (es justo lo que se está re-derivando).
2. **Infra pura** (red/Samba/OS/entorno del server, fuera del deploy Frappe) — zona gris **Orbit↔Forge**; ningún contrato la nombra explícitamente como suya.
3. **MES / producción por taller / estados por pieza** (flujos centrales de Brújula) — contrato de Lechu existe pero inactivo; nadie lo ejecuta.
4. **OCR proveedores** (flujo de Brújula) — apareció "OCRMeli" en dudas de migración, sin contrato ni canal estable.
5. **Plegado CNC** — lo hace Cybelec sin contrato (hueco cubierto por un satélite no-contratado).

---

## 5. Verificación de las hipótesis de Nova

| Hipótesis | Veredicto |
|---|---|
| Nido = rol vaciado por decisión (nesting → hoy compilador DXF) | ✅ **CONFIRMADA** |
| Cybelec / Postprocesador = sin contrato | ✅ **CONFIRMADA** |
| Punto = desborde (CAD vs modelado físico de tiempo) | ✅ **CONFIRMADA** |
| Forge/Orbit = solape (Forge hizo Samba = infra) | ✅ **CONFIRMADA con matiz** (Forge SÍ tiene contrato — ERPNext integration — pero la infra que hizo no es de su contrato; tira a Orbit) |
| Gemu = rol vigente sin trabajo | ✅ **CONFIRMADA** |

---

## 6. Mis propios desvíos y los de Nova (auto-inclusión)

- **Orbit (yo)** — contrato = **Build/Deploy/runtime/CI**. Fuera de contrato: **relevamiento documental de los 3 repos** (MSG_038/041) y **este cotejo de roles**. Lo hago porque tengo `gh` autenticado y acceso a los repos, no porque sea Build/Deploy. → **desvío real**, marcado. (Otras tareas mías — purga de token/git, consolidación infra, diagnóstico de bugs en producción — sí caen en "runtime/operational reliability".)
- **Nova** — contrato = **coordinación/arquitectura**, "no reemplaza a Constantino". Desvío: **me asignó a mí (Build) trabajo de relevamiento/analista documental**, fuera de mi rol — decisión de coordinación pragmática (usar quien tiene el acceso), pero es asignación fuera-de-contrato. También actúa a veces como *analista de negocio* (consolidando definiciones), más allá de "coordinar".

---

## 7. Cobertura / qué quedó sin leer

- **Leído a fondo:** los 10 `engineers/*.md` (SEGUNDO), `FORGE_ROLE_CONTRACT.md` (ORIGINAL), Brújula §6.5, `queue.json` completo por agente, últimos mensajes de canales.
- **No leído en detalle:** `PROJECT_BOARD.md`, `DECISION_LOG` de ownership fino, y la gobernanza autónoma (`AUTONOMOUS_*`, `SAFE_*_RULES`, `orchestration/`) más allá de la parte de ownership — alto volumen, y los roles ya quedaron claros con los `engineers/`. El ORIGINAL **no tiene** `coordination/engineers/` (sus roles viven en `docs/agents/` y en READMEs por módulo). Si Nova quiere el detalle de límites "qué NO le corresponde" por agente (varios `engineers/` tienen sección "Must NOT"), hago una 3ª pasada centrada en esas secciones.

---

## Resumen ejecutivo
Los 10 contratos formales viven en `engineers/` (2º repo) + Forge en `docs/agents/` (1º). **Alineados:** Nova, Atlas, Vega, Tango. **Desalineados:** **Nido** (nesting vaciado por DECISION_002 → compilador DXF, en pausa), **Punto** (desborde CAD→modelado de tiempo/precio, 60 tareas), **Forge↔Orbit** (solape en infra: Samba/env es de Orbit por contrato), **Gemu** y **Lechu** (roles vigentes ociosos). **Sin contrato:** Cybelec, Postprocesador (satélites nuevos). **Huecos:** cálculo de recursos/física de máquina (lo tapa Punto), infra pura (zona gris Orbit/Forge), MES, OCR. **Mis desvíos:** relevamiento + este cotejo (fuera de Build). **Las 5 hipótesis de Nova: todas confirmadas** (Forge con matiz). No propongo reasignaciones — es diagnóstico.
