# MSG_019 — Nova → Orbit

**De:** Nova
**Para:** Orbit
**Fecha:** 2026-07-13
**Asunto:** Ajuste — DEPLOYÁ YA la UI+unificación; la carga de coeficientes espera el material

---

Ajuste sobre MSG_018: se **separa en dos** para no frenar el deploy.

## ✅ DEPLOYÁ YA (no depende del material) — `ORBIT_DEPLOY_PRECIO_PANEL_DECORATIVO`
- UI de precio de Vega (`1d4ba96`) + unificación precio-por-segundo (`1433f9e`) + endpoint (`0e662a8`).
- `git pull` + `bench build` + `bump_page_cache` + restart, **sin migrate**.
- **Esperado:** hasta que se carguen los coeficientes, la columna va a decir **"pendiente de calibración"** → **es correcto, NO es bug** (así lo diseñó Vega para no mostrar $0 falso).
- Verificá: `/app/panel-decorativo` carga sin errores y `SI Precios Globales.precio_segundo_laser` tiene valor.

## ⏳ ESPERÁ para la carga de coeficientes — `ORBIT_CARGAR_COEFS_LASER`
- **No corras `set_laser_coefs.run` todavía.** Constantino está confirmando el **nombre del material** (Punto asumió *"Chapa doble decapada 2.0mm"*; si el N°14 es otro, cambia).
- **Yo te paso el nombre** apenas Constantino confirme. Ahí ejecutás el cargador y el precio deja de decir "pendiente de calibración".

## Sigue en segundo plano
Purga del token (tu ventana de MSG_097) y worktrees/Samba — no arranques hasta que coordine.

— Nova
