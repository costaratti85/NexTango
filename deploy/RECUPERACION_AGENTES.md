# Recuperar a los agentes si se rompe la Mint — relevamiento + procedimiento realista

> Pregunta de Constantino: *"si se rompe la Mint donde tengo Claude Desktop (Cowork), ¿cómo
> recupero a TODOS los agentes?"* — Respuesta honesta abajo. **Relevamiento de solo lectura;
> no se probó restauración ni reinstalación.**

---

## Lo más importante (la verdad, sin vueltas)

**Los agentes NO son programas que se "prenden" desde un archivo de sesión.** Cada agente
(Orbit, Nova, Atlas, Forge, Punto, Vega…) es una sesión de Claude a la que se le da un **rol** y
un **contexto**. Su identidad y su conocimiento durable **no viven en la Mint**: viven en
**GitHub** (la carpeta `coordination/` + las memorias). La Mint solo tiene la *instancia corriendo*
de Claude Desktop y el historial de sesiones.

Por eso hay **dos capas**, y solo una se pierde si muere la Mint:

| Capa | Dónde vive | ¿Sobrevive a que muera la Mint? |
|---|---|---|
| **Cerebro durable**: roles, DECISIONs, canon, `queue.json`, reportes, briefs, **memorias** | GitHub (`coordination/`) + backup de memorias | **SÍ** (está en la nube y ahora también respaldado) |
| **Instancia local**: sesiones vivas de Cowork, login/tokens, identidad de dispositivo, caches | `~/.config/Claude/` en la Mint | **NO** transfiere 1:1 (ver abajo) |

**Conclusión honesta:** restaurar `~/.config/Claude/` en una **máquina nueva NO "revive" las
sesiones 1:1.** Sí se recupera **todo lo que importa** para reconstituir el equipo: memorias,
config y el canon entero. Los agentes se **vuelven a instanciar** desde esos archivos — no se
"resucita" la ventana de chat tal cual estaba.

### Por qué las sesiones no transfieren 1:1 (evidencia relevada)
- **Cifrado atado al SO:** `~/.config/Claude/Local State` usa `os_crypt` con backend `portal`
  (servicio de secretos del sistema). Las cookies/tokens se cifran con una clave del **keyring de
  la Mint** → en otra máquina **no se pueden descifrar**.
- **Identidad de dispositivo:** hay `ant-did` y `ant-device-registry.json` (registro por
  dispositivo). Una máquina nueva se registra como **otro** dispositivo.
- **Login:** Claude Desktop se autentica contra la **cuenta** (costaratti@gmail.com), no contra
  archivos. En la máquina nueva se **inicia sesión de nuevo**.
- Lo que **sí** es texto plano y sirve de referencia: los **transcripts** (`.jsonl`) y las
  **memorias** (`.md`).

---

## Qué guarda Claude Desktop/Cowork en la Mint (mapa)

Ruta base: `~/.config/Claude/` (**555 MB** total). Lo relevante:

| Carpeta / archivo | Tamaño | Qué es | ¿Backup? |
|---|---|---|---|
| `local-agent-mode-sessions/` | 26 MB | **sesiones vivas de Cowork** + `…/agent/memory/` (MEMORY.md + memorias de Cowork) | **SÍ** (nuevo) |
| `claude_desktop_config.json` | 2 KB | **config MCP** (servidores/conectores) | **SÍ** (nuevo) |
| `config.json` | 5 KB | config de la app | **SÍ** (nuevo) |
| `Cache/`, `Code Cache/`, `claude-code/`, `GPUCache/` | ~490 MB | **caches regenerables** | NO (a propósito) |
| `Cookies`, `Local State`, `blob_storage/`, `IndexedDB/` | var. | auth/estado cifrado, atado a la máquina | NO (no sirve en otra máquina) |

Además, **fuera** de `~/.config/Claude`, en `~/.claude/projects/<proyecto>/memory/` viven las
**memorias del CLI** (las que usa este equipo en el repo). Para Nextango son **22 archivos**
(`deploy-nextango.md`, `infra-critica.md`, `user-constantino.md`, los modelos de láser/plegado,
etc.) + su `MEMORY.md`. **Estas también quedan respaldadas** (ver abajo).

---

## Qué está A SALVO hoy y qué era un riesgo

**A salvo (en GitHub):** `coordination/` — **379 archivos** commiteados y **pusheados**
(`main == origin/main`). Roles, canon, DECISIONs, `queue.json`, reportes, briefs.

