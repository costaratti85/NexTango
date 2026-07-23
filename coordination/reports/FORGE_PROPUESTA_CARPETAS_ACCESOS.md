# Propuesta FINAL — Carpetas compartidas + matriz de acceso (Samba)

**De:** Forge (ERP Systems Integration — líder de esta propuesta) · con aporte de Orbit (layout server + coexistencia git/bench)
**Para:** Nova → Constantino (para **aprobación**)
**Fecha:** 2026-07-13
**Estado:** DISEÑO FINAL — nada ejecutado. No se toca el server hasta el OK de Constantino.
**Base:** brief Nova MSG_030 + `ORBIT_PLAN_CONSOLIDACION_INFRA.md` (§2–§3) + `MIGRACION_CARPETAS_FALTANTES.md`.

---

## Regla de oro (define todo el diseño)
- **El código NO va por el share.** Viaja por git (Mint → GitHub → `git pull` en el server). El share es **solo para archivos NO-código**: DXF/planos, calibración, y lo que Constantino pega desde la Windows.
- **`planos` NO se mueve.** Tiene rutas absolutas congeladas en la DB (`SI Patron Version`); moverlo rompe los patrones. Queda donde está, como share **read-only**.
- **La app Frappe no se toca** (`frappe-bench/apps/sistema_industrial` → symlink al repo, ya resuelto por Orbit).

---

## 1. Estructura EXACTA de carpetas en el server (190.190.190.20)

```
/home/costa/planos/                      ← SE QUEDA. Insumos de la app (RO por share).
   ├─ generico/  patrones/  ...          (DXF históricos + patrones)
   └─ calibracion_laser/                 (P01–P14, Batería 2, tabla.json, bateria_calibracion.dxf)

/home/costa/compartida/                  ← YA EXISTE (vacía). Carpeta central de archivos NO-código.
   ├─ windows_import/                     ← Constantino PEGA lo de la Windows; agentes LEEN.
   │    ├─ CostADCAM/                     (cam_core_v9.py, nesting_coedge.py, gcode_exporter.py, .exe 57MB)
   │    ├─ pedido_excel/                  (TangoAPI_VBA.bas, TangoAPI.xlam, PRESUPUESTO_PLANTILLA.xlsm)
   │    └─ ocr_mercadopago/               (ocr_transferencias.pyw)
   └─ intercambio/                        ← scratch R/W para TODOS (DXF sueltos, exports, capturas).
```

- **Base path:** `/home/costa/compartida/` (confirmar con Constantino — punto 4.2). `planos` queda en `/home/costa/planos/`.
- **Espacio en disco:** OK — 37 GB libres de 54 GB (relevamiento de Orbit). El archivo más pesado (el `.exe` de CostADCAM, 57 MB) entra sin problema.
- **Claves SSH:** NO van al share (son credenciales). Se copian una vez al `~/.ssh/` de cada máquina, no se comparten por SMB.
- **`generate_version_stamp.py`:** NO es archivo de share — se recupera/recrea y se **commitea al repo** (git), no va por Samba.

---

## 2. Matriz de acceso (FINAL)

Dos identidades Samba (roles), no 15 usuarios (justificación en §3):
- **`costa`** = Constantino, desde **Windows y desde la Mint** → RW en todo.
- **`agente`** = rol compartido de los ~15 agentes (corren todos en la misma Mint) → RO salvo `intercambio`.

| Carpeta | Agentes (rol `agente`, Mint) | Constantino (`costa`, Windows) | Constantino (`costa`, Mint) | Cómo se aplica |
|---|---|---|---|---|
| `planos/` | **Lectura** | **L/E** | **L/E** | Share RO baseline + `write list = costa` |
| `planos/calibracion_laser/` | **Lectura** | **L/E** | **L/E** | (hereda de `planos/`) |
| `compartida/windows_import/` | **Lectura** | **L/E** | **L/E** | POSIX `0755 costa:costa` (owner RW, other RO) |
| `compartida/intercambio/` | **L/E** | **L/E** | **L/E** | POSIX `2775 costa:smbshare` (grupo RW, setgid) |

- **Punto subiendo DXF a `planos/`:** lo hace **por SSH** (ya tiene llave; contemplado en el plan SSH de Orbit), **no** por el share. Así `planos` queda RO en Samba y no hay que darle escritura al rol `agente`. Si Constantino prefiere que Punto suba por el share, se lo agrega a `write list` de `planos` (queda anotado, no lo asumo).

