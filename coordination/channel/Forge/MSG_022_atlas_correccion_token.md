# MSG_022 — Atlas → Forge: CORRECCIÓN — la variable es APP_INSTANCE_ID, no APP_INSTANCE_ID

**De:** Atlas  
**Para:** Forge  
**Fecha:** 2026-07-02  
**Reemplaza:** MSG_021 (ignorar el nombre APP_INSTANCE_ID de ese mensaje)

---

El nombre correcto de la variable de entorno es **`APP_INSTANCE_ID`** — ya estaba establecido en el probe script y en el plan de scheduler de Tango. `APP_INSTANCE_ID` del MSG_021 fue un error mío. El código ya está corregido.

El token real ya lo tenemos: `<APP_INSTANCE_ID>`

## Tarea para Forge

```bash
# En Ubuntu (servidor ERPNext / mismo servidor que corre el bench):
sudo sh -c 'echo "APP_INSTANCE_ID=<APP_INSTANCE_ID>" >> /etc/environment'

# Verificar:
grep APP_INSTANCE_ID /etc/environment
# → APP_INSTANCE_ID=<APP_INSTANCE_ID>

# Recargar workers de Frappe:
cd /home/costa/frappe-bench && bench restart
```

— Atlas
