# Plan de consolidación de infraestructura — Ubuntu server 190.190.190.20

**De:** Orbit (Build/Deploy) · con Forge en apoyo (Samba)
**Para:** Nova → Constantino (para aprobación)
**Fecha:** 2026-07-13
**Estado:** DISEÑO — nada ejecutado. No se toca el server hasta aprobación.

---

## 0. Relevamiento del estado actual (solo lectura, hoy)

Antes de diseñar, verifiqué qué hay en el server:

| Elemento | Estado real |
|---|---|
| Repo git | **Ya existe** en `/home/costa/Nextango/` — clon completo, ramas `main` + `erpnext`, worktree en `erpnext`. Remote = GitHub `costaratti85/NexTango`. |
| App Frappe | `/home/costa/frappe-bench/apps/sistema_industrial` es un **symlink** → `/home/costa/Nextango/apps/sistema_industrial`. El bench ya consume el repo central. |
| `planos` | `/home/costa/planos/` (DXF, `calibracion_laser/` con `tabla.json`+`bateria_calibracion.dxf`+`bateria2/`, `generico/`). Share Samba `[planos]` **read-only**, `valid users=costa`, `hosts allow=190.190.190.0/24`. |
| `compartida` | `/home/costa/compartida/` existe y está **vacía** (candidata natural a carpeta central RW). |
| Samba | Instalado y activo. Shares reales: `[planos]` (RO, LAN) y `[MiCarpeta]` (placeholder sin usar, `/ruta/a/tu/carpeta`). |
| Disco | 37 GB libres de 54 GB (28% usado). Sobra para lo de la Windows (el mayor es el `.exe` de CostADCAM, 57 MB). |
| Ruido | `/home/costa/` tiene ~25 scripts sueltos `check_*.py` + logs — conviene ordenarlos en la consolidación. |

**Conclusión clave:** la "carpeta central" **casi ya existe**. El repo está consolidado en `/home/costa/Nextango/` y el bench lo consume por symlink. El trabajo real es: (a) una carpeta central de **archivos no-git** compartida R/W, y (b) formalizar los shares para Windows+Mint. El código sigue viajando por git, no por Samba.

---

## 1. Convivencia app Frappe ↔ carpeta central (sincronizadas por git)

**La app NO se mueve y NO hace falta tocar nada: la convivencia ya está resuelta por el symlink existente.**

```
/home/costa/Nextango/                          ← REPO CENTRAL (git, rama erpnext desplegada)
      └── apps/sistema_industrial/  ←──────┐
/home/costa/frappe-bench/                   │ symlink (ya existe)
      └── apps/sistema_industrial  ─────────┘  ← lo que ve el bench
```

- El repo central **es** `/home/costa/Nextango`. El bench lo consume vía symlink → **lo desplegado siempre = lo del repo central**, sin duplicar checkout ni copiar archivos.
- **Sincronización = git**: el deploy sigue siendo `git pull` en `/home/costa/Nextango` (rama erpnext) + `bench build`/`migrate`. Sin cambios al flujo actual.
- **Decisión justificada:** symlink (ya montado) > clon separado (duplicaría y se desincronizaría) > remote adicional (innecesario). No se toca.
- **Opcional:** si se quiere el checkout de `main` también visible en el server (p.ej. para leer `coordination/` de ambas ramas), agregar un worktree: `git worktree add /home/costa/Nextango-main main`. No es necesario para el bench.

---

## 2. Carpeta central: dónde vive y qué se consolida

Separo explícitamente **dos naturalezas** de contenido, porque van por vías distintas:

### 2A. Código versionado → por **git** (NO por Samba)
Vive en `/home/costa/Nextango/` (repo, main+erpnext). Se sincroniza por git contra GitHub. **No se comparte por Samba** para trabajo (SMB + `.git` = lentitud y riesgo de corrupción del índice). Si se quiere inspección de solo-lectura desde el share, se expone aparte (ver 3).

### 2B. Archivos NO versionados → por **Samba R/W**
Carpeta central única: **`/home/costa/compartida/`** (ya existe, vacía). Estructura propuesta:

