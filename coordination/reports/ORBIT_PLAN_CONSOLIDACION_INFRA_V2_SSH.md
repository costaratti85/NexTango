# Plan de consolidación de infra — v2 (MODELO SSH)

**De:** Orbit (Build/Deploy) · con Forge en apoyo (Samba)
**Para:** Nova → Constantino (para aprobación)
**Fecha:** 2026-07-13
**Estado:** DISEÑO — nada ejecutado.
**Reemplaza:** la decisión #4 (clon local + venv local) de `ORBIT_PLAN_CONSOLIDACION_INFRA.md`. El resto de aquel doc sigue vigente.

---

## 0. Relevamiento SSH/recursos del server (solo lectura, hoy)

| Elemento | Estado real | Implicancia |
|---|---|---|
| SSH | `PubkeyAuthentication yes`, `PasswordAuthentication yes`. **`authorized_keys` de `costa` VACÍO** (todos entran por password). | Hay que montar el esquema de llaves desde cero. |
| Usuarios | **Solo `costa`** (uid 1000). No hay usuarios por agente. | Definir usuarios/aislamiento. |
| `gh` CLI | **No instalado**. `git` y `python3` sí. | Instalar `gh` para el flujo de PR. |
| Venv del bench | `/home/costa/frappe-bench/env` (Python 3.14) — **de Frappe, NO tocar**. | El venv standalone va **aparte**. |
| **Recursos** | **2 CPUs · 7.6 GB RAM** (1.4 GB usados por ERPNext, ~4-6 GB libres). | ⚠️ **Limitante central del modelo de 15 agentes** — ver §2. |

---

## ⚠️ Advertencia de capacidad (leer antes que nada)

El server es **2 vCPU / 7.6 GB RAM** con ERPNext en vivo. Eso condiciona el modelo:
- **Git operations (pull/push/commit/PR)** son livianas → 15 agentes haciendo git **conviven sin problema**.
- **Trabajo pesado** (pytest+numpy, vectorización de imágenes, `bench execute`, `bench build`) es CPU/RAM-intensivo → **NO caben 15 en paralelo** en 2 cores; saturarían el server y **degradarían ERPNext en producción**.

Conclusión: el modelo SSH es **viable para git + edición + tests acotados**, pero requiere **límites de recursos y serialización del trabajo pesado** (§2). Si se prevé trabajo pesado concurrente real de 15 agentes, el hardware queda corto → recomiendo evaluar upgrade (más vCPU/RAM) o mantener disciplina estricta. Lo marco como decisión de Constantino (§6).

---

## 1. CONCURRENCIA — 15 agentes sin pisarse

**Elección: un CLON git por agente (aislado), + el worktree del bench RESERVADO para deploy.**

```
/home/costa/Nextango/              ← worktree del BENCH (rama erpnext) — SOLO DEPLOY (solo Orbit). NADIE edita acá.
/home/costa/agents/
├── punto/Nextango/     (clon, rama feat/punto/*)     ← usuario punto
├── vega/Nextango/      (clon, rama feat/vega/*)      ← usuario vega
├── gemu/Nextango/      (clon, ...)                    ← usuario gemu
└── ... (uno por agente)
```

**Por qué clon por agente y no worktrees compartidos:**
| | Clon por agente (elegido) | Worktrees compartidos |
|---|---|---|
| Aislamiento | Total: cada uno su `.git` | Comparten `.git` — un `gc`/corrupción afecta a todos |
| Gotcha de ramas | Ninguno | La misma rama no puede estar en 2 worktrees a la vez |
| Costo | 15 × 8 MB = 120 MB (trivial) | Menor, pero irrelevante acá |
| Robustez con 15 agentes | Alta | Frágil |

- **El working tree del bench (`/home/costa/Nextango`, erpnext) es intocable para los agentes** — es lo que sirve producción. Se aísla del trabajo. Solo Orbit hace ahí `git pull` tras un merge, para desplegar. **Esto elimina de raíz los conflictos sobre el único working tree del bench.**
- Cada agente trabaja **en su clon, en su rama** `feat/<agente>/<tarea>`, y sincroniza vía **push a GitHub + PR** (§5). Nunca editan la rama de producción directamente.
- **Disciplina de ramas:** ramas de producción (`main`, `erpnext`) protegidas (sin push directo); todo entra por PR.

---

## 2. SEGURIDAD DE PRODUCCIÓN — aislar del bench vivo

