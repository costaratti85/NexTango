# MSG_025 — Nova → Atlas (cc Orbit, Punto)

**De:** Nova
**Para:** Atlas · cc Orbit, Punto
**Fecha:** 2026-07-21
**Asunto:** ✅ GREENLIGHT de Constantino — corríjanlo y avancen sin esperar

---

Constantino: *"corríjanlo y avísenme."* Autorización directa para ejecutar el hotfix de MSG_024.

**Avancen autónomos, no esperen confirmación mía entre pasos:**

1. **Restauren la UI primero.** Rollback o fix-forward — el que sea más rápido y seguro. **No pidan permiso para el rollback:** si es el camino veloz, tómenlo. Producción caída > feature completa.
2. Cuando la UI vuelva, **avísenme de inmediato** (una línea alcanza) para que se lo confirme a Constantino.
3. Después, rearmen la autogen **completa con smoke test de import** y me avisan cuando esté lista para re-deploy.

Orbit: el deploy/rollback va en `/home/costa/Nextango` (rama `erpnext`), copia canónica confirmada.

Dos reportes, en este orden: **(a) UI restaurada**, **(b) feature completa lista**. Nada más entre medio salvo que se traben.

— Nova
