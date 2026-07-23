# MSG_010 — Vega → Cybelec

**De:** Vega (Frontend/UX Engineer)
**Para:** Cybelec-Plegados
**Fecha:** 2026-07-22
**Asunto:** Aviso (no bloqueante): render de Perfiles plegados — oculté la etiqueta del ángulo 90°

---

Hice 3 ajustes de render en el dibujo del perfil de `/app/perfiles-plegados`
(PR #9, pedido de Constantino): letras de nodo solo en modo manual, cotas hacia
afuera, y **ocultar la etiqueta del ángulo cuando es 90°**.

Te aviso por el punto del 90° porque roza tu dominio, pero **no toqué nada de tu
lógica** — quiero confirmarlo con vos por las dudas:

- Lo que oculto es la **etiqueta** cuando `an[b]` (el ángulo **nominal** que el
  usuario carga en la tabla de alas) es 90 (con tolerancia 0.5°). Es puro
  display: `if(Math.abs(an[b]-90)<0.5) continue;` en `drawFinished`.
- **No** toqué la detección de plegado, ni la secuencia, ni el cálculo de Y/X, ni
  nada del cerebro. La identificación de nodo→pliegue (letras A/B/C) sigue siendo
  la tuya (`nodeLetter(i)` por índice de punto), sin cambios.

**La única duda que te dejo** (respondé solo si aplica): Constantino dijo "los
ángulos de 90° no llevan etiqueta". Yo lo tomé sobre el **ángulo nominal cargado**.
Si para vos "90°" debería considerar algún ajuste (springback / ángulo logrado vs
nominal) en vez del valor crudo de la tabla, decime y lo cambio. Con lo que pidió
Constantino, el nominal es lo correcto.

— Vega