```
/home/costa/compartida/            ← SHARE CENTRAL R/W (Windows + Mint)
├── windows_import/                ← lo que Constantino pega de la Windows
│   ├── CostADCAM/                 (cam_core_v9.py, nesting_coedge.py, gcode_exporter.py, el .exe 57MB)
│   ├── pedido_excel/              (TangoAPI_VBA.bas, TangoAPI.xlam, PRESUPUESTO_PLANTILLA.xlsm)
│   ├── ocr_mercadopago/           (ocr_transferencias.pyw)
│   └── ssh_keys/                  (id_rsa/id_ed25519 — copiar y sacar de acá al ~/.ssh de cada máquina)
├── intercambio/                   ← scratch compartido de trabajo (DXF sueltos, exports, capturas)
└── planos → (ver nota)            ← ver decisión sobre planos abajo
```

**`planos` — NO se mueve.** La app tiene rutas absolutas `/home/costa/planos/...` **congeladas en la DB** (`SI Patron Version`). Moverlo rompería patrones existentes. Por eso:
- `/home/costa/planos/` **queda donde está**, con su share `[planos]` **read-only** (ya funciona; incluye `calibracion_laser/`).
- Constantino ve **dos unidades de red**: `planos` (RO, insumos de la app) y `compartida` (RW, trabajo + import de Windows). Es lo más seguro; unificarlas en una sola letra de red vía symlinks obliga a `wide links` en Samba (riesgo de seguridad) — no lo recomiendo.

> Referencia de qué se consolida: tabla completa en `coordination/MIGRACION_CARPETAS_FALTANTES.md` (CostADCAM, VBA/Excel, ocr_transferencias, clave SSH, generate_version_stamp, calibración, planos).

---

## 3. Samba: shares, credenciales, permisos, LAN

Reutiliza el patrón que **Forge** ya validó en `[planos]`. Propuesta de `smb.conf`:

```ini
[compartida]                        ; NUEVO — carpeta central de trabajo/import, R/W
   path = /home/costa/compartida
   read only = no
   writable = yes
   valid users = costa
   hosts allow = 190.190.190.0/24
   hosts deny = 0.0.0.0/0
   create mask = 0664
   directory mask = 0775
   browseable = yes

[planos]                            ; EXISTENTE — insumos de la app, solo lectura (sin cambios)
   path = /home/costa/planos
   read only = yes
   valid users = costa
   hosts allow = 190.190.190.0/24
```

- **Credenciales:** usuario Samba `costa` (mismo del share planos). Necesita **contraseña Samba** seteada con `smbpasswd -a costa` (es independiente de la de login Linux). → acción de Constantino/Forge (punto 6).
- **Restricción LAN:** `hosts allow = 190.190.190.0/24` + `hosts deny` — nunca expuesto a internet. Puerto **445/tcp** (y 139) solo en la interfaz LAN; si hay firewall (`ufw`), abrir 445 **solo** desde 190.190.190.0/24.
- **Permisos R/W:** `compartida` R/W para `costa`; `planos` RO (protege los DXF que la app usa en vivo).
- **Acceso:**
  - Windows: `net use Z: \\190.190.190.20\compartida /user:costa` (y `Y:` para `planos`).
  - Mint: `mount -t cifs //190.190.190.20/compartida /mnt/compartida -o username=costa,password=...,uid=$(id -u),vers=3.0` (RW) y `planos` con `ro`.
- **Ejecutor:** **Forge** (es su expertise, ya hizo `[planos]`). Le paso la config por su canal.

---

## 4. Workflow de desarrollo post-consolidación (agentes en la Mint)

**Recomendación: código por clon git local; archivos por share SMB. NO trabajar el código sobre el share.**

| Dimensión | Clon git local (recomendado) | Trabajar sobre el share SMB |
|---|---|---|
| Velocidad build/test | Rápido (disco local) | **Lento** (I/O de miles de archivos por SMB) |
| **venv Python** (`ezdxf`/`paramiko`) | Local, sano | **Se rompe/arrastra** sobre SMB — no viable |
| `.git` operaciones | Rápidas y seguras | Riesgo de corrupción de índice |
| Archivos pesados (DXF, `.exe`, xlsm) | — | **Ideal** — acceso directo compartido |

**Modelo recomendado:**
- **Código** → cada agente/máquina Mint **clona de GitHub** (`~/SistemaIndustrial/Nextango` main + `Nextango-erpnext` erpnext, como ya está) y corre su **venv local** (`.venv`, ya creado: ezdxf 1.4.4 / paramiko 5.0.0). Sincroniza con `git pull`/`push`.
- **Archivos no-git** (planos, DXF de referencia, CostADCAM, lo de Windows) → **montar el share** `//190.190.190.20/compartida` (RW) y `//.../planos` (RO) en la Mint. Se leen/escriben directo, sin pasar por git.
- **Regla:** el `.venv` **nunca** sobre SMB. Si un script necesita leer un DXF del share, lee del punto de montaje; el intérprete y las libs corren local.