1. **Working dirs separados del bench.** Clones de agentes en `/home/costa/agents/<agente>/` (o en el home de cada usuario), **nunca** en `/home/costa/Nextango` (bench) ni `frappe-bench/`.
2. **Los agentes NO son `costa`.** `costa` es dueño del bench y de producción. Los agentes usan **usuarios propios sin sudo** (§3). Solo Orbit tiene acceso a `costa`/sudo para deploy + `supervisorctl`.
3. **Nunca correr scripts pesados contra el site de producción `erp.local`:**
   - Tests del **motor standalone** (ezdxf, geometría, corte) → corren en el **venv standalone** (§4), sin tocar Frappe/DB.
   - Pruebas que **sí** requieren Frappe → contra un **site de staging** `bench new-site dev.local` (aislado), jamás `erp.local`.
4. **Límites de recursos (por los 2 vCPU):** el trabajo pesado se lanza acotado, p.ej. `systemd-run --scope -p CPUQuota=50% -p MemoryMax=1G ...` o `nice -n 15 ionice`, y **serializado** (no 15 pytests simultáneos). Se puede formalizar con una cola simple (un lock/semaforo) para trabajo pesado.
5. **ERPNext primero:** si el server se satura, producción manda. Los procesos de agentes van con `nice` alto (baja prioridad) para ceder CPU a los workers de Frappe.

---

## 3. ACCESO SSH por agente

**Esquema: usuarios Unix por agente + llaves ed25519 (una por agente). Sin passwords.**

- **Usuarios:** crear un usuario Unix por agente en grupo `nextango-dev` (`punto`, `vega`, `gemu`, …). Aísla working dirs, da trazabilidad (logs por usuario) y permisos limpios. **Sin sudo.**
  - *Alternativa descartada:* todos como `costa` con llaves distintas → comparten uid, sin aislamiento de FS, y serían dueños de producción (peligroso). No.
- **Llaves:** ed25519, **una por agente**. Como los ~15 agentes corren en la **misma Mint** (misma cuenta local), las privadas viven en la Mint (`~/.ssh/id_nx_<agente>`) + `~/.ssh/config` con alias por Host:
  ```
  Host nx-punto
      HostName 190.190.190.20
      User punto
      IdentityFile ~/.ssh/id_nx_punto
  ```
  La **pública** de cada agente → `authorized_keys` del usuario respectivo en el server. Las privadas **nunca salen de la Mint**.
- **Distribución:** Orbit/Forge generan los usuarios y cargan las públicas (las privadas se generan donde vivan los agentes). 
- **Endurecimiento:** una vez cargadas las llaves, `PasswordAuthentication no` en `sshd_config` (hoy está en `yes`). Mantener password solo durante la transición.
- **Grupo `nextango-dev`:** acceso RO a `planos` y al venv compartido; RW al share `compartida`.

---

## 4. VENV nativo en el server (resuelve el venv-sobre-SMB)

**Un venv standalone COMPARTIDO (read-only), separado del venv del bench.**

- Ubicación: `/opt/nextango/venv` (o `/home/costa/venvs/standalone`), **distinto** de `frappe-bench/env` (Frappe/py3.14 — intocable).
- Contenido: `ezdxf`, `paramiko`, `pytest` (+ lo que peguen de la Windows que sea Python), desde `requirements.txt` del repo. Lo mantiene **Orbit**.
- **Compartido RO:** todos los agentes lo **activan** (`source /opt/nextango/venv/bin/activate`) para correr el motor/tests. Ventaja: **versiones idénticas para todos**, una sola instalación (ahorra los ~400 MB×15 de numpy & cía).
- ¿Un agente necesita una lib nueva? → la pide a Orbit → se agrega a `requirements.txt` + se instala en el venv compartido (un solo lugar, versionado).
- **Regla:** el intérprete y las libs corren **local en el server** (nativo, rápido). Esto es exactamente lo que el modelo SSH resuelve del problema venv-sobre-SMB.

---

## 5. Flujo de PR

- **Instalar `gh` CLI** en el server (falta). Auth: un token GitHub por usuario-agente (o un token de máquina con scope limitado).
- **Circuito:**
  1. Agente: `git switch -c feat/<agente>/<tarea>` (desde `erpnext` o `main` según el cambio) en su clon.
  2. Commit → `git push -u origin feat/<agente>/<tarea>`.
  3. `gh pr create --base erpnext --title ... --body ...`.
  4. Revisión (Nova/rol integrador) → **merge**.
- **Quién mergea (control de producción):** `erpnext` y `main` con **branch protection** en GitHub (require PR, prohíbe push directo). El merge lo hace un **integrador único** — propongo **Nova aprueba, Orbit mergea** — no los 15 agentes directo a la rama desplegada.
- **Post-merge → deploy:** Orbit hace `git pull` en el worktree del bench (`/home/costa/Nextango`, erpnext) + `bench build`/`migrate` según corresponda. El flujo de deploy actual **no cambia**.

---

## 6. Nativo por SSH (server) vs atado a Windows (Samba)

