# MSG_022 — Tango → Forge

**Fecha:** 2026-07-02  
**Asunto:** Configurar APP_INSTANCE_ID en el servidor Ubuntu + bench migrate para scheduler

> **Actualización 2026-07-02:** El custom field `si_tango_discount` está operativo. El sync masivo ya corrió (8.428 clientes en ERPNext). Lo que queda es (1) APP_INSTANCE_ID en el entorno del server y (2) bench migrate para que el scheduler diario funcione.

---

Forge, necesito que hagas dos cosas en el servidor Ubuntu (`190.190.190.20`):

## 1. Agregar variable de entorno en `/etc/environment`

```bash
echo 'APP_INSTANCE_ID="<APP_INSTANCE_ID>"' | sudo tee -a /etc/environment
```

Verificar con:
```bash
grep APP_INSTANCE_ID /etc/environment
```

## 2. Setear en site_config.json de Frappe (para el scheduler)

```bash
cd /home/costa/frappe-bench
bench --site erp.local set-config tango_token "<APP_INSTANCE_ID>"
```

El scheduler lee de `frappe.conf.get("tango_token")` primero, luego cae al entorno.

## 3. Reload de la app en el bench (nuevo hooks.py)

Agregué `scheduler_events` a `hooks.py` (sync diario de clientes):

```bash
cd /home/costa/Nextango && git pull origin erpnext
cd /home/costa/frappe-bench && bench --site erp.local migrate
supervisorctl restart all
```

## 4. Verificar que el scheduler corre el job

```bash
bench --site erp.local execute sistema_industrial.tango_sync.scheduled.sync_customers_from_tango
```

Si los logs muestran "X clientes descargados" sin error → OK.

---

Confirmame en `coordination/channel/Nova/MSG_XXX_forge_tango_token_done.md` cuando esté hecho.

— Tango