---

## 5. Coordinación con la purga del token + origin canónico

### Origin canónico: **GitHub** (`costaratti85/NexTango`) — se mantiene.
- **Justificación:** (a) la purga (`ORBIT_PURGA_HISTORIAL_TOKEN`) ya está diseñada y ensayada contra GitHub como origin; (b) todos los clones (server + Mint) ya apuntan ahí; (c) la meta de Constantino es consolidar **archivos**, no cambiar el remoto git; (d) mover a un bare repo en el server como origin agregaría reconfiguración de todos los remotes y un punto único de falla en la LAN, sin beneficio para esta meta.
- El **server `/home/costa/Nextango` es un clon más** (consumido por el bench), no el origin.

### Orden seguro (las dos operaciones son ortogonales, pero comparten "clones a resync")
La consolidación de infra (Samba/carpetas) **no toca git history**; la purga sí (force-push). El único cruce: el clon del server es uno de los que hay que **resincronizar** tras el force-push.

**Secuencia recomendada:**
1. **Purga primero** (ya está lista, esperando la ventana de Nova): force-push → **resync de TODOS los clones**, incluido `/home/costa/Nextango` del server (`git fetch && git reset --hard origin/erpnext`, con backup previo del working tree sucio de thumbnails — ver mi MSG_097).
2. **Consolidación de infra después** (o en paralelo, ya que no depende del history): crear `compartida/`, shares Samba, montar en Mint, y recién ahí Constantino pega lo de la Windows.
3. Repo **privado** → Constantino confirmó **sin rotación** de token; la purga es higiene. No hay dependencia de rotación.

**Regla de oro post-purga:** ningún clon debe `merge`/`pull` de una rama vieja (reintroduce el token). Solo `reset --hard origin/<rama>`. Aplica también al clon del server.

---

## 6. Qué necesita de Constantino (acciones manuales / decisiones)

| # | Necesito | Detalle |
|---|---|---|
| 1 | **Contraseña Samba** para `costa` | Se setea con `smbpasswd -a costa` (distinta de la de login). ¿Reusar una existente o definir una nueva? La comparto con Windows+Mint. |
| 2 | **OK a los paths** | Carpeta central = `/home/costa/compartida/` (RW). `planos` queda donde está (RO). ¿De acuerdo o preferís otro nombre/ubicación? |
| 3 | **Puerto LAN 445** | Confirmar que la LAN 190.190.190.0/24 puede llegar al 445 del server (si hay `ufw`/firewall, Forge lo abre solo para esa subred). |
| 4 | **Decisión VBA vs Python** (PedidoExcel) | Define si el material VBA va como R/W (sigue en VBA) o solo-lectura de referencia (se reescribe en Python). Cambia permisos de esa subcarpeta. |
| 5 | **Confirmar orden** | ¿Purga del token primero (abrir la ventana con Nova) y después la consolidación? Es lo que recomiendo. |
| 6 | **Recuperación Windows** | El share del disco viejo `\\190.190.190.15\c` sigue con `LOGON_FAILURE`. Para lo de la tabla de migración hace falta la credencial válida (o que Constantino copie a mano a `compartida/` una vez montada). |
| 7 | (menor) **Limpieza de `/home/costa`** | ¿Puedo archivar los ~25 `check_*.py` sueltos + logs a `compartida/intercambio/_home_scripts/`? Ordena el home. |

---

## Resumen ejecutivo

- **La app no se mueve** — ya convive con el repo central por symlink; sync por git. Cero riesgo.
- **Carpeta central de archivos = `/home/costa/compartida/`** (RW, Samba), con `windows_import/` para lo de la Windows. **`planos` no se mueve** (paths congelados en DB), queda RO.
- **Dos shares Samba** restringidos a la LAN: `compartida` (RW) + `planos` (RO). Ejecuta **Forge**.
- **Código por git local + venv local; archivos por share.** El venv nunca sobre SMB.
- **Origin canónico = GitHub.** **Purga del token primero**, consolidación después; ambos requieren resync del clon del server.
- **Bloqueos externos:** contraseña Samba, credencial de la Windows vieja, y OK de paths/orden — todo de Constantino (punto 6).

**Nada de esto se ejecuta hasta que Constantino apruebe.** Con el OK, Forge y yo lo implementamos en una ventana coordinada.

— Orbit
