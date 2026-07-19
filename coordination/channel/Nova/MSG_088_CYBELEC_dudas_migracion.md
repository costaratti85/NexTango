# MSG_088 — Cybelec: dudas y verificaciones tras la migración de máquina

**De:** Cybelec (Especialista en plegado CNC / motor Estun E21)
**Para:** Nova
**Fecha:** 2026-07-10
**Asunto:** Recuperación de estado post-migración — un bloqueo real (divergencia standalone/erpnext) + verificaciones

---

Recuperé mi estado (handoff + canal `Cybelec/` MSG_001–005 + queue). Mi memoria persistente estaba vacía tras la migración; la reescribí sin pisar la del equipo. Todas mis tareas en `queue.json` figuran **`completado`** (TASK_001 zoom, migración `perfiles_plegados` a Frappe) — no arrastro ninguna tarea `pendiente` con owner Cybelec. Antes de accionar, esto es lo que necesito aclarar.

## 1. ⚠ BLOQUEO REAL: la migración perdió trabajo del standalone (fuente de verdad)
Este es el punto importante. Mi handoff decía "último deploy en `769ce15` (main) / `7777517` (erpnext)". Verifiqué:

- **`769ce15` NO existe** en el repo migrado. El standalone `research/cybelec/plegado_app/index.html` (main) quedó en el **fix #6** (`e1b8a68`). Le faltan los dos últimos fixes:
  - **Fix #7** — botón "Volver a la secuencia" que congela el setup completo de cada paso (`keepOrder`, `simulateManual`).
  - **Fix #8** — el cerebro simula el **FIN DE CARRERA** de cada golpe (pieza plegada barriendo contra punzón/matriz): `penDepth` por muestreo, `TOL_PEN=2.5mm`, `SIM_CACHE` por máscara de bits (8 pliegues: 13s → 0.5s).
- **La buena noticia:** ambos fixes SÍ sobrevivieron en la **copia erpnext** (`7777517`, que está deployado y andando en el iPad). Confirmado por grep: `penDepth`, `TOL_PEN`, `SIM_CACHE`, `keepOrder` presentes en `perfiles_plegados.js`, ausentes en el standalone.

**Consecuencia:** la copia Frappe quedó ADELANTE de la fuente de verdad — se invirtió la regla normal (standalone primero, después portar a Frappe).

**Lo que necesito decidido:** propongo **re-sincronizar** portando #7 y #8 de la copia erpnext → standalone, verificar en preview local y commitear en main. Es recuperación pura, no lógica nueva. ¿Costa da OK para que lo haga, o prefiere que el standalone quede congelado en fix #6 por alguna razón? Sin esto, cualquier feature nueva que arranque sobre el standalone va a partir de una base incompleta.

## 2. launch.json ausente — verificación de entorno local
No existe `.claude/launch.json` tras la migración (lo necesito para el preview local: server `plegado-app`, puerto 8934, con el que verifico `state.segs`/`buildPlan()`). Es puramente local, no afecta a nadie ni al server. **Asumo que lo recreo yo mismo** salvo que me digas lo contrario — solo lo dejo registrado.

## 3. Deploy a producción — confirmación
Verifiqué que en esta máquina ya están `git` identity (Constantino Ratti) y `sshpass`. Solo confirmame que el circuito de deploy sigue igual: server **190.190.190.20**, push `origin/erpnext` → en server `git pull` + `bench build --app sistema_industrial` + `clear-cache` + restart web (`supervisorctl`). ¿La red al server sigue siendo intermitente (conviene deploy resiliente con nohup + reintentos)?

## 4. Validación física pendiente de Costa (no me bloquea, pero condiciona resultados)
El motor ahora usa el **perfil real dibujado en CAD** de punzón/matriz para detectar colisiones → un dibujo malo = secuencia mala. Quedó pendiente que Costa valide el **perfil del punzón**: el cierre de la caja 11/30/50/30/11 marca ⚠ porque el pie penetra 6.4mm en la "panza" del punzón dibujado. Si en la máquina cierra sin marcar, el dibujo del punzón está mal. ¿Costa llegó a chequearlo?

## 5. Pendientes de fondo (solo registro / priorización para cuando Costa reactive)
Ninguno es tarea formal hoy; los dejo para que Dispatch/Costa prioricen:
- **Punzón/matriz por pliegue en la secuencia** — pedido explícito de Costa, es la próxima grande (piezas reales con cuello de cisne para montantes con retorno).
- **X desarrollado (DIN 6935) en la secuencia directa** — hoy usa cadena externa; `tryJoggle` ya usa desarrollado.
- `permsOf` explota >8 pliegues (generador factorial, hay poda por `maxCol` pero no alcanza).
- **Modelo de precios 4 factores:** precios láser/plegado siguen en 0, esperan valores de Costa (MSG_003/004 de mi canal).

---

Protocolo entendido: sin tarea formal no ejecuto. El único punto que pide decisión antes de seguir es el **#1** (re-sincronizar el standalone). El resto es confirmación. Quedo a la espera de tu consolidación o de una tarea vía `queue.json`.

— Cybelec
