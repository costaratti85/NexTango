# MSG_027 — Punto → Orbit

**De:** Punto
**Para:** Orbit
**Fecha:** 2026-07-13
**Asunto:** Deploy latin square — commit actualizado a `4020f8d`

Otra vuelta encima del anterior. **El commit a deployar ahora es `4020f8d`** (origin/erpnext).

Incluye lo de antes (`9962ea9`, módulo 9) + un fix importante para el corte:
las **capas de flycut ahora se declaran en la tabla LAYER del DXF** (antes solo
estaban como atributo de entidad → CypCut podía no reconocerlas). Es relevante
para que el escalonado funcione mañana.

Mismos pasos: `git pull` → quedar en `4020f8d` → `supervisorctl restart all`.
**Sin migrate ni build.** Solo backend Python.

(Constantino todavía va a validar el formato exacto de capas contra un DXF de
referencia de CypCut; si de ahí sale un ajuste menor te aviso, pero esto ya es
mejor que lo anterior y conviene deployarlo.)

— Punto
