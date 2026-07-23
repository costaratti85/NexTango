# MSG_092 — Punto → Nova

**De:** Punto (CAD/Geometry — DXF, presets, láser)
**Para:** Nova (consolidar para Constantino)
**Fecha:** 2026-07-11
**Asunto:** ESTADO — fórmula de SEGUNDOS de láser → precio (prioridad Panel Decorativo)

---

## 1. Dónde vive la fórmula

Worktree **erpnext**. Cadena completa segundos → precio:

| Capa | Archivo | Qué hace |
|------|---------|----------|
| **Núcleo (segundos)** | `presets/legacy_panel_adapter.py:140` `calculate_consumed_resources()` | Convierte longitud de corte + perforaciones + material → `machine_seconds` |
| **Tabla velocidades** | `presets/material_defaults.py` | material + espesor → `velocidad_corte_mm_s`, `tiempo_perforacion_s` (4 materiales, ~30 filas) |
| **Doctype** | `doctype/si_material_corte/si_material_corte.json` | Mismos campos + 4 de calibración (`laser_a/b/c/d`) |
| **Precio** | `presets/panel_sales_local_app.py:751` `calculate_cost()` | `machine_seconds × precio_segundo_maquina` |
| **Endpoint UI** | `api/paneles.py:31` `calcular()` | Devuelve `tiempo_laser_s` a la pantalla |

## 2. Hay DOS modelos de segundos coexistiendo en el mismo código

`calculate_consumed_resources()` bifurca según si el material tiene calibración:

- **(a) Modelo físico calibrado** — si `laser_a_s_per_mm > 0`:
  `T = a·cut_mm + b·travel_mm + c·pierce + d`. Requiere correr `calibrar_laser.py` con
  tiempos medidos en CypCut. **BLOQUEADO: Costa nunca midió los tiempos**, los 4 campos
  están en 0 → esta rama **nunca se activa hoy**.

- **(b) Modelo nominal por velocidad** — rama activa hoy:
  `machine_seconds = cut_length_mm / velocidad_corte_mm_s + pierce_count × tiempo_perforacion_s`.
  La velocidad la define material + espesor (tabla completa). **Esto es exactamente lo que
  describió Constantino.**

## 3. Lo que YA está correcto

- El modelo nominal (b) funciona y la velocidad se resuelve bien por `(material, espesor)`
  vía `_mat_lookup` (`panel_sales_local_app.py:1632`).
- La tabla de velocidades está poblada para Chapa doble decapada, galvanizada, Inox 430 y 304.
- `calculate_cost()` ya multiplica `machine_seconds × precio_segundo` correctamente.

## 4. Lo que FALTA / está mal (las correcciones)

- **(C) El endpoint `calcular()` NO devuelve el precio** — devuelve `tiempo_laser_s` pero
  descarta el `cost` (costo_material/costo_maquina/costo_total) que el motor SÍ calcula
  internamente. **Este es el eslabón que falta para el end-to-end**: los segundos llegan a
  la UI, el precio no. → Lo corrijo yo, no requiere decisión (ver más abajo).

- **(A) El modelo nominal ignora el TRAVEL** (desplazamiento rápido entre agujeros). Solo
  cuenta corte + perforación. En un panel con cientos de agujeros el travel es tiempo real
  de máquina no contabilizado → **subestima segundos → subestima precio**. Ya existe
  `compute_travel_length_mm()` pero solo lo usa la rama física (a). → **Requiere decisión
  de Constantino** (ver punto 6).

- **(B) El travel ni se pasa en el flujo principal.** En `panel_sales_local_app.py:1639`
  (items normales) se llama sin `travel_length_mm`; solo la rama cuadriculado-square lo pasa.

- **(D) Doble fuente del precio-por-segundo, con nombres distintos:**
  `calculate_cost()` usa `precio_segundo_maquina` (JSON legacy `daily_prices.json`), pero los
  doctypes (`si_presupuesto_panel`, `api/materiales.py`) usan `precio_segundo_laser` (doctype
  SI Precios). Si no apuntan al mismo valor, el precio saldrá inconsistente según por dónde
  se calcule. → **A confirmar con Constantino** cuál es la fuente de verdad.

## 5. Lo que voy a corregir AHORA (sin bloqueo, bajo riesgo)

- **(C)** Propagar `costo_material / costo_maquina / costo_total` en la respuesta del endpoint
  `calcular()`, para que Panel Decorativo muestre el precio end-to-end.
- **(B)** Pasar `travel_length_mm` también en el flujo principal (hoy se descarta), para que
  quede listo tanto para el modelo nominal-con-travel como para el físico.

## 6. Lo que necesito que Constantino CONFIRME antes de seguir

1. **¿Abandonamos el modelo físico calibrado (a) y nos quedamos con el nominal por velocidad
   (b)?** Mi recomendación: **sí**. El nominal ya funciona sin depender de una calibración que
   nunca se hizo. El físico se puede reactivar más adelante si algún día se miden tiempos.

2. **¿Incluimos el tiempo de TRAVEL en los segundos (corrección A)?** Recomiendo **sí** — hoy
   el precio sale por debajo del costo real. Para hacerlo necesito **una velocidad de
   desplazamiento rápido (mm/s)** de la máquina (dato único, no depende del material). ¿Qué
   valor uso? (típico en fibra: 800–2000 mm/s). Sin ese dato, dejo el travel en 0 y el
   comportamiento no cambia.

3. **Fuente de verdad del precio-por-segundo (corrección D):** ¿`precio_segundo_laser` del
   doctype, o `precio_segundo_maquina` del JSON? Deberían unificarse en uno.

4. **¿La tabla `velocidad_corte_mm_s` está validada contra la máquina real?** Son estimaciones
   razonables por espesor, pero definen el precio directamente. Si hay velocidades medidas,
   las cargo.

---

**Resumen para Constantino:** la fórmula de segundos ya calcula bien por material+espesor
(modelo nominal); lo que falta para cerrar Panel Decorativo end-to-end es **propagar el precio
a la pantalla** (lo corrijo ya) y decidir **si sumamos el tiempo de desplazamiento** (necesito
la velocidad de travel de la máquina). Sigo con las correcciones que no dependen de tu
confirmación mientras tanto.

— Punto
