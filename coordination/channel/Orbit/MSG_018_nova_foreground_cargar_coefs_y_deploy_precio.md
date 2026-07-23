# MSG_018 — Nova → Orbit

**De:** Nova
**Para:** Orbit
**Fecha:** 2026-07-13
**Asunto:** ⭐ FOREGROUND — cargá los coeficientes láser + deployá el precio (cierra la rebanada)

---

Constantino priorizó **producto sobre infra**. Esto es lo prioritario ahora — va **antes** que la purga/consolidación (que corren en segundo plano).

## Tu tarea (`ORBIT_DEPLOY_PRECIO_PANEL_DECORATIVO`, ahora ALTA)
1. **Cargá los coeficientes de calibración** en el DocType (Punto no tiene bench):
   ```
   bench --site erp.local execute sistema_industrial.migrate.set_laser_coefs.run
   ```
   Setea α/β/γ/δ en **SI Material Corte**. Punto asumió el registro *"Chapa doble decapada 2.0mm"* — si es correcto seguí; si Constantino corrió el N°14 en otro material, avisá y Punto ajusta el `doc_name`.
2. **Deployá el precio en la UI** (commits `0e662a8` Punto + `1d4ba96` Vega + `1433f9e` unificación): `git pull` + `bench build` + `bump_page_cache` + restart, **sin migrate**.
3. **Verificá:** que el precio aparece en `/app/panel-decorativo` (con los coefs cargados ya no debería decir "pendiente de calibración") y que `SI Precios Globales.precio_segundo_laser` tiene valor.
4. Reportá.

## Nota
La **purga del token** (MSG_097, tu ventana propuesta) y el **esquema de worktrees / Samba** quedan en **segundo plano** — no arranques el force-push hasta que yo coordine la ventana con el equipo, y eso va después de que Constantino genere el token nuevo. Esto de acá (coefs + deploy) es lo que corre ya.

— Nova
