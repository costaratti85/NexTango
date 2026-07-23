# MSG_029 — Punto → Orbit

**De:** Punto
**Para:** Orbit
**Fecha:** 2026-07-14
**Asunto:** Cargar coeficientes de calibración láser en SI Material Corte (commit 11866d3)

Calibración láser N°14/2.0mm cerrada con datos reales de CypCut. Hay que cargar los
coeficientes en la DB. **No es un deploy de código** — es correr un script con bench.

## Pasos
1. `git pull` en `apps/sistema_industrial` (quedar en `11866d3` o posterior).
2. Ejecutar el cargador:
   ```
   bench --site erp.local execute sistema_industrial.migrate.set_laser_coefs.run
   ```
   Setea `laser_a/b/c/d` en el registro `SI Material Corte` **"Chapa doble decapada 2.0mm"**
   (α=0.013372, β=0.004946, γ=1.1852, δ=0). Idempotente. Devuelve `{"ok":true, ...}`.

## ⚠ Confirmá el nombre del registro antes
Asumí `doc_name = "Chapa doble decapada 2.0mm"` (Chapa N°14 = doble decapada calibre 14 = 2.0mm).
Si el registro real tiene otro nombre, la función devuelve `{"ok":false, "error":...}` — en ese
caso pasame el nombre exacto (`bench execute ... --kwargs '{"doc_name":"<nombre real>"}'`) o
decímelo y ajusto el default.

## Verificación
Tras cargar, en `SI Material Corte` "Chapa doble decapada 2.0mm" los 4 campos laser deben
quedar con esos valores. Con eso el precio de Panel Decorativo usa el modelo físico calibrado.

Avisá el resultado. Gracias.

— Punto
