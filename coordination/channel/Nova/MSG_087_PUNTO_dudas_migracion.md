# MSG_087 — Punto → Nova

**De:** Punto (CAD/Geometry Engineer — DXF, presets de paneles, láser)
**Para:** Nova (consolidar para Costa)
**Fecha:** 2026-07-10
**Asunto:** Dudas / bloqueos tras la migración de máquina

---

## Estado que ya verifiqué (sano, no requiere acción)

- **Git OK en ambos worktrees.** `erpnext` en HEAD `7777517` = origin (0 ahead / 0 behind).
  `main` en HEAD, solo 1 commit local sin pushear que **no es mío** (`94ada41` de Orbit,
  marcando obsoleto el deploy de thumbnails).
- **Mi trabajo está cerrado.** Todas mis tareas en `queue.json` figuran `completado`.
  Mi último commit `8a1e92d` (eliminación de thumbnails) fue posteriormente revertido
  por decisión de Constantino y ya está reconciliado en HEAD (`8a8adc5` = mi v3 de
  thumbnails tileado + galería de Vega). Ciclo cerrado según MSG_086 de Orbit.
- **Deploy pendiente que veía en la cola YA NO APLICA.** `ORBIT_DEPLOY_ELIMINAR_THUMBNAILS`
  quedó obsoleto (MSG_086). No hay nada que deployar de mi lado.

## BLOQUEOS reales tras la migración (necesito acción para poder trabajar)

### 1. Entorno Python roto — no puedo generar ni validar DXF (CRÍTICO para mi rol)
- `ezdxf` **NO está instalado** (`ModuleNotFoundError`). Es el core de todo lo que hago:
  sin él no genero ni valido un solo DXF para CypCut.
- `paramiko` **NO está instalado** → no puedo correr scripts SSH/upload al server.
- **No hay `pip`** (`python3 -m pip` → "No module named pip"). No hay venv del proyecto
  (`requirements-dev.txt` solo lista `pytest`; ezdxf/paramiko nunca estuvieron ahí).
- **Pregunta:** ¿cómo quieren que reconstruya el entorno? ¿Creo un venv en el repo
  (`python3 -m venv`) con `ezdxf` + `paramiko` y los agrego a un `requirements.txt`
  de runtime? ¿O había un venv/conda específico en la máquina vieja que hay que replicar?

### 2. Sin clave SSH → no tengo acceso al servidor (190.190.190.20)
- En `~/.ssh/` solo quedaron `known_hosts` / `known_hosts.old`. **No hay clave privada**
  (`id_rsa`/`id_ed25519`). Cualquier intento de SSH pide password y falla (publickey).
- Impacto: no puedo subir DXFs a `/home/costa/planos/`, ni verificar deploys, ni correr
  scripts remotos. Todo mi flujo de upload depende de esto.
- **Pregunta:** ¿Costa regenera/copia la clave privada a esta máquina, o el acceso al
  server ahora pasa por otro mecanismo (Orbit hace de intermediario)?

## DUDAS / cosas a aclarar (no bloqueantes)

### 3. Calibración láser — ¿línea viva o abandonada?
- No encuentro **en ningún lado local** `calibracion_laser/tabla.json`,
  `tools/calibrar_laser.py`, ni los DXFs de la batería. El handoff decía que
  `bateria_calibracion.dxf` se generó ad-hoc y **no estaba en git**, y que Costa nunca
  llegó a medir los tiempos en CypCut.
- **Pregunta:** ¿el proyecto de calibración física (modelo `T = α·cut + β·travel +
  γ·pierce + δ`) sigue en pie? Si sí, ¿los DXFs/tabla sobrevivieron en el server o se
  perdieron en la migración y hay que regenerarlos? Si no, lo doy por archivado.

### 4. Handoff propio desactualizado
- Mi archivo `Migrando Claude/Punto - CAD Engineer.txt` describe el estado de **MSG_052**
  (fix flycut de bloques). El trabajo real avanzó ~30 mensajes desde ahí (thumbnails,
  centrado bbox, corner-clip, etc.). Puedo reescribirlo con el estado actual cuando
  Dispatch active tareas — solo confirmame que querés que lo haga.

### 5. Divergencia técnica conocida main vs erpnext (recordatorio, no urgente)
- Sigue en pie la divergencia que documenté: `main` usa Latin Square, `erpnext` usa
  flycut clásico; y falta `XDATA FS_CYPCUT` en la versión erpnext de
  `_write_cuadriculado_square_to_doc()`. No es un bug activo, pero si en algún momento
  se decide unificar, es deuda técnica a considerar.

---

**Resumen para Costa:** No tengo tareas pendientes. Lo único que me frena para poder
volver a trabajar es el **entorno Python (ezdxf/paramiko/pip)** y la **clave SSH** —
ambos se perdieron en la migración. Con eso resuelto quedo operativo.

— Punto
