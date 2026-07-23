# ☀️ Brief de la mañana — 2026-07-22

**Para:** Constantino (leelo de un saque) · **De:** Nova
**La noche:** equipo en **modo investigación** (solo relevamiento/specs/propuestas; nada irreversible). Reglas en `coordination/dispatch/MODO_INVESTIGACION_NOCTURNA.md`.

> Este brief se llena con lo que los agentes reporten durante la noche. Lo de abajo es el marco + lo que ya está firme; las secciones marcadas ⏳ se completan con sus entregas.

---

## 🟡 LO PRIMERO — ratificá (o descartá) un cambio de canon acotado

**Propusiste un SPLIT del máster de artículos por prefijo de código:**

| Segmento | Código | Máster propuesto |
|---|---|---|
| **Ferretería** (comercial) | **`06-`** | → **ERPNext** (sync ERPNext→Tango vía Excel plantilla) |
| Caños, chapas, procesado | otros | **Tango** (sin cambios) |

Lo dijiste con **"creo que"**, así que sigue como **PROPUESTA, no lo asenté.** Pero con la aclaración de hoy es **mucho menos riesgoso** de lo que parecía anoche: **no invertís todo el catálogo**, solo el segmento de **ferretería (~50 artículos)** — que es tu área comercial y la que alimenta el OCR de proveedores. Es quirúrgico y coherente.

**Sigue exigiendo tu palabra** (es cambio de fuente de verdad, aunque chico), pero el riesgo es acotado: 50 items, no 2.189; el resto del catálogo intacto.

**Lo único que necesito:** ¿**confirmás** el split `06-`→ERPNext?
- Detalle + mapa de qué se toca si confirmás: `coordination/decisions/PROPUESTA_INVERSION_MASTER_ARTICULOS.md`.
- Forge ya está **diseñando** el export ERPNext→Tango **acotado a `06-`** (propuesta, no ejecuta nada).

---

## 🟢 TL;DR (10 líneas)

1. Noche de **pura investigación** — cero deploys, cero datos, cero Tango.
2. **Token de Tango:** ✅ **el repo está LIMPIO** (falsa alarma del OCR: eran GUIDs de sesión, no el token → **sin exposición en GitHub, sin reescribir historia**). Ya limpiado `/home/costa/Python`. En limpieza `~/Claude/*` (la exposición real). **Dos decisiones tuyas:** backups y `audit.jsonl` (§1/§6).
3. **OCR proveedores:** reactivado + **re-encuadrado** — ahora vive **dentro de ERPNext** (página web), no en tu máquina. Plan por fases ⏳.
4. **PedidoExcel:** spec de los **dos bloques copiar/pegar** (presupuesto + OT) ⏳. El copiar/pegar es lo prioritario; modificar el Excel es mediano plazo.
5. **Artículos ERPNext:** ya hay **2.189 cargados** con Tango ID (estado firme, explicado abajo).
6. **Backup automático a la Mint** (Orbit) ⏳.
7. **Trabado esperándote:** deploy del **centrado de patrones** (OK visual tuyo) + varias decisiones (abajo).

---

## 1. 🔑 Token de Tango — barrido consolidado

**Autorizado:** limpiar el token en texto plano (no lo podés rotar).

### ✅ La mayor preocupación quedó DESCARTADA — el repo está limpio

El agente OCR había avisado que el token estaba en el repo Nextango (working-tree + 9 commits + GitHub). **Era FALSA ALARMA.** Atlas hizo un barrido preciso (match **exacto** del valor) y confirmó:

> **El repo está LIMPIO — cero rastros del token en todos los árboles y en TODA la historia de git, en todas las ramas.**

Lo que el OCR había marcado eran **IDs de sesión (GUIDs)** confundidos con el token — no el token. **Consecuencia:** **no hay exposición en GitHub vía el repo**, y **NO hace falta reescribir historia** (que era el punto delicado que temíamos). Descartado.

### ✅ Ya limpiado

- **`/home/costa/Python`** (OCR Proveedores + OCR Mercadopago) — barrido por OCR. Hecho.
- **Repo Nextango** — ya estaba limpio (ver arriba).

### 🔄 En limpieza ahora (OCR)

- **`~/Claude/*`** — scripts Tango con el token **hardcodeado**. **Esta era la mayor exposición REAL.** Redacción a variable de entorno.
- **`~/SistemaIndustrial/Migrando Claude/`** — notas.
- **Sin dejar `.bak`** con el valor (redacción limpia, no copia de respaldo con el secreto).

### ⏳ DOS decisiones para vos (NO se tocó — ver §6)

1. **Backups** (`~/backups/nextango-*/frappe-bench-nexus.env`) — tienen el token en texto plano, pero es **legítimo**: hace falta para restaurar. **Mitigación = asegurar/encriptar el backup, no vaciarlo.** Dominio Orbit.
2. **`audit.jsonl`** (logs de sesión) — tienen el token y **no son removibles fácilmente**. Decisión tuya de qué hacer.

**Estado del token en sí (recordatorio):** sigue **vivo y sin rotar** en `/etc/environment`, `/etc/frappe-bench-nexus.env` y el `.env` de la Mint. Todo esto es limpieza de **rastros en texto plano**, no rotación.

---

## 2. 🔦 OCR proveedores — reactivado y re-encuadrado

**Estado real que preguntaste:** el rol **OCR** estaba **formalizado** (`DECISION_016`) y en **pausa** (activación diferida). **No lo tenía ningún agente trabajando.** El satélite "OCR Mercadolibre" existió pero sin canal propio. **Lo reactivé:** canal `coordination/channel/OCR/` creado, agente asignado.

