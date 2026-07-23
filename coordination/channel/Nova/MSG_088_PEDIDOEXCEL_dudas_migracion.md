# MSG_088 — PedidoExcel: dudas y bloqueos tras la migración de máquina

**De:** PedidoExcel (sesión satélite — Cargar pedido a Tango vía presupuesto Excel)
**Para:** Nova
**Fecha:** 2026-07-10
**Asunto:** Recuperación de estado post-migración — bloqueos, decisiones a ratificar y verificaciones antes de accionar

---

Recuperé mi estado desde el handoff (`Migrando Claude/Cargar pedido a facturar en Tango a traves de presu excel.txt`) y revisé el repo. Soy sesión satélite: sin canal propio ni cola de tareas. **No acciono nada** hasta que consolides. Objetivo del flujo: un botón en el presupuesto Excel que crea Pedidos directamente en Tango Gestión (proceso 19845 / GVA21), eliminando el copy-paste manual. Te dejo lo que necesito destrabar, ordenado por criticidad.

## 1. 🔴 BLOQUEANTE — Los archivos de trabajo no migraron a esta máquina
Todo el laburo del flujo vivía en la ruta Windows `C:\Users\vendo\OneDrive\Documentos\Costa\Claude\`:
- `TangoAPI_VBA.bas` (módulo VBA principal, con la lógica de resolución de IDs y armado del pedido — el ~70% "inteligente" ya construido)
- `TangoAPI.xlam` (add-in Excel)
- `PRESUPUESTO_PLANTILLA.xlsm` (plantilla)
- `fix_plantilla.py` (formato condicional)

Esta máquina es **Linux** y **ninguno de esos archivos está acá** (busqué en todo `~/SistemaIndustrial`). Sin ellos no puedo continuar el enfoque VBA/Excel. **Necesito decisión de Costa:** ¿recuperamos esos archivos (traerlos a esta máquina / OneDrive accesible) o **reencaramos el flujo como módulo Python versionado en el repo**? Ver punto 2.

## 2. 🟠 DECISIÓN DE ARQUITECTURA — ¿VBA externo o Python en el repo?
El repo tiene `apps/sistema_industrial/sistema_industrial/tango_sync/` con `customer_push.py` y `article_push.py`, pero **no hay push de Pedidos** todavía. Dos caminos:
- **(A) Seguir con VBA/Excel** — recuperando los `.bas`/`.xlam`. Rápido para Costa (botón en Excel), pero no versionado, no testeable, atado a Windows.
- **(B) Reescribir como `tango_sync/pedido_push.py`** en el repo — testeable, versionado, coherente con `customer_push`/`article_push`. El Excel quedaría como front (o se dispararía por otra vía).

Mi recomendación es **(B)** para que quede en el repo y con tests, reusando `http_client.py`. Pero es una decisión de Costa porque cambia la experiencia de uso (botón en Excel vs. otro disparador). **¿Cuál priorizamos?**

## 3. 🔴 BLOQUEANTE FUNCIONAL — Licencia "Transacciones Tango Ventas"
Mi handoff registra que la licencia actual es solo **"ABMs y consultas Live"**; para **crear** Pedidos por API hace falta la licencia **"Transacciones Tango Ventas"**, que estaba **pendiente de contratar**. Sin ella el POST de pedidos va a devolver error de permiso, se prueba lo que se pruebe. **¿Se contrató ya?** Si no, puedo dejar el código listo pero no probar el POST real contra Tango.

## 4. 🟠 Token / entorno — nada configurado en esta máquina
- El código canónico usa `APP_INSTANCE_ID` (env var) como header `ApiAuthorization`, `Company` en header, `TANGO_URL`, `TANGO_COMPANY=25`. Verificado en `http_client.py`.
- Mi handoff traía un token **hardcodeado** (`<APP_INSTANCE_ID>`) — asumo que quedó **obsoleto** por el cleanup de token (canónico ahora `APP_INSTANCE_ID`, no hardcode). **Confirmame** que ese token del handoff ya no se usa.
- En esta máquina **no hay** `APP_INSTANCE_ID`, `TANGO_URL` ni nada en el entorno (verificado con `env`). ¿La nueva máquina ya tiene el entorno replicado, o eso es de Forge todavía? Y **¿`server-t:17000` es alcanzable desde esta Linux en la red local?** Sin esto no puedo correr ni los probes.

## 5. 🟡 Constantes del pedido — ¿tenemos los IDs reales?
Para armar el JSON del Pedido faltan IDs que `tools/probe_tango_constants.py` está pensado para descubrir, pero **no sé si llegó a correrse** ni con qué resultados:
- **CondicionVenta** (proc 2497) — ¿cuál es la habitual de la empresa (contado / 30 días)?
- **ListaDePreciosVentas** (proc 984) — ¿número de lista principal?
- **Moneda** (proc 1660) — ID de ARS.
- **Deposito** (proc 2941) — ¿cuál para los pedidos?
- **Talonarios**: handoff dice A=31, B=34. **¿Siguen vigentes?**

¿Existen ya esos IDs consolidados en algún lado (doc/mensaje), o los tengo que descubrir corriendo el probe una vez que tenga entorno (punto 4)?

## 6. 🟡 Detalles de UI de la plantilla (por si seguimos con Excel)
Del handoff, decisiones que no están en ningún archivo del repo y quiero ratificar:
- Dropdown A/B (talonario) está en **celda D5** (merge D5:D10), no en AC2.
- CONFIG y MAPEO deben vivir en el **`.xlam`** (no en cada presupuesto). El bug pendiente era `ActiveWorkbook.Sheets(...)` → `ThisWorkbook.Sheets(...)`.
- `GetByFilter` no soporta `LIKE` (hay que paginar y filtrar en código); usa `filtroSql=WHERE%20...`.

Estos los aplico yo si vamos por (A); solo confirmá que siguen válidos.

## 7. 🟢 Dónde versiono mi trabajo y cómo reporto
Soy satélite sin cola. **¿Dónde dejo lo que produzca?** ¿Creo `tango_sync/pedido_push.py` + tests en `main` y te reporto por este canal, o querés que trabaje en un worktree/rama aparte? ¿Abro carpeta de canal propia o sigo escribiéndote siempre acá?

---

Prioridad para destrabar: **puntos 1, 2 y 3** (sin eso no hay flujo). El resto es verificación/ajuste. Quedo a la espera de tu consolidación o de una decisión de Costa.

— PedidoExcel
