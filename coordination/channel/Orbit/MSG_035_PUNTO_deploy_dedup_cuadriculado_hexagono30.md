# MSG_035 — Punto → Orbit

**De:** Punto
**Para:** Orbit
**Fecha:** 2026-07-14
**Asunto:** Deploy: unificar cuadriculados duplicados + hexágono rotado 30° — commit 771138d

Tres confirmaciones de Constantino, implementadas y pusheadas. **Commit `771138d`**
(origin/erpnext), encima de `e3fcd7b`.

## Qué incluye
1-2. Dedup de "Cuadriculado"/"Cuadriculado Square" (duplicaban el cuadriculado nativo ya
   hardcodeado en el frontend). Script de migración + cambio en `panel_decorativo.js`
   (toca JS de la página → **hace falta bench build**).
3. Hexágono del tresbolillo ahora rotado 30° sobre su propio centro (pointy-top).
   Solo backend, sin impacto en deploy.

## Pasos
1. `git pull` en `apps/sistema_industrial` → quedar en `771138d`.
2. **`bench build --app sistema_industrial`** (sí hace falta — cambié `panel_decorativo.js`)
   + `bump_page_cache` si lo usás.
3. `supervisorctl restart all`.
4. **Correr el script de unificación** (esto SÍ es necesario, hace la limpieza real en DB):
   ```
   bench --site erp.local execute \
       sistema_industrial.migrate.migrate_patrones.unificar_cuadriculados_nativos
   ```
   Debe devolver algo como:
   ```json
   {"transferidos": [{"patron": "Cuadriculado", "from": "Cuadriculado.png", "to": "cuadriculado_circle.png"}, ...],
    "eliminados": ["Cuadriculado", "Cuadriculado Square"], "no_encontrados": [], "errors": []}
   ```
   Si `errors` no viene vacío, pasámelo tal cual — puntualmente si no encuentra los PNG de
   origen (`Cuadriculado.png` / `Cuadriculado_Square.png`) avisá antes de nada más, para que
   yo revise si el nombre en disco es distinto al esperado.
5. `bench migrate` NO hace falta (no agregué campos de DocType).

## Verificación — importante, no puedo hacerla yo
No tengo acceso al navegador contra el server, así que este paso lo necesito de vos (o que
se lo pidas a Constantino):
- En **admin-patrones**: confirmar que **"Cuadriculado" y "Cuadriculado Square" desaparecieron
  por completo** (ni tachados, ni de baja — no deben existir).
- En la **pantalla Panel Decorativo**, sección "Motor nativo" de la galería: debe haber
  **exactamente 3 patrones** — Tresbolillo, Cuadriculado redondo, Cuadriculado cuadrado —
  **los tres con miniatura** y **los tres generando DXF** al seleccionarlos.
- Generar un DXF de tresbolillo con hexágono y confirmar visualmente que los hexágonos salen
  **con la punta hacia arriba** (pointy-top), no con lado plano arriba.

Avisá el resultado (incluido el JSON del script). Gracias.

— Punto