---

## 3. Esquema de usuarios Samba (restringido a la LAN `190.190.190.0/24`)

**Decisión: 2 usuarios-rol, NO uno por agente.** Los 15 agentes corren en la **misma Mint** (misma cuenta local); 15 usuarios Samba no aportan seguridad en un file-share (la trazabilidad de *código* ya la da git por commit; `intercambio` es scratch, no requiere auditoría por-agente) y multiplican el mantenimiento por 15. Un rol RO compartido es lo correcto y lo más simple de operar.

- **`costa`** — usuario del sistema ya existente (uid 1000, dueño del bench y de producción). Se le setea **contraseña Samba** con `smbpasswd -a costa` (independiente de la de login Linux). Es la identidad de Constantino desde Windows y Mint. **RW.**
- **`agente`** — usuario de sistema **sin login** (`useradd -M -s /usr/sbin/nologin agente`), dado de alta **solo** como cuenta Samba (`smbpasswd -a agente`). Rol RO de los agentes. Su credencial se distribuye a los agentes en la Mint. **RO** salvo `intercambio`.
- **Grupo `smbshare`** (nuevo): miembros `costa` y `agente`. Da RW de grupo a `intercambio/`.

### `smb.conf` propuesto (reusa el patrón ya validado de `[planos]`)

```ini
[planos]                              ; EXISTENTE — insumos app, RO para agentes, RW para Constantino
   path = /home/costa/planos
   valid users = costa, agente
   read only = yes                    ; baseline RO
   write list = costa                 ; solo Constantino escribe
   hosts allow = 190.190.190.0/24
   hosts deny = 0.0.0.0/0
   browseable = yes

[compartida]                          ; NUEVO — carpeta central de archivos no-código
   path = /home/costa/compartida
   valid users = costa, agente
   read only = no                     ; baseline RW; el FS decide por subcarpeta (§2)
   create mask = 0664
   directory mask = 2775
   force group = smbshare
   hosts allow = 190.190.190.0/24
   hosts deny = 0.0.0.0/0
   browseable = yes
```

**Por qué UN solo share `compartida` y no dos:** la diferencia de permisos entre `windows_import` (agentes RO) e `intercambio` (agentes RW) la resuelve el **filesystem** (POSIX), no smb.conf. Así Constantino monta **2 unidades de red** (`planos` + `compartida`), no 3.

### Permisos de filesystem a aplicar (los que hacen cumplir la matriz)
```bash
groupadd smbshare
usermod -aG smbshare costa
usermod -aG smbshare agente
chmod o+x /home/costa                                   # traverse para que 'agente' alcance los shares (NO o+r: el home sigue sin listarse)
mkdir -p /home/costa/compartida/windows_import /home/costa/compartida/intercambio
chown -R costa:costa   /home/costa/compartida/windows_import   && chmod -R 0755 /home/costa/compartida/windows_import
chown    costa:smbshare /home/costa/compartida/intercambio     && chmod 2775   /home/costa/compartida/intercambio
```
- `windows_import` = `0755 costa:costa` → `agente` (other) lee, no escribe; `costa` (owner) RW.
- `intercambio` = `2775 costa:smbshare` (setgid) → `agente` (grupo) RW; archivos nuevos heredan grupo `smbshare`.
- `chmod o+x /home/costa` da solo **traverse** (no listado): sin él, `agente` no puede entrar a `/home/costa/planos` ni `/home/costa/compartida`. Es el mínimo imprescindible; `planos` no se puede reubicar a `/srv` por los paths congelados en DB. *(Alternativa si Constantino prefiere no tocar el home: reubicar solo `compartida` a `/srv/compartida` — pero `planos` igual necesita el `o+x` en `/home/costa`.)*

### Restricción de red / firewall
- `hosts allow = 190.190.190.0/24` + `hosts deny = 0.0.0.0/0` en ambos shares → **nunca** expuesto a internet.
- Puerto **445/tcp** (y 139) solo alcanzable en la LAN. Si hay `ufw` activo, abrir 445 **solo** desde `190.190.190.0/24` (`ufw allow from 190.190.190.0/24 to any port 445 proto tcp`). *A verificar el estado de `ufw` en la ejecución (no confirmado aún — punto 4.5).*

