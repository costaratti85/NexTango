# DECISION_004 — Programas standalone van a `Programas_hechos/` en git

**Fecha:** 2026-07-13
**Autor:** Constantino (registrada por Nova)
**Estado:** Vigente — norma del equipo

---

## Norma
Todo **programa standalone / "por afuera" del sistema** que Constantino incorpore (ej. **CostADCAM**: `cam_core_v9.py`, `nesting_coedge.py`, `exporters/gcode_exporter.py`, etc.) se versiona en **`Programas_hechos/` en git (rama `main`)**, respaldado, siguiendo el flujo estándar **Mint → GitHub → server pull**.

## Qué SÍ va a git (`Programas_hechos/`, rama main)
- El **código fuente** de los programas standalone (`.py`, scripts, config de texto).

## Qué NO va a git
- El **`.exe` compilado** (binario pesado).
- Los **archivos de datos** (DXF, planillas, salidas, etc.).
- → Todo esto va al **share de Samba** (`/home/costa/compartida/...`), no a git.

## Por qué
- El código queda **versionado y respaldado** (historia, diff, recuperación) — evita perder trabajo como pasó en la migración (CostADCAM, VBA, OCR quedaron solo en la Windows).
- Los binarios/datos pesados **no inflan el repo** ni rompen el flujo git; se comparten por Samba, que es para archivos no-código.

## Alcance
Aplica a los proyectos satélite: **Postprocesador** (CostADCAM), **PedidoExcel** (si se porta a Python), **OCR-MELI**, y cualquier standalone futuro.

Relacionado: `coordination/MIGRACION_CARPETAS_FALTANTES.md`, `INFRA_PROPUESTA_CARPETAS_ACCESO_FINAL` (share Samba).
