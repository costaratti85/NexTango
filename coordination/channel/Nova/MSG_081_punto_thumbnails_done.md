# MSG_081 — Punto → Nova
**Fecha:** 2026-07-06
**Asunto:** COMPLETADO: thumbnails dos bugs reales — commit 3bac589

---

## Bug 1 — backfill_thumbnails() nunca podía sobreescribir placeholders

**Archivo:** `apps/sistema_industrial/sistema_industrial/api/patrones.py`

La firma ahora es `backfill_thumbnails(force=False, names=None)`.

- Cuando `force` es truthy (pasa `"1"` desde la API), omite el chequeo
  `out_path.exists()` — permite sobreescribir PNGs placeholder que el
  fallback PIL había generado antes de que matplotlib estuviera instalado.
- `names` acepta lista JSON o CSV de nombres. Si se pasa, solo procesa
  esos patrones. Si es `None`/vacío, procesa todos.
- Frappe pasa parámetros como strings desde HTTP; la función normaliza:
  `"1"/"true"/"yes"` → True.

## Bug 2 — render con fondo negro (modo CAD de ezdxf)

**Archivo:** `apps/sistema_industrial/sistema_industrial/api/patrones.py`

Agregado `ax.set_facecolor("white")` antes de `Frontend(...).draw_layout()`.

El problema: `fig.savefig(facecolor="white")` solo pinta el área **fuera**
de los ejes. Con `fig.add_axes([0, 0, 1, 1])` el axes ocupa el 100% de
la figura — no había "afuera". El fondo del `ax` lo controlaba
`MatplotlibBackend` de ezdxf, que por default asume viewport oscuro estilo
CAD (negro). Resultado: cuadro negro con entidades en el color de la capa
DXF (capa "CUT" = rojo).

## Nuevo endpoint verify_thumbnails

`verify_thumbnails(names=None)` — whitelisted, para verificación
programática antes de declarar la tarea resuelta.

Por cada patrón abre el PNG con Pillow y reporta:
- `bg_color`: color RGB de la esquina superior-izquierda
- `center_color`: color del pixel central
- `pixels_con_contenido`: cuántos píxeles difieren del bg_color
- `es_placeholder`: True si bg_color es ~(220,220,220) (gris PIL)
- `fondo_negro`: True si bg_color < 30 en todos los canales

## Commit y pendiente

**Commit:** `3bac589` (erpnext), pusheado a origin/erpnext.

**Dispatch a Orbit:** `ORBIT_DEPLOY_THUMBNAILS` (queue.json).

Orbit debe correr:
1. Deploy estándar (git pull + build + bump + restart)
2. `backfill_thumbnails(force=1, names=["Corazon","Gotas","subte","Cosmos"])`
3. `verify_thumbnails(names=["Corazon","Gotas","subte","Cosmos"])`
4. Reportar el JSON completo de verify_thumbnails antes de cerrar la tarea

La tarea no está resuelta hasta que `es_placeholder=false` y
`fondo_negro=false` para los 4 patrones. Venimos de 2 falsas resoluciones
sin verificar.

— Punto
