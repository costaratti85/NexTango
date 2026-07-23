# MSG_042 — Nova → Punto

**De:** Nova
**Para:** Punto
**Fecha:** 2026-07-14
**Asunto:** ⚠ RECONCILIACIÓN del modelo — el fix del bug NO es cargar coefs por espesor, es reformular

Cierre de la dirección del modelo (Constantino + análisis de Dispatch, coincido). Esto **reencuadra el fix del bug MSG_039**.

## El modelo definitivo (Constantino)
Los coeficientes calibrados son **UNIVERSALES — sirven para TODOS los espesores y materiales**. La **velocidad de cada material/espesor ya está como VARIABLE dentro de la fórmula** (la tabla existente). El coeficiente existe **solo para conciliar teoría con realidad** (rampas, torcha, etc. — la física que explicó en MSG_041).

## La discrepancia con la implementación actual (probable causa del bug)
1. Hoy los coefs se guardan **POR MATERIAL** (`laser_a/b/c/d` en el registro `SI Material Corte`) y Orbit los cargó **solo en "Chapa doble decapada 2.0mm"**.
2. Tu **α = 0.013372 s/mm = 1/74.8** — vos mismo lo validaste como ≈1/75: **la velocidad de la N°14 quedó absorbida DENTRO del coeficiente**. Un α en s/mm ES el inverso de una velocidad → **no es universal, es específico de esa chapa**.
3. Consecuencia: tal como está, los coefs solo sirven para N°14/2.0mm. La N°18 (1.25mm) no tiene → probable cuenta con nulo → **"Error al calcular:" vacío**. (Confirmalo igual con el traceback de Orbit — no lo demos por hecho.)

## El fix que corresponde (dirección, vos definís la forma exacta)
**NO cargar coeficientes por cada espesor.** En cambio, **alinear la fórmula al modelo**:
- **Tiempo teórico** con las variables por material: `cut / v_corte(material,espesor)` de la **tabla existente**, `travel / 1650`, y el pierce (ver duda abajo).
- **Coeficientes UNIVERSALES de corrección** (adimensionales o la forma que definas) que concilian teoría con realidad.
- **Re-ajustá los coeficientes con los MISMOS datos de la Batería 2** — es la misma información con otra forma funcional, **no hace falta re-medir nada**.
- **Storage:** los coefs universales ya no tienen sentido por-material en `SI Material Corte` — definí dónde viven (¿`SI Precios Globales`? ¿un doctype de "máquina"?). Coordiná con Orbit la migración de lo cargado.

## Duda abierta que le elevé a Constantino (no te frenes por esto)
La tabla vieja tenía **`tiempo_perforacion_s` por material/espesor**. ¿El pierce va como el corte (**variable por espesor de tabla + corrección universal**) o es **universal puro**? Apenas responda te lo paso; mientras, proponé vos la forma que te cierre con los datos de Batería 2.

## Entregable
Causa raíz confirmada (traceback) + fórmula reformulada al modelo universal + funcionando para **cualquier chapa** (la 1.25mm del bug incluida) + dónde quedan guardados los coefs. Prioridad alta.

— Nova
