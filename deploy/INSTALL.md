# NexTango — Instalación y datos (índice)

Dos cosas **separadas**, que no se mezclan. Se tocan **solo al final**, en este orden:

```
   1) INSTALAR EL PROGRAMA (una vez)        2) RESTAURAR LOS DATOS (recurrente)
   ┌─────────────────────────────┐         ┌─────────────────────────────┐
   │  install_programa.sh        │  ───▶   │  restore_datos.sh           │
   │  (código/entorno, sin datos)│  luego  │  (datos dentro del programa)│
   └─────────────────────────────┘         └─────────────────────────────┘
        doc: PROGRAMA.md                         doc: DATOS.md
```

---

## El límite (qué es cada cosa)

|  | **1. PROGRAMA** (código/entorno) | **2. DATOS** |
|---|---|---|
| Qué preserva | el SOFTWARE (Frappe/ERPNext + app custom) | patrones, precios, coefs, clientes, planos, `encryption_key`, token |
| De dónde viene | **GitHub** (reproducible) | **backup** de datos (`backup_datos.sh`) |
| Contiene datos | **NO** | **SÍ** (y credenciales → no va a git) |
| Cada cuánto | **una vez** por máquina | **recurrente**, independiente del código |
| Script | `install_programa.sh` | `backup_datos.sh` / `restore_datos.sh` |
| Doc | [PROGRAMA.md](PROGRAMA.md) | [DATOS.md](DATOS.md) |
| Destino | la máquina | `/home/costa/backups/…` (+ copia fuera del server) |

## El orden (obligatorio)

1. **Primero el programa** → seguir [PROGRAMA.md](PROGRAMA.md).
   Deja el sistema levantado con un **site vacío** (sin datos).
2. **Después los datos** → seguir [DATOS.md](DATOS.md).
   `restore_datos.sh <dir-backup> erp.local` mete los datos **dentro** del programa ya instalado.

> No hay un solo script que haga las dos cosas: es a propósito. Se pueden instalar programas
> nuevos sin tocar los datos, y se pueden respaldar/restaurar datos sin reinstalar el programa.

## Máquina nueva, de punta a punta

```bash
# --- 1. PROGRAMA (una vez) ---
ADMIN_PW='...' DB_ROOT_PW='...' ./install_programa.sh

# --- 2. DATOS (después) ---
#   (llevar un backup de datos hecho con ./backup_datos.sh, ej. por scp)
./restore_datos.sh /ruta/al/backup erp.local
```

Prerequisitos del SO, versiones y config manual (token Tango, `server-t`): ver
[PROGRAMA.md](PROGRAMA.md). Detalle de qué son "los datos" y la `encryption_key`: ver
[DATOS.md](DATOS.md).

## Estado de prueba (honesto)

- `backup_datos.sh`: **probado** — hay un backup real verificado (ver reporte a Nova).
- `install_programa.sh` / `restore_datos.sh`: probados **en su lógica**, no de punta a punta
  contra un site real. Antes de confiar en ellos para un evento, **probar el restore en un
  site aislado** (`test.local`), no en `erp.local`.
