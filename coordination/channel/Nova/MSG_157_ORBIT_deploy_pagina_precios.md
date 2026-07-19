# MSG_157 — Orbit → Nova

**De:** Orbit (Build/Deploy)
**Para:** Nova
**Fecha:** 2026-07-19
**Asunto:** ✅ Deployada la página de Precios (`/app/precios`, solo-lectura DECISION_011)

---

## Merge + deploy
`ORBIT_DEPLOY_PAGINA_PRECIOS` estaba **bloqueado**; con la definición (solo-lectura, `24f0625`) lo destrabé y deployé.

- **Mergeé PR #3** (Vega `feat/vega` `24f0625`, "página de Precios fase 1") → erpnext `47b08f7`. Sin conflictos. PR #3 **MERGED**.
- El pull arrastró también `f1ec381` (Punto: simulador de movimiento ETAPA 1) — **puramente aditivo** (`tools/simulador_toolpath.py` + test, sin JS/DocType), ya estaba en erpnext. Inocuo.
- Deploy: `git pull` → version stamp → **`bench migrate`** → `bench build` → `bump_page_cache` → `restart all`. **7/7 workers RUNNING.**

## ⚠️ Nota sobre el migrate (importante para futuros deploys de páginas)
El brief que me llegó decía "sin migrate", pero la **descripción de la tarea (MSG_037) ya avisaba que SÍ lo necesita** — y lo confirmé en vivo: sin migrate la Page `precios` **no se registra** (`tabPage` vacía → `/app/precios` no existe). Corrí `bench migrate`, la Page quedó registrada (`precios` / "Precios") y la página carga. Regla: **Page nueva o cambio de workspace ⇒ migrate** (son documentos, no assets).

## Verificación
- `/app/precios` → **HTTP 301** (redirect a login, normal). Los **502** que vi al inicio eran **transitorios**: nginx no alcanzaba a gunicorn mientras reiniciaba (`connect() failed to upstream` durante el boot de workers). Ya estable.
- `precios.js` deployado: **agrupa por familia** (20+ refs), flag **solo-lectura**/`readonly`, endpoints de **lectura** (`api.materiales.get_precios`/`get_all`), y la **constancia del sync**: `precio_por_kg` + "no existe" + "carga inicial" — tal como anticipaste (muestra la carga inicial y dice que el sync Tango→`precio_por_kg` no existe aún, en vez de inventar fecha). ✅
- La página quedó **partida** (según la decisión): *Parámetros de costeo* editables + *Precios de venta (precio_por_kg, maestro Tango)* **solo-lectura** → ya **no pisa el precio de Tango**.

## Pendiente (solo Constantino, requiere login)
La verificación **visual** — ver la tabla con las 4 familias, el shortcut "Precios" en el workspace, y la prueba de guardar un *parámetro de costeo* — la hace Constantino logueado (no tengo credenciales de UI). Todo lo server-side está OK.

Recordatorio del hilo abierto: con la página en solo-lectura, `precio_por_kg` queda **congelado hasta que exista el sync Tango→SI Material Corte** (opción (a) que se priorizó). Eso es tarea aparte.

— Orbit
