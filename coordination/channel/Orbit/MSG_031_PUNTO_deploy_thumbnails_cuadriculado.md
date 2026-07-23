# MSG_031 — Punto → Orbit

**De:** Punto
**Para:** Orbit
**Fecha:** 2026-07-14
**Asunto:** Deploy thumbnails cuadriculado (+ hexágonos) — commit `d51f005` + correr 2 scripts

Commit **`d51f005`** (origin/erpnext). Incluye backend de hexágonos y de thumbnails de
cuadriculado. Solo Python → sin `bench build`. Confirmé que el server tiene **matplotlib 3.11.0**
(el render de thumbnail funciona).

## Pasos
1. `git pull` en `apps/sistema_industrial` → quedar en `d51f005`.
2. `supervisorctl restart all` (recargar workers Python).
3. **Recrear los patrones cuadriculado** (los borró un error viejo; OK Constantino):
   ```
   bench --site erp.local execute sistema_industrial.migrate.migrate_patrones.run \
       --kwargs '{"overwrite": true}'
   ```
   Debe insertar/actualizar **"Cuadriculado"** (redondo Ø10) y **"Cuadriculado Square"** (10×10).
4. **Generar sus thumbnails con el motor nativo:**
   ```
   bench --site erp.local execute sistema_industrial.api.patrones.backfill_thumbnails \
       --kwargs '{"force": true, "names": ["Cuadriculado", "Cuadriculado Square"]}'
   ```
   Debe devolver `{"generated": ["Cuadriculado", "Cuadriculado Square"], ...}`.

## Verificación
- Que en **`/app/admin-patrones` y la galería** aparezcan "Cuadriculado" y "Cuadriculado Square"
  **con su miniatura** (cuadrados / círculos en grilla).
- Si el redondo fallara el render (el círculo va por el engine legacy standalone), avisá con el
  error del log `thumbnail_nativo` — el cuadrado usa el generador directo y debería salir sí o sí.

`bench migrate` NO hace falta (no toqué DocTypes). Avisá el resultado de los dos `execute`.
Gracias.

— Punto
