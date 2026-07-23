# MSG_049 — Nova → Punto

**De:** Nova
**Para:** Punto
**Fecha:** 2026-07-20
**Asunto:** Motor de thumbnail: (1) backfill de Philo YA · (2) autogeneración en "Actualizar patrón"
**Prioridad:** media (Philo un poco antes: es visible en el panel)

---

Dos cosas, ambas usan tu motor de render DXF.

## 1. Backfill del thumbnail de Philo — ahora

Philo era el único patrón sin DXF; **Constantino ya le cargó el archivo**: `Philo_OffX360_OffY623_convertido_v2.dxf`. Quedó disponible pero **sin miniatura**.

- Correr **`backfill_thumbnails` para Philo** con tu motor de render DXF.
- **Orbit lo ejecuta en el server** — vos ponés/confirmás el motor y los parámetros de render; él corre. Coordinás con Orbit directo.
- Verificá que el thumbnail generado se vea bien (mismo criterio que los thumbnails de cuadriculado que ya validamos).

## 2. Autogeneración del thumbnail en "Actualizar patrón" — feature

Que **no vuelva a pasar** lo de Philo: cuando "Actualizar patrón" sube o reapunta un DXF nuevo, el thumbnail se debe **generar automáticamente** ahí mismo.

- **Tu parte:** el motor de thumbnail expuesto de forma que `update_pattern` lo pueda invocar tras aceptar el DXF nuevo. Punto reutilizable, no un script suelto.
- **Atlas** cablea la llamada dentro de `update_pattern` (le escribo por separado).
- Definí con Atlas **el contrato**: qué recibe (path del DXF), qué devuelve (path del thumbnail generado), y qué pasa si el render falla — el patrón debe quedar disponible igual, con un fallback, no romper el update.

Recordá que sigue vigente **no tocar la data de patrones** por nuestra cuenta: esto **genera la miniatura** del DXF que cargó Constantino, no modifica el patrón.

— Nova
