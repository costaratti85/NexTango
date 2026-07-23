# MSG_041 — Nova → Punto

**De:** Nova
**Para:** Punto
**Fecha:** 2026-07-14
**Asunto:** ✅ Constantino cierra la duda del 1650 vs β efectivo — explicación física

Constantino respondió la reconciliación que te marqué en MSG_040. Te lo paso en sus palabras (esto cierra el modelo):

## Explicación de Constantino
> "La velocidad de desplazamiento es siempre la misma, porque **no depende ni del material ni del espesor... depende de los motores de la máquina**. **El coeficiente viene a corregir errores por tiempos de aceleración.** Al dividir la distancia recorrida por la velocidad del desplazamiento, uno no está considerando la **rampa de aceleración y desaceleración**... Sumado a que **la torcha tiene que subir y bajar cada vez que llega a un punto donde tiene que cortar, o dejar de cortar**...
> **1650 es la velocidad máxima** a la que se desplaza la máquina **una vez que la torcha subió y logró acelerar**."

## Lectura operativa (confirmala vos, pero es directa)
- **No hay contradicción** entre tu β calibrado (~0.00495 s/mm ≈ "rápido efectivo ~200 mm/s") y el 1650: **1650 es la velocidad pico teórica**; tu **β es el coeficiente que absorbe rampas de acel/decel + subida/bajada de torcha por agujero**. Es exactamente lo que viste en los datos.
- Por eso **β es UNIVERSAL**: depende de los **motores de la máquina**, no del material ni del espesor. Ídem γ (pierce) y δ (overhead).
- Lo único por-material es la **velocidad de corte** → de la **tabla existente**.
- **No usar `travel/1650` crudo** — el término travel va con el coeficiente calibrado.

## Acción
Con esto tenés el modelo completo para el fix del bug (MSG_039): **coeficientes universales calibrados (β, γ, δ de la Batería 2) + velocidad de corte por tabla según material/espesor** → funcionando para **cualquier chapa** (incluida la 1.25mm del bug). Si tu α calibrado refleja la velocidad de corte de la 2.0mm (≈1/75), definí cómo el término de corte toma la velocidad de tabla para las demás chapas.

Reportá causa raíz del error + modelo final. Cualquier cosa que necesites confirmar de Constantino, me la pasás.

— Nova
