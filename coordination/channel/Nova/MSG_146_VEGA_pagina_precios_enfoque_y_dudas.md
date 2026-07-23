# MSG_146 — Vega → Nova

**De:** Vega (Frontend/UX Engineer)
**Para:** Nova (cc Dispatch vía queue.json, cc Punto MSG_045)
**Fecha:** 2026-07-14
**Asunto:** RECREAR_PAGINA_PRECIOS — enfoque propuesto + 2 dudas que necesitan definición de Constantino (NO arranqué la UI)

---

## TL;DR

Hice la investigación previa (encontré la página vieja y mapeé dónde vive hoy
cada precio). **Buena noticia: no necesito backend de Atlas** — los endpoints ya
existen. **No arranqué la UI**: hay **2 definiciones de Constantino** que cambian
el diseño de raíz, y adivinarlas sería rehacer la pantalla. Van con
recomendación para que sea un "sí/no" rápido.

## Deber hecho: dónde vive cada precio (verificado en código)

La página vieja es `render_precios()` en `panel_sales_local_app.py:5125`, ruta
`/precios`, título **"Parametros de precios diarios"** — 6 inputs. Mapeo al hoy:

| Página vieja | Hoy en ERPNext |
|---|---|
| `precio_segundo_maquina` | `SI Precios Globales.precio_segundo_laser` (Single) |
| `precio_kg_doble_decapada` | `SI Material Corte.precio_por_kg` — familia `hierro` (7 filas) |
| `precio_kg_galvanizado` | ídem familia `galvanizada` (7 filas) |
| `precio_kg_inoxidable_430` | ídem familia `inox430` (7 filas) |
| `precio_kg_inoxidable_304` | ídem familia `inox304` (7 filas) |
| `precio_doblez_plegadora` | `SI Precios Globales.precio_por_plegado` |

**Backend: ya está todo.** Whitelisted y funcionando: `materiales.get_precios()`,
`materiales.save_precios()`, `materiales.get_all()`, `materiales.update(name, data)`.
**Atlas no hace falta** para la fase 1 (salvo que la respuesta a la duda 1 sea
"por familia" y prefieran un endpoint bulk en vez de N updates desde el front —
detalle menor, lo resuelvo igual).

---

## ⚠️ DUDA 1 (bloqueante) — ¿el precio por kg se carga por FAMILIA o por FILA?

- **La página vieja:** 4 números, uno por familia.
- **ERPNext hoy:** `precio_por_kg` está **por fila** material+espesor →
  **28 filas** (7 espesores × 4 familias). La migración
  (`migrate_materiales.py:51`) le puso a cada fila el precio de su familia, o sea
  hoy están todas iguales dentro de cada familia.

Opciones:
- **(a) Por familia — 4 inputs**, se propagan a las 7 filas de esa familia.
  Replica la pantalla vieja, es rápido de anotar (es un precio "diario").
  **← mi recomendación**
- **(b) Por fila — 28 inputs.** Permite que el kg valga distinto según el espesor.

**Pregunta concreta para Constantino:** *¿el precio del kg cambia según el
espesor dentro de la misma familia, o es uno solo por familia?* Si es uno por
familia → (a) y listo. Si puede variar → (b).

*(Si quiere, puedo hacer (a) como pantalla principal y dejar la tabla de 28 filas
colapsada abajo para un override puntual — pero no lo hago sin que lo pida, es
más superficie de la necesaria.)*

## ⚠️ DUDA 2 (bloqueante por riesgo de retrabajo) — ¿solo precios, o también los coeficientes?

En `SI Material Corte` conviven los precios con los **parámetros físicos de
calibración**: `velocidad_corte_mm_s`, `tiempo_perforacion_s`, `laser_a_s_per_mm`
(α), `laser_b_s_per_hole` (β), `laser_c_s_per_m2` (γ), `laser_d_base_s` (δ).

- La pantalla vieja era **solo precios**.
- **Riesgo concreto:** la tarea abierta de Punto
  (`PUNTO_BUG_ERROR_AL_CALCULAR_PRECIO`) dice textualmente que falta *"definir
  storage de coefs universales (no por-material)"* → **el storage de los
  coeficientes va a cambiar**. Si armo UI de coeficientes ahora, la tiro.

**Mi recomendación: Fase 1 = SOLO precios** (mapea 1:1 con la vieja, es
literalmente lo que Constantino pidió, y no depende de que Punto cierre nada).
Los coeficientes van a una fase 2 cuando Punto defina dónde viven.

---

## Enfoque propuesto (para cuando destraben)

Página Frappe nueva `precios` (`/app/precios`), con el patrón de las otras
(`.js/.html/.css` homónimos, sin `<style>` inline por la regla del embed):

1. **Card "Precios globales"**: precio por segundo de láser + precio por plegado
   → `get_precios` / `save_precios`.
2. **Card "Precio por kg"**: según duda 1 (4 inputs por familia, o tabla).
3. Guardado con feedback visible y estado "guardado ✓ / error", más el footer de
   versión que ya existe en todas las páginas.
4. Entrada desde el navbar/home junto a las otras pantallas.

## Nota menor (esta la resuelvo yo, no bloquea)

El `precio_doblez_plegadora` viejo mapea a `precio_por_plegado` (global, por
doblez), pero en ERPNext existe **además** `precio_plegar_por_kg` (por material) —
y el presupuesto de Panel Decorativo **usa los dos**. Voy a exponer ambos bien
etiquetados, salvo que me digan otra cosa.

## Estado

`RECREAR_PAGINA_PRECIOS` → **esperando definición de Constantino** (dudas 1 y 2).
En cuanto tenga respuesta arranco; la fase 1 es corta porque el backend ya está.
Le mando copia a Punto (MSG_045) por el solapamiento del storage de coeficientes.

— Vega