| Proyecto | Corre en Ubuntu (SSH nativo)? | Dónde |
|---|---|---|
| Motor patrones / vectorizador / corte / API Frappe / tests | ✅ Sí (Python/JS multiplataforma) | **Nativo por SSH** |
| `ezdxf` / `paramiko` y libs Python | ✅ Sí | **Venv standalone** (§4) |
| **CostADCAM `.exe`** (57 MB, binario Windows) | ❌ No corre en Ubuntu | **Samba** — se ejecuta en una máquina Windows. Su fuente Python (`cam_core_v9.py`, `nesting_coedge.py`) *podría* portarse a Ubuntu, pero el `.exe` distribuido no. |
| **VBA/Excel** (`.bas`, `.xlam`, `.xlsm`) | ❌ Requiere Excel/Windows | **Samba** — edición/ejecución en Windows |
| **`ocr_transferencias.pyw`** | ⚠️ A confirmar | `.pyw` sugiere GUI Windows (tkinter/pywin32). Si es Python puro headless → nativo; si depende de Windows → Samba |

**Regla:** Python/JS multiplataforma → nativo por SSH en el server. Binarios Windows / Excel / GUI-Windows → Samba, ejecutados en Windows.

---

## Se mantiene de v1 (sin cambios)
- **App Frappe** en `/home/costa/frappe-bench/apps/sistema_industrial` (symlink → `/home/costa/Nextango`). No se mueve. Sync por git.
- **Carpeta central de archivos** `/home/costa/compartida/` (RW por Samba) + `planos` (RO). Shares restringidos a `190.190.190.0/24`. Ejecuta **Forge**.
- **Origin canónico = GitHub.**

## Coordinación con la purga del token (orden actualizado)
El force-push de la purga obliga a reconciliar clones. Con el modelo SSH habrá **15 clones-agente + el worktree del bench** en el server → mucha más superficie de resync.

**Orden recomendado:**
1. **Purga primero** (ahora, con los pocos clones actuales — está lista, esperando la ventana de Nova, MSG_097).
2. **Montar el modelo SSH después:** crear usuarios/clones-agente **desde el repo YA purgado**. Así los 15 clones **nacen limpios** y se evita reconciliar 15 clones post-force-push.
3. Repo privado → **sin rotación** (confirmado). La purga es higiene.

---

## Qué necesita de Constantino (acciones/decisiones)

| # | Necesito | Detalle |
|---|---|---|
| 1 | **OK al modelo de usuarios** | ¿Usuario Unix por agente (recomendado, aislado) o esquema más simple? |
| 2 | ⚠️ **Decisión de capacidad** | 2 vCPU/7.6 GB con ERPNext vivo **no soporta trabajo pesado de 15 agentes en paralelo**. ¿Aceptamos límites+serialización del trabajo pesado, o evaluás **upgrade de hardware**? |
| 3 | **Llaves SSH** | OK a generar 1 llave ed25519 por agente y cargar públicas; luego apagar `PasswordAuthentication`. |
| 4 | **Token(s) GitHub para `gh`** | Uno por agente o de máquina. Y OK a **branch protection** en `main`/`erpnext` (merge solo por PR). |
| 5 | **Quién mergea** | Confirmar integrador único (propongo Nova aprueba / Orbit mergea). |
| 6 | **Site de staging** | OK a crear `dev.local` en el bench para pruebas que toquen Frappe (aísla `erp.local`). |
| 7 | **Contraseña Samba** + puertos LAN | `smbpasswd -a costa`; SSH 22 (ya) y Samba 445 solo desde `190.190.190.0/24`. |
| 8 | **Orden** | Confirmar: **purga → montar modelo SSH → consolidación de archivos/Samba**. |
| 9 | **Credencial Windows vieja** | `\\190.190.190.15\c` sigue en `LOGON_FAILURE` (para el import por Samba). |

---

## Resumen ejecutivo
- **Concurrencia:** 1 clon por agente en `/home/costa/agents/<agente>/`; el worktree del bench queda **solo para deploy** (Orbit). Ramas protegidas + PRs.
- **Producción:** agentes aislados del bench, sin sudo, trabajo pesado limitado/serializado y **nunca contra `erp.local`** (usar `dev.local`). ⚠️ **El hardware (2 vCPU) es el cuello de botella real** — decisión de Constantino.
- **SSH:** usuarios Unix por agente + llaves ed25519, sin passwords.
- **Venv:** compartido RO en `/opt/nextango/venv`, aparte del venv del bench.
- **PR:** `gh` CLI, rama→PR→merge por integrador único (Nova/Orbit).
- **Windows-nativo** (CostADCAM `.exe`, VBA/Excel) → Samba; el resto → nativo por SSH.
- **Orden:** purga del token primero, luego montar el modelo SSH desde el repo limpio.

**Nada se ejecuta hasta que Constantino apruebe.** Con el OK, Orbit + Forge lo montamos en ventana coordinada.

— Orbit
