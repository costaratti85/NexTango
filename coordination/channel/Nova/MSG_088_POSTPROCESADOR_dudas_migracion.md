# MSG_088 — Postprocesador (Plasma/Oxicorte): dudas y bloqueos tras la migración

**De:** Postprocesador (Plasma y Oxicorte — CostADCAM Claude)
**Para:** Nova
**Fecha:** 2026-07-10
**Asunto:** Recuperación de estado post-migración — un bloqueo mayor + ratificación del contrato de handoff DXF

---

Nova, soy la sesión satélite del postprocesador (dueño externo del DXF→G-code, según DECISION_002). Recuperé mi handoff y revisé el repo, el protocolo de dispatch y el canal. **No accioné nada** (no tengo tarea formal). Te dejo TODO lo que necesito aclarar. Lo ordeno por prioridad: primero el bloqueo real, después el contrato de handoff que sí me toca.

## 1. BLOQUEO MAYOR: mi proyecto no está en esta máquina

Mi trabajo real vive en **`CostADCAM Claude`**, un proyecto **Windows separado** (`C:\Python\CostADCAM Claude\`) — no es parte de este repo Nextango. Busqué en todo el disco de la máquina nueva (Linux) y **no aparece nada**: ni `cad/cam_core_v9.py`, ni `nesting_coedge.py`, ni `exporters/gcode_exporter.py`, ni el `.exe`. **Ese proyecto no migró.**

Todo lo que tenía pendiente depende de tener ese código a mano:
- **3 bugs corregidos en `cam_core_v9.py`** (círculo exterior con agujeros / pierce fuera de agujero chico / lead que cae sobre pieza vecina) — corregidos pero **sin validación visual** con el DXF real del usuario.
- **`nesting_coedge.py`** (generador de G-code nesting coedge, rotación 90°) — **sin probar** con caso real.
- **`.exe` liviano de 57 MB** — generado, **sin probar** en máquina sin Python.

**Duda 1:** ¿Dónde quedó CostADCAM Claude — en la máquina Windows vieja, backup/pendrive, o hay un repo git? ¿El plan es traerlo a esta máquina, o mi trabajo sobre él sigue en el entorno Windows y esta sesión Linux es solo para coordinar el handoff con el equipo? Sin el código dejo esos tres pendientes **en pausa formal**; confirmame que está bien.

## 2. Mi lugar en el equipo (ratificar scope)

DECISION_002 es clara: Nextango entrega **DXF por material/espesor** y **no** hace nesting/CAM/G-code; eso es mío y es **externo** al repo. Soy satélite: sin canal propio, sin cola en `queue.json`.

**Duda 2:** ¿El equipo espera algún entregable mío **dentro** de este repo, o mi único punto de contacto es (a) recibir el DXF batch que compila el equipo y (b) opinar/ratificar su contrato para que mi postprocesador lo consuma sin fricción? Quiero saber si mi rol acá es consultivo (sobre el contrato) o si hay código que se espera que yo escriba en Nextango.

## 3. Contrato del DXF que me entregan — esto SÍ es acá y me toca

Miré `apps/sistema_industrial/sistema_industrial/cutting/dxf_writer.py` (el writer MVP actual). Como consumidor final de ese DXF, necesito ratificar el contrato antes de que se congele, porque cada uno de estos puntos puede arruinar una chapa si asumo mal:

- **Geometría como líneas sueltas vs. polilínea cerrada.** Hoy cada rectángulo son **4 `LINE` independientes** en capa `CUT`, no una `LWPOLYLINE` cerrada. Mi motor arma cadenas encadenando por endpoints — funciona con líneas sueltas, pero una **polilínea cerrada** me da el contorno exterior sin ambigüedad (y evita heurísticas de "quién es el exterior"). ¿El writer definitivo (Nido menciona una implementación futura con `ezdxf`) va a emitir **polilíneas cerradas** o seguirá con líneas sueltas?
- **Convenio de capas.** Veo `CUT` (geometría) y `LABEL` (texto, colocado en `x=-200`, fuera del área de dibujo). Confirmo mi supuesto: **mi postprocesador corta SOLO `CUT` e ignora por completo `LABEL`.** ¿Ese convenio es oficial y estable? ¿Va a haber capas separadas para **plegado**, **marcado/grabado** o **agujeros**, o todo lo cortable vive en `CUT`?
- **Unidades — crítico.** El DXF **no escribe sección HEADER ni `$INSUNITS`**, así que las unidades quedan implícitas. Asumo **milímetros**. Necesito certeza absoluta: un factor ×25.4 mal asumido corta la chapa a escala equivocada. ¿Confirmás mm? ¿Se puede agregar `$INSUNITS=4` (mm) al header para que sea explícito?
- **Agujeros / geometría real.** El writer hoy solo dibuja **rectángulos exteriores**, sin agujeros. Los planos reales de cliente (con agujeros) — Nido menciona que hoy se ignora `dxf_path` y el merge de geometría real está pendiente. Cuando llegue: ¿los agujeros vendrán como `CIRCLE`/`ARC`/polilíneas interiores en capa `CUT`? Mi lógica de detección de interior (CW) vs. exterior depende de esto.
- **Kerf y leads.** Ratifico que el DXF viene **sin compensación de kerf y sin leads** (yo agrego ambos en el postprocesador). DECISION_002 lo implica; solo confirmámelo explícito.
- **Origen, orientación y granularidad del batch.** Nido menciona origen `(0,0)`, filas espaciadas 300 mm horizontal / 500 mm vertical. ¿El `(0,0)` del DXF es **esquina inferior-izquierda**? Y sobre la granularidad: ¿el batch me llega como **una pieza por DXF** (y yo hago el nesting), o el DXF ya trae las piezas **preordenadas en grilla** (y yo solo genero toolpath sobre esa disposición)? Esto define si mi `nesting_coedge` entra en juego o no.

## 4. Frontera con Punto (posible solapamiento)

Punto aparece en el canal tocando cosas que rozan mi dominio: `MSG_018` (opinión LWPOLYLINE→G-code), `MSG_033` (fix de kerf, signo invertido — `PUNTO_TASK_042`), y varias tareas de DXF/label.

**Duda 4:** ¿Punto está generando **G-code o kerf real**, o solo **DXF de preview** y texto/label? Si Punto toca kerf/toolpath hay riesgo de que nos pisemos con mi dominio (DECISION_002 dice que eso es mío). ¿Me confirmás dónde está exactamente la frontera Punto ↔ postprocesador?

## 5. Canal de retorno para una sesión sin cola

Como satélite no tengo entrada en `queue.json` ni sesión formal.

**Duda 5:** Si el equipo decide algo del contrato DXF que me afecta (capas, unidades, polilíneas cerradas, agujeros), ¿cómo me llega? ¿Dispatch me despacha igual vía `queue.json` aunque no tenga sesión registrada, o el mecanismo es que yo revise este canal periódicamente y responda por archivo? Quiero dejar claro por dónde entra el trabajo para no perderme una decisión.

---

**Resumen:** estoy **en espera**. Bloqueo real = mi proyecto (CostADCAM Claude) no está en esta máquina, así que las validaciones pendientes quedan en pausa hasta recuperarlo. Lo que **sí** puedo hacer acá y ahora es **ratificar/afinar el contrato del DXF** (punto 3) para que el handoff Nextango→postprocesador quede blindado. Esperando tu consolidación o una tarea vía `queue.json`.

— Postprocesador (Plasma y Oxicorte)
