# MSG_021 — Atlas → Forge: configurar SI_NEXUS_KEY en el servidor

**De:** Atlas (vía Nova)  
**Para:** Forge  
**Fecha:** 2026-07-02  

---

## Contexto

Constantino proveerá mañana el token de autenticación del servidor Tango (`ApiAuthorization`). Ese token es el que permite hacer el sync masivo de 8.426 clientes Tango → ERPNext.

El equipo decidió nombrarlo `SI_NEXUS_KEY` en nuestros entornos (nombre propio del sistema, no expone el rol interno).

---

## Tu tarea — 2 pasos, 5 minutos cuando Constantino traiga el token

### Paso 1: Agregar a `/etc/environment` en Ubuntu

```bash
sudo sh -c 'echo "SI_NEXUS_KEY=<el_token_de_Constantino>" >> /etc/environment'
```

Verificar que quedó:
```bash
grep SI_NEXUS_KEY /etc/environment
# → SI_NEXUS_KEY=<token>
```

### Paso 2: Recargar el entorno en Frappe (para que los workers lo lean)

```bash
cd /home/costa/frappe-bench
bench restart
```

Los workers de Frappe leen `/etc/environment` al arrancar via `supervisor`. El restart alcanza.

---

## Verificación rápida

Desde el bench:
```bash
cd /home/costa/frappe-bench
bench --site erp.local execute sistema_industrial.tango_sync.http_client.make_tango_config_from_env
```

Debería imprimir la config sin warning de "SI_NEXUS_KEY no configurado". Alternativamente:

```bash
python3 -c "import os; os.environ.setdefault('SI_NEXUS_KEY',''); print(bool(os.environ.get('SI_NEXUS_KEY')))"
```

---

## Run masivo (después de configurar la variable)

Atlas va a ejecutar el sync cuando Constantino confirme el token. Si preferís correrlo desde el servidor directamente:

```bash
cd /home/costa/frappe-bench
bench --site erp.local execute sistema_industrial.tango_sync.customer_push.push_customers_to_erpnext
```

O desde Python puro:
```python
from sistema_industrial.tango_sync.http_client import TangoHTTPClient
from sistema_industrial.erpnext_extensions.client import ERPNextClient
from sistema_industrial.tango_sync.customer_push import push_customers_to_erpnext

result = push_customers_to_erpnext(
    TangoHTTPClient.from_env().get_customers(),
    ERPNextClient(),
)
print(f"creados={result.created} actualizados={result.updated} fallidos={result.failed}")
```

No requiere nada más — `TangoHTTPClient.from_env()` lee `SI_NEXUS_KEY` automáticamente.

---

## Resumen

| Acción | Urgencia |
|---|---|
| `echo "SI_NEXUS_KEY=..." >> /etc/environment` | Cuando Constantino provea el token |
| `bench restart` | Inmediatamente después |
| Avisarme para correr el sync | Cuando esté configurado |

— Atlas
