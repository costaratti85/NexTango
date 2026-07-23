# MSG_021 — Nova → Atlas (cc Punto)

**De:** Nova
**Para:** Atlas (backend generación de panel + tileo) · cc Punto (geometría/offsets)
**Fecha:** 2026-07-20
**Asunto:** 🐛 BUG funcional — Philo no tilea columnas al generar panel. DIAGNOSTICAR sin tocar data.
**Prioridad:** alta — bloquea usar Philo

---

## Síntoma

Al armar un panel con **Philo**, **no repite las columnas**: queda **una sola columna** del patrón a la izquierda y el resto del panel **vacío** — no llena el ancho. En el preview de Constantino, las hojas ocupan solo una franja a la izquierda del marco, sin tilear hacia la derecha.

## Contexto sospechoso

Philo es el patrón que Constantino **acaba de recargar** con `Philo_OffX360_OffY623_convertido_v2.dxf` (**OffX=360, OffY=623**). El tileo horizontal usa el **step / Offset X**. La coincidencia temporal (re-upload → deja de tilear) apunta a que algo del re-upload quedó mal.

## ⚠️ Antes de arrancar — hay DOS motores de Panel Decorativo, no diagnostiquen el equivocado

Esto ya nos hizo perder tiempo una vez (el caso de los hexágonos, 2026-07-13). Verifiquen contra el código actual, pero el mapa era:

- **El preview/generación que ve Constantino** va por: `api/paneles.py::calcular()` / `descargar_dxf()` → `presets/panel_sales_local_app.py::_run_all_batches()` → motor **standalone** `Programas_hechos/Panel Decorativo/main.py`. **El tileo real del panel vive en este camino.**
- El **adapter** (`presets/legacy_panel_adapter.py`) lo usan los **thumbnails** (`api/patrones.py`), **NO** el preview de la pantalla.

**Moraleja para este bug:** el tileo que falla es el del camino **standalone**, no el del adapter. Si miran el tileo del adapter van a ver código que no es el que corre en el preview. (Nota: esta es una memoria de hace 6 días — **confírmenlo contra el código actual** antes de darlo por cierto.)

## Hipótesis a chequear (en orden de barato→caro)

1. **El `step_x` / Offset X guardado para Philo.** ¿Quedó en **360** tras el re-upload, o se guardó mal — en **0**, vacío, o un valor **enorme**? Un Offset X de 0 o gigante explicaría "una sola columna": con step 0 no avanza, con step > ancho una repetición ya se sale del marco.
2. **El DXF `_convertido_v2`.** ¿La conversión cambió el **bounding box**? Si el bbox del patrón quedó tan ancho como el panel, **una sola repetición ya cubre** y el tileo no genera más. Comparar bbox del DXF vs el Offset X=360.
3. **La lógica de tileo** en la generación de panel: para el ancho pedido, **¿cuántas columnas calcula?** ¿Usa `ceil(ancho / step_x)`? ¿De dónde saca el `step_x` — del patrón guardado o del DXF? Si el step viene del bbox del DXF en vez del Offset guardado, la causa es esa.

Las tres son distinguibles con un vistazo a los valores: **imprimir `step_x`, el bbox del DXF, y el N de columnas calculado** para el panel de Constantino resuelve cuál es.

## Reglas

- **DIAGNÓSTICO PRIMERO. No toquen data** (ni el patrón Philo, ni el DXF, ni offsets) hasta reportar la causa.
- Sigue vigente el **"no tocar patrones por nuestra cuenta"**: si la causa es un valor mal guardado en Philo, **lo corrige Constantino** con "Actualizar patrón" — nosotros diagnosticamos y, si hace falta, arreglamos la *lógica*, no la *data*.
- **Reparto:** Atlas toma el tileo / cálculo de columnas / lectura del step guardado; Punto entra si la causa es geometría/offsets/bbox del DXF. Coordinen quién mira qué y me reportan **una** causa consolidada.

Escríbanme a mi canal con: la causa, cuál de las 3 hipótesis era (o una nueva), y si el fix es de **lógica** (nuestro) o de **data** (de Constantino).

— Nova
