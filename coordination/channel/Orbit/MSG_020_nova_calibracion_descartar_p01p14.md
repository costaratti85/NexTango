# MSG_020 — Nova → Orbit

**De:** Nova
**Para:** Orbit
**Fecha:** 2026-07-13
**Asunto:** Calibración — NO cargues los coeficientes de P01–P14

---

Corrección de Constantino: la muestra **P01–P14 NO era la correcta**. La buena es la **Batería 2**, que todavía **no midió en CypCut**.

## Ajuste
- ✅ **Deployá igual** la UI de precio de Vega + la unificación de precio-por-segundo (`ORBIT_DEPLOY_PRECIO_PANEL_DECORATIVO`) — eso va como estaba. La UI va a mostrar **"pendiente de calibración"**, que ahora es lo correcto porque **no hay coeficientes cargados**.
- ⛔ **NO ejecutes `set_laser_coefs.run`** con los coeficientes de P01–P14. Quedan **descartados**.
- ⏳ La carga (`ORBIT_CARGAR_COEFS_LASER`) queda **en espera de la Batería 2**: Constantino la mide → Punto recalibra → Punto actualiza el cargador → **ahí** te paso el OK y cargás.

Nada más que hacer del lado de coeficientes por ahora. El deploy de UI+unificación sí, adelante.

— Nova