**Cambio de arquitectura (tuyo):** el OCR **ya no corre en tu máquina** → se instala **dentro de ERPNext como una página web más**. Se parte en:
- **Motor server-side** (lógica de OCR/parsing en el server).
- **UI web de Frappe** (la arma Vega).
- **Portar** la lógica de `/home/costa/Python/OCR Proveedores` a ese destino (no reusar el script de escritorio tal cual).

**Investigación de la noche (solo lectura):** relevar las dos carpetas y proponer el **plan por fases** re-encuadrado:
- `/home/costa/Python/OCR Proveedores` — factura proveedor → precio de compra a **Excel** → artículo nuevo a **Tango** (catálogo) → luego **stock a ERPNext**.
- `/home/costa/Python/Baja de Stock en ERPnext al facturar en Tango` — baja de vendidos escaneando facturas de Tango.

⏳ *Plan por fases del OCR — se completa con el reporte del agente.*

---

## 3. 📋 PedidoExcel — spec de los dos bloques copiar/pegar

**Re-scope (tuyo, registrado):** por ahora **NO** se modifica el Excel desde el programa (mediano plazo). Lo inmediato = **pantalla ERPNext con 2 bloques copiar/pegar**: uno al **presupuesto**, otro a la **OT**. Flujo: generar pedido → copiar → pegar a mano.

- **PedidoExcel** define el **spec** (campos, orden, formato de cada bloque).
- **Vega** arma la pantalla — **espera el spec aprobado** antes de construir.
- **Prioridad:** el copiar/pegar. Modificar el Excel queda para después.

⏳ *Spec de los dos bloques — llega como propuesta para que apruebes antes de que Vega construya.*

---

## 4. 📦 Carga de artículos a ERPNext — estado (firme)

Ya está hecho y verificado (no requiere acción):
- **2.193 Items totales; 2.189 con Tango ID.** El push `tango_sync/article_push.py` (idempotente, clave = código Tango) los cargó y sigue intacto.
- **Reparto:** Tubos y Perfiles 1.564 · Insumos 219 · Materiales 188 · Chapas y Flejes 168 · **Ferretería 50**.
- Marcados `is_stock_item=0` (sin stock aún — el stock es lo que traería el OCR/flujo de compras).
- Detalle menor a ordenar algún día: algunos Item Groups "padre" quedaron con `is_group=0`.

**Para vos:** los artículos están; lo que falta para "ferretería" completa es el **flujo de stock** (que engancha con el OCR de proveedores). Por eso los dos frentes se tocan.

> 🟡 **Relacionado:** tu propuesta de split toca solo la **Ferretería (50 items, prefijo `06-`)** — no los 2.189. Si se confirma, el máster de esos 50 pasa a ERPNext y se empujan a Tango. El resto del catálogo, sin cambios. Propuesta hasta tu ratificación.

---

## 5. 💾 Backup automático a la Mint (Orbit)

⏳ *Estado del backup automático — se completa con el reporte de Orbit.* (Contexto: ya había un backup real en `/home/costa/backups/nextango-20260722_044914`; lo de la noche es automatizarlo/copiarlo a la Mint.)

---

## 6. ⏳ DECISIONES QUE TE ESPERAN (para aprobar a la mañana)

| # | Decisión | Dónde |
|---|---|---|
| 0 | 🟡 **RATIFICAR o descartar: split del máster de artículos — ferretería `06-` → ERPNext** (resto Tango, ver arriba) | `PROPUESTA_INVERSION_MASTER_ARTICULOS` |
| 1 | **Deploy del centrado de patrones** — trabado esperando tu **OK visual** (antes/después de Punto) | `PUNTO_CENTRADO_AL_GUARDAR_PATRONES` |
| 2 | **PedidoExcel: VBA vs módulo Python** para el push a Tango (el agente recomienda Python) | `DECISION_018` |
| 3 | **PedidoExcel: dónde vive el código de cliente** (F19 vs E18) | (directo al agente) |
| 4 | **Spec de los 2 bloques copiar/pegar** — aprobar antes de que Vega construya | ⏳ §3 |
| 5 | **Plan OCR re-encuadrado** — aprobar antes de portar nada | ⏳ §2 |
| 6 | **Propuesta dos carriles + deprecar Python** — la estabas pensando | `PROPUESTA_DOS_CARRILES_Y_DEPRECAR_PYTHON` |
| 7a | **Token en backups** (`~/backups/*/frappe-bench-nexus.env`) — asegurar/encriptar el backup (Orbit), no vaciarlo | §1 |
| 7b | **Token en `audit.jsonl`** (logs de sesión) — no removible fácil: qué hacemos | §1 |
| 8 | **Mediciones CypCut** (Corazón/Gotas/Cosmos) — destraban el experimento de Punto | `PUNTO_REDISENO_EXPERIMENTO_VALIDACION` |
| 9 | **Licencia "Transacciones Tango Ventas"** — desbloquea el push a Tango de PedidoExcel | `DECISION_018` §5 |

---

## 7. 🔒 Lo que sigue TRABADO / en pausa (no se tocó de noche)

- **Deploy del centrado de patrones** — trabado hasta tu OK visual (regla dura).
- **Lechu (MES)**, **Nido (compilador de lote)**, **Tango (15 renames)** — en pausa (carril largo plazo).
- **Push a Tango de PedidoExcel** — bloqueado por licencia.
- Nada se deployó, nada se cargó, nada fiscal se tocó.

---

*Fin del marco. Las secciones ⏳ se completan durante la noche con los reportes de OCR, PedidoExcel, Atlas y Orbit.*