**⚠️ Riesgo detectado (hay que cerrarlo):** **265 archivos de `coordination/` SIN commitear** en
la Mint — entre ellos **18 en `decisions/`** (canon), **6 en `reports/`**, 3 en `research/`, 233
mensajes de canal. **Eso hoy vive solo en la Mint.** Si muere la Mint sin pushear, se pierden.
→ **Recomendación:** hacer un commit+push de barrido de `coordination/` (coordinar con Nova para
no pisar trabajo en curso). Es la forma más barata de blindar el cerebro durable.

**Respaldado desde ahora (nuevo backup):** memorias (CLI + Cowork), config MCP y sesiones de
Cowork como referencia — ver siguiente sección.

---

## Backup del "cerebro de los agentes" (YA ANDANDO)

Se **sumó al cron diario** que ya corre (13:00). Cada día, además del backup de datos, el server
**hala de la Mint** (rsync, read-only sobre la Mint, con la clave `id_backup`) la parte durable:

- `~/.config/Claude/local-agent-mode-sessions/` (sesiones Cowork + memorias Cowork)
- `~/.config/Claude/claude_desktop_config.json` + `config.json` (config MCP)
- `~/.claude/projects/*/memory/` (memorias del CLI — 22 .md del proyecto Nextango)

**Destino:** `/home/costa/backups/agentes-mint-<ts>/` en el **SERVER** (queda **fuera** de la
Mint). Retención: últimos 10. **Primera corrida verificada:** 2 sesiones Cowork, MEMORY.md de
Cowork y de CLI presentes, config MCP incluida, 27 MB.

> Nota: excluye las 490 MB de caches y el estado cifrado (no sirven en otra máquina).

---

## Procedimiento de recuperación (realista, paso a paso)

Si la Mint muere y se arma una máquina nueva:

1. **Instalar Claude Desktop + Cowork** en la máquina nueva e **iniciar sesión** con la cuenta
   (costaratti@gmail.com). Esto crea un dispositivo nuevo — es normal.
2. **Reponer la config MCP:** copiar del backup `agentes-mint-<ts>/config-Claude/claude_desktop_config.json`
   a `~/.config/Claude/` (así vuelven los conectores/MCP). Revisar rutas/credenciales.
3. **Clonar el repo** (trae TODO el cerebro durable de una):
   `git clone -b main https://github.com/costaratti85/NexTango.git` → `coordination/` con roles,
   DECISIONs, canon, `queue.json`, reportes, briefs. (Y la rama `erpnext` para el código.)
4. **Restaurar las memorias:**
   - CLI: copiar `agentes-mint-<ts>/claude-projects-memory/<proyecto>/memory/` a
     `~/.claude/projects/<proyecto>/memory/`.
   - Cowork: las memorias de Cowork están dentro del backup de `local-agent-mode-sessions/…/agent/memory/`;
     reponerlas en la carpeta equivalente de la instalación nueva.
5. **Reconstituir el equipo:** abrir Cowork y **relanzar cada agente desde su brief/rol** de
   `coordination/agents/` + los handoffs de `coordination/channel/<Agente>/`. El agente "arranca"
   leyendo su rol, el canon (DECISIONs) y su memoria — no hace falta que "reviva" la sesión vieja.
6. **Verificar Tango/deploys:** que `server-t` resuelva y las credenciales estén (ver
   `PROGRAMA.md` / `DATOS.md`). Para los datos de ERPNext, es otro backup (el de `DATOS.md`).

**Qué se pierde igual (aceptado):** el hilo exacto de las conversaciones vivas y el estado de la
app. **Qué NO se pierde:** el conocimiento, las decisiones, las memorias y el rol de cada agente.

---

## Resumen de una línea para Constantino
> Los agentes **no** viven en la Mint: su cerebro está en **GitHub** (`coordination/`) + las
> **memorias**, y ahora ambas cosas están **respaldadas fuera de la Mint** (backup diario al
> server). Si la Mint muere: máquina nueva → instalar Claude Desktop + login → clonar el repo →
> reponer memorias → relanzar cada agente desde su rol. **No** se "resucita" la sesión vieja tal
> cual, pero se **recupera todo lo que importa**. Pendiente: pushear los **265** archivos de
> `coordination/` que hoy están solo en la Mint (18 son DECISIONs).
