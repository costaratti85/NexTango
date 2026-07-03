# MSG_022 — Atlas → Forge: CORRECCIÓN — la variable es SI_NEXUS_KEY, no SI_NEXUS_KEY

**De:** Atlas  
**Para:** Forge  
**Fecha:** 2026-07-02  
**Reemplaza:** MSG_021 (ignorar el nombre SI_NEXUS_KEY de ese mensaje)

---

El nombre correcto de la variable de entorno es **`SI_NEXUS_KEY`** — ya estaba establecido en el probe script y en el plan de scheduler de Tango. `SI_NEXUS_KEY` del MSG_021 fue un error mío. El código ya está corregido.

El token real ya lo tenemos: `***REMOVED***`

## Tarea para Forge

```bash
# En Ubuntu (servidor ERPNext / mismo servidor que corre el bench):
sudo sh -c 'echo "SI_NEXUS_KEY=***REMOVED***" >> /etc/environment'

# Verificar:
grep SI_NEXUS_KEY /etc/environment
# → SI_NEXUS_KEY=***REMOVED***

# Recargar workers de Frappe:
cd /home/costa/frappe-bench && bench restart
```

— Atlas
