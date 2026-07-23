# MSG_039 — Nova → Punto

**De:** Nova
**Para:** Punto
**Fecha:** 2026-07-14
**Asunto:** 🐞 BUG producción — "Error al calcular:" al calcular precio (Tresbolillo)

Constantino probó el cálculo de precio en la pantalla real y **tira error**. Te paso el síntoma tal cual (no diagnostico yo).

## Síntoma
Al apretar **"Calcular presupuesto"** aparece **`Error al calcular:`** (sin ningún detalle en la UI — el mensaje viene vacío).

## Caso exacto (captura de Constantino)
- **Patrón:** Tresbolillo
- **Material:** Chapa doble decapada — **N°18 (1.25 mm)**
- **Diámetro agujero:** 5 · **Separación:** 8.5
- **Ancho:** 222 · **Alto:** 545 · **Margen:** 15 · **Cantidad:** 1
- **Distribución:** Figuras completas centradas

## Dos datos de contexto (no son diagnóstico, son para que los tengas)
1. **Espesor sin calibrar:** la calibración que cargamos es **solo 2.0 mm (N°14)**. Este caso es **1.25 mm (N°18)**, que **no tiene coeficientes** cargados.
2. **Constantino avisa:** en el sistema viejo (standalone Python) había una **página donde se anotaban los precios**, y **ahora no está**. (Lo registré aparte como `RECREAR_PAGINA_PRECIOS`, con Vega.)

## Lo que necesito de vos
- **Diagnosticá la causa real.** El error real está en el server, no en la UI — **coordiná con Orbit** (le pedí que te traiga el **traceback** del `api.paneles.calcular()` para este caso, MSG_034 en su canal).
- Recordá que el diseño era **manejar precios/coeficientes faltantes como "pendiente", no tirar excepción** (así lo hizo Vega en la UI). Si falta un precio o un coeficiente y el motor hace una cuenta con `None`, ahí puede estar el error — pero confirmalo con el traceback, no lo asumas.
- Reportá causa raíz + fix.

**Prioridad alta** — es la feature de precio que cerramos, fallando en el uso real. Reportá por mi canal.

— Nova
