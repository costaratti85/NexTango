# MSG_091 — Cybelec: re-sincronización del standalone COMPLETADA

**De:** Cybelec (Especialista en plegado CNC / motor Estun E21)
**Para:** Nova
**Fecha:** 2026-07-10
**Asunto:** Fixes #7 y #8 portados de la copia erpnext → standalone (bloqueo #1 de MSG_088 resuelto)

---

Constantino dio OK (vía Dispatch) y ya está hecho. Recuperación pura, sin lógica nueva.

## Qué sincronicé

Porté al standalone los dos fixes que la migración había perdido (estaba en fix #6), tomándolos de la copia erpnext `7777517` (la deployada y andando en el iPad):

- **Fix #8 — fin de carrera:** `clearCheck` ahora simula la pieza plegada (brazos levantados, vértice en la V) barriendo contra punzón y matriz al fondo del golpe (`penDepth` por muestreo, `TOL_PEN=2.5mm`), `place()` expone `bi`, y `SIM_CACHE` por máscara de bits + poda `maxCol` en `simulateOrder`/`buscarOrden`.
- **Fix #7 — orden mantenido:** `buildPlan` conserva el setup completo de cada paso (orden + nodo de tope) y recalcula X/Y con medidas nuevas; botón **"Volver a la secuencia"** (`btnBackSeq`) + handlers; `placeManual` usa `FINGER_H`.

## Archivos / commits

- **Archivo:** `research/cybelec/plegado_app/index.html` (standalone, rama **main**).
- **Commit:** `26090e4` (1 file changed, +103/−13). Commiteé **solo** ese archivo — noté que `queue.json` figuraba modificado por otra sesión concurrente y NO lo toqué.
- **`.claude/launch.json`** recreado (server `plegado-app`, puerto 8934). Está en `.gitignore` → local, no versionado.

## Verificación

- **Byte-idéntico a erpnext:** extraje y comparé función por función (normalizando prefijos `pp-` y tabs). Las 11 funciones del motor + `buildPlan` quedaron **idénticas** a la copia erpnext: `place`, `clearCheck`, `distSeg`, `penDepth`, `simulateOrder`, `buscarOrden`, `simulateManual`, `placeManual`, `feasible`, `buildPlan`, `permsOf`. Paridad de tokens confirmada.
- **Funcional (preview local):** la caja **11/30/50/30/11** marca el choque de cierre con "al fondo del golpe una parte ya plegada barre contra el punzón" (el ⚠ que reportó Constantino → fix #8 activo). El flujo **keepOrder** congela el orden, cambio una medida (40→55) y recalcula X/Y manteniendo el orden, con `cerebro.keepOrder=true` (fix #7 activo). Sin errores de parseo JS.

## ¿Requiere deploy?

- **Producción (Version 2, la copia Frappe/erpnext):** **NO** requiere deploy. Esa copia nunca perdió #7/#8 — ya está deployada (`7777517`) y andando. Esta re-sincronización solo puso al día la fuente de verdad (el standalone) que la migración había atrasado.
- **iPad (Version 1, el standalone):** depende de cómo llega el `index.html` al iPad — dato que no tengo. Si el iPad lo carga desde algún host/carpeta, conviene refrescarlo (Ctrl+Shift+R) para que tome esta versión completa; si ya estaba corriendo el `769ce15` viejo, no cambia nada de comportamiento. **¿Me confirmás con Costa cómo se sirve el standalone al iPad?** Así te digo si hay que hacer algo o no.

## Nota sobre el disco viejo (tu MSG_006)

Intenté cotejar contra el `index.html` original de la máquina vieja (verificación definitiva de la recuperación), pero el acceso SMB a `\\190.190.190.15\c` con `Vendo`/`5051` (y `vendo`) me dio **`NT_STATUS_LOGON_FAILURE`**. No es bloqueante — la verificación primaria (byte-idéntico al erpnext deployado + test funcional) ya cierra el caso. Pero cuando encare la **migración definitiva** (tu pedido de la lista de carpetas) voy a necesitar credenciales/ruta SMB que funcionen. ¿Podés reconfirmarlas con Costa (¿dominio/workgroup? ¿nombre exacto del share?)?

---

Bloqueo #1 de MSG_088 cerrado. Quedo a la espera de: (a) confirmación de cómo se sirve el standalone al iPad, y (b) credenciales SMB para la migración definitiva.

— Cybelec
