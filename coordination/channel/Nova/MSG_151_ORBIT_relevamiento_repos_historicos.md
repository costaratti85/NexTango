# MSG_151 — Orbit → Nova

**De:** Orbit (Build/Deploy)
**Para:** Nova
**Fecha:** 2026-07-19
**Asunto:** ✅ Relevamiento de los 3 repos históricos — entregable listo

---

**Documento:** `coordination/research/RELEVAMIENTO_REPOS_HISTORICOS.md`

## Resumen ejecutivo (10-15 líneas)

- **Identificación (por 1er commit + contenido, NO por nombre/fecha-de-creación):**
  - **ORIGINAL** = `Sistema-Industrial` (1er commit **13-mayo**, 87 commits, "ERP+CAD/CAM+Nesting+MES", from-scratch).
  - **SEGUNDO** = `Sistema_Industrial_Nextango` (1 commit, snapshot; README = "fork of the original… replacing from-scratch with ERPNext" = el pivote).
  - **ACTUAL** = `NexTango`.
  - Ojo: la fecha de creación en GitHub engañaba (Sistema-Industrial figura "más nuevo" pero su trabajo empezó en mayo).
- **Naturaleza:** ambos viejos son **arquitectura y gobernanza de agentes** (CAD/nesting/CAM), previos al criterio de taller real.
- **Rescatable concreto:** SOLO las **tolerancias CAD + orientación de contornos** (`Sistema-Industrial/coordination/CAD_DECISIONS.md`: snap 0.01 / min_seg 0.05 / max_gap 0.10 / epsilon 0.001 mm; outer CCW, holes CW). Hoy no hay doc equivalente en NexTango.
- **Confirmatorio (no contradice):** ERPNext backbone + Tango frontera fiscal + Excel pricing — ya es DECISION_001/003.
- **Contradicho (gana NexTango):** todo el **nesting/CAM/G-code propio** de los viejos → `DECISION_002`. También "ERP desde cero" → `DECISION_001`.
- ⚠️ **No hay fórmulas de precio ni de plegado** que rescatar — el "modelo de precio perdido" **no vive en estos repos**.
- **Secretos:** ninguno hallado.
- **Cobertura honesta:** ~292 docs; leí identificación/arquitectura/decisiones + barrido temático. Sin leer en detalle: proceso autónomo (AUTONOMOUS_*, DTOs, PROJECT_BOARD) — bajo valor. 2ª pasada dirigida a pedido.

## Propuesta de portado (NO ejecutada — la aprueban vos + Constantino)
1. Tolerancias CAD + orientación → candidato a `DECISION_007` o doc de referencia (a confirmar vigencia).
2. Aislar `ezdxf` tras adapter → a confirmar (buena práctica pero contradice uso directo actual).
3. Nesting/CAM/precio/plegado → nada que portar.

Todo solo-lectura: cero cambios en cualquier repo, nada de código copiado. Detalle completo (citas + paths + tabla de contradicciones) en el documento.

— Orbit
