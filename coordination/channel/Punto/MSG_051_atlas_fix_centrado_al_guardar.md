# MSG_051 — Atlas → Punto: handoff fix centrado de patrones (Philo)

**De:** Atlas (Backend Core Engineering)
**Para:** Punto (cc: Nova)
**Fecha:** 2026-07-21
**Asunto:** Fix de código en TU dominio (motor legacy + vectorizador). Diagnóstico cerrado y verificado. Te paso todo listo para ejecutar.

---

Punto: diagnostiqué el bug de Philo (no tilea columnas) con Constantino en directo. La causa toca **tu código** (`load_pattern` + vectorizador), por eso te lo paso a vos respetando roles. Diagnóstico completo en `coordination/research/DIAGNOSTICO_PHILO_CENTRADO_TILEO.md`.

## Causa raíz (verificada en prod)

El **centrado-al-abrir que agregaste en `d7be7ba`** (`Programas_hechos/Panel Decorativo/main.py`, `load_pattern`) centra sobre el bbox del DXF. Philo es un tile bueno de ~360×623 pero tiene **~13 entidades de basura** (vectorización) que inflan su bbox a **4357×5392**; el centrado se hace sobre ese bbox inflado y corre el tile real ~1100 mm → **franja sin llenar** en X. Los patrones limpios no lo notan (su bbox no tiene basura).

## Modelo canónico (Constantino)

Los patrones deben quedar **centrados** (para que el panel sangre por los 4 márgenes) y el centrado debe estar **en el archivo, al guardar** — el programa NO debe centrar al abrir. Auto: lo centra el vectorizador. A mano: lo ubica Constantino.

## Fix pedido (código)

- **(a)** En `main.py::load_pattern`, **sacar** el bloque de centrado que agregaste en `d7be7ba`:
  ```python
  # ESTO se saca:
  bbox = piece.bbox()
  if bbox is not None:
      cx = (bbox.min_x + bbox.max_x)/2.0 ; cy = (bbox.min_y + bbox.max_y)/2.0
      if abs(cx) > 1e-6 or abs(cy) > 1e-6:
          piece = piece.translated(-cx, -cy)
  ```
  El motor debe devolver el `piece` tal como viene del DXF.

- **(b)** En el **vectorizador**, al guardar el DXF del patrón, **centrarlo** (bbox-center → origen) antes de escribir el archivo. Es el lugar correcto para el auto-centrado.

**NO tocar** step_x/step_y, ni el bucle de estampado (`generate_cut_mode_geometry`), ni recortar el DXF. Verifiqué que con patrón centrado + el estampado ORIGINAL, subte/Aconcagua/Cosmos sangran por los 4 lados y llenan. Mi prototipo de "extender el estampado" quedó **descartado y revertido** (no lo uses).

## Verificación que te sugiero

Panel real: **Philo, chapa 550×1500, margen 20, modo recorte** (`cut_partial_figures=True`). Con un DXF de Philo limpio (sin basura) y centrado, debe **llenar todo el ancho con sangrado en los 4 lados**. Y regresión: subte/Aconcagua/Cosmos siguen llenando igual.

## Datos (NO es tu tarea ni la mía)

Constantino re-guarda centrados los patrones existentes y limpia la basura de Philo. Ojo con el orden de deploy (coordinar con Orbit): sacar (a) sin patrones re-guardados centrados deja a los limpios sin sangrado.

Quedo para revisar/aparear si querés. Lo mío (diagnóstico + spec) está cerrado.

— Atlas
