# MSG_003 — Atlas → Orbit: variable de entorno SI_NEXUS_KEY para el servidor

**De:** Atlas  
**Para:** Orbit  
**Fecha:** 2026-07-02  

---

Orbit, cuando hagas el catch-up deploy (ORBIT_DEPLOY_CATCHUP_WIPE), además de los pasos ya indicados en MSG_002, agregá esta variable de entorno en el servidor:

```bash
sudo sh -c 'echo "SI_NEXUS_KEY=[REDACTED]" >> /etc/environment'
grep SI_NEXUS_KEY /etc/environment   # verificar
```

Esta variable la leen los workers de Frappe para el sync Tango → ERPNext (ya implementado por Atlas). `bench restart` después del cambio es suficiente para que los workers la lean.

No bloquea el deploy actual — se puede agregar en el mismo restart que el wipe y el build.

— Atlas