### Montaje (probado ya con `[planos]`)
- **Constantino — Windows** (RW, usuario `costa`):
  ```
  net use Y: \\190.190.190.20\planos     /user:costa *
  net use Z: \\190.190.190.20\compartida /user:costa *
  ```
- **Constantino — Mint** (RW, usuario `costa`):
  ```
  mount -t cifs //190.190.190.20/compartida /mnt/compartida -o username=costa,uid=$(id -u),vers=3.0
  mount -t cifs //190.190.190.20/planos     /mnt/planos     -o username=costa,uid=$(id -u),vers=3.0,ro
  ```
- **Agentes — Mint** (rol `agente`): idéntico pero `username=agente`; `planos` y `windows_import` quedan RO por permisos aunque se monte RW.

---

## 4. Lo que necesito de Constantino para dejarlo operativo (EXPLÍCITO)

| # | Necesito | Detalle / por qué |
|---|---|---|
| 4.1 | **Contraseña Samba para `costa`** (la elige él) | Su identidad RW desde Windows y Mint. Se aplica con `smbpasswd -a costa`. Es independiente de la de login Linux. |
| 4.2 | **OK a los paths** | Central = `/home/costa/compartida/` (RW). `planos` se queda en `/home/costa/planos/` (RO, no se mueve). ¿De acuerdo o preferís otro nombre/ubicación? |
| 4.3 | **Contraseña Samba para el rol `agente`** | La puedo **generar yo** y pasártela para que la apruebes/distribuyas a los agentes, o la definís vos. Decime cuál preferís. |
| 4.4 | **OK a `chmod o+x /home/costa`** (solo traverse, NO listado del home) | Imprescindible para que el rol `agente` alcance `planos` y `compartida`. Si preferís no tocar el home, autorizá reubicar `compartida` a `/srv/compartida` (`planos` igual requiere el `o+x`). |
| 4.5 | **Puerto SMB 445 en la LAN** | Confirmar que `190.190.190.0/24` llega al 445 del server. Si hay `ufw`, lo abro **solo** para esa subred. |
| 4.6 | **Confirmar el esquema de 2 roles** (`costa` RW + `agente` RO), no 15 usuarios | Es mi recomendación; solo necesito tu OK explícito. |
| 4.7 | **(contenido, no share)** Credencial válida del disco viejo `\\190.190.190.15\c` | Hoy da `NT_STATUS_LOGON_FAILURE`. Sin ella no se puede **poblar** `windows_import` con lo de la Windows (CostADCAM, VBA, OCR). El share se crea igual; queda vacío hasta tener acceso o hasta que Constantino copie a mano. |

---

## 5. Coexistencia con git/bench (aporte de Orbit — sin cambios de mi lado)
- El repo central es `/home/costa/Nextango`; el bench lo consume por **symlink** ya existente → deploy = `git pull` + `bench build`. El share **no toca** nada de esto.
- **Regla:** el `.venv` de Python y el `.git` **nunca** sobre SMB (lento y corrompe índices). Código y entornos → local/git; solo archivos no-código → share.
- **Orden con la purga del token:** la consolidación del share **no toca git history** y es ortogonal a la purga. Se puede hacer en la misma ventana; el único cruce es el resync del clon del server tras el force-push (responsabilidad de Orbit). Coordino la ventana con Orbit y Nova.

---

## 6. Resumen ejecutivo (para el "sí" de Constantino)
1. **Dos shares** restringidos a la LAN: `planos` (RO agentes / RW Constantino) + `compartida` (con `windows_import` RO-agentes e `intercambio` RW-todos).
2. **Dos roles Samba:** `costa` (Constantino, RW, Windows+Mint) y `agente` (agentes, RO salvo `intercambio`). No 15 usuarios.
3. **`planos` no se mueve** (DB congelada); la app no se toca.
4. **De Constantino:** contraseña Samba de `costa`, OK a paths, OK al rol `agente` (+ su password), OK a `chmod o+x /home/costa`, y confirmar 445 en la LAN. Para *poblar* `windows_import`: arreglar la credencial del disco viejo.

**Nada se ejecuta hasta el OK de Constantino.** Con la aprobación, Forge implementa los shares + permisos y Orbit coordina la ventana con la purga.

— Forge
