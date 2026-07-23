# MSG_135 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino) + Dispatch
**Fecha:** 2026-07-16
**Asunto:** Rediseño de la fórmula — avancé todo lo que pude, pero está BLOQUEADO por un dato que no tengo

Constantino pidió ver resultados. Voy a ser directo: **todavía no hay resultados con datos
reales**, y prefiero decir eso ahora a inventar un ajuste que parezca lindo. Explico qué
hice, qué falta, y por qué.

## El bloqueo

Para ajustar j (desplazamiento) contra el `Move time` real, y para validar el modelo de
corte contra el `Processing time` real — necesito el **desglose por componente
(Processing/Move/Delay) de los 12 paneles de la Batería 2**. Lo que yo tengo guardado
(`calibracion_bateria2_REAL.json`) es solo el **Total agregado** de cada panel — nunca
recibí la descomposición.

Ustedes SÍ la tienen — la consulta anterior citó números exactos de B2_01 (142.3/14.4/43.9
vs 152.5/21.1/27.0), así que en algún momento Constantino se la pasó a Dispatch/Nova por un
canal que a mí no me llegó (mismo patrón que ya pasó con la calibración P01-P14). **Necesito
esos 12×3 números (Processing_s, Move_s, Delay_s por panel) para poder ajustar o validar
cualquier cosa con datos reales.**

## Lo que SÍ hice — y ya me deja algo concreto para reportar

Preparé toda la infraestructura (commit `dae7233`), y de paso encontré un hallazgo que **no
necesita el dato faltante**:

### 1) Reconstruí la geometría REAL de los 12 paneles
No desde parámetros teóricos — desde los mismos 12 DXF que subí y que CypCut procesó
realmente. Extraje los 3484 saltos individuales (por eje X/Y, en orden serpenteante
boustrophedon — la estrategia estándar, aunque no puedo confirmar al 100% que es el orden
exacto que usó CypCut, lo marco como supuesto) y los segmentos de corte de cada agujero.

### 2) Implementé el modelo de desplazamiento como pediste
- Jerk-limitado por eje: `t = (32·d/j)^(1/3)`, **max(tx, ty)**, no hipotenusa.
- **Verifiqué la fórmula matemáticamente yo mismo** (derivación del perfil jerk simétrico de
  4 tramos, reposo a reposo) — no es un número que copié, la re-derivé y da exacto 32.
- La linealicé: t = k·max(dx,dy)^(1/3) con k=(32/j)^(1/3) → el ajuste de k (y de un posible
  `t_torcha`) es una regresión lineal de 2 parámetros, auditable igual que hice con α/β/δ.
- Probé la maquinaria de ajuste con datos sintéticos (k conocido, sin ruido): recupera el k
  exacto. Con offset de t_torcha sintético: también lo recupera exacto. **La herramienta
  funciona; lo que falta es el dato real para correrla en serio.**

### 3) Hallazgo que SÍ puedo reportar ya, sin el dato faltante
Con los 3484 saltos reales reconstruidos: **el rango de distancias va de 25mm a 140mm**
(mediana 40mm). Con cualquier velocidad máxima razonable (500 a 1650 mm/s) y el jerk de
referencia, la distancia crítica donde el régimen puro-jerk deja de valer está entre
1562mm y 56000mm — **muy por encima de cualquier salto real de estos 12 paneles.**

**Conclusión, tal como pediste que reporte:** las 12 muestras cubren **solo el régimen
corto (puro-jerk)**. No hay evidencia del régimen lineal (jerk→aceleración→crucero) en
estos datos. No lo implementé — no por pereza, sino porque no hay con qué validarlo. Si en
algún momento se necesita cubrir paneles con saltos largos (varios cientos de mm), va a
hacer falta una batería de calibración nueva con saltos más largos.

### 4) Corte: no toqué nada todavía
Como pediste — no asumí que es la misma física que los saltos. Dejé la función con
`NotImplementedError` explícito hasta tener el Processing time real.

### 5) Sobre el punto 4 del consejo (flycut también reduce desplazamiento)
Lo marco como pendiente conocido, no resuelto: el modelo de `apto_flycut` que implementé la
vez pasada solo afecta el pierce (γ). Si con flycut la máquina no frena completo entre
agujeros, el término de desplazamiento (β/k) también debería cambiar con `apto_flycut` — pero
no tengo mediciones de CypCut con flycut activado para calibrar ESE caso. Lo dejo señalado
para cuando haya esos datos; no lo inventé.

## Lo que necesito para poder mostrar resultados de verdad

**El desglose Processing/Move/Delay de los 12 paneles B2_01 a B2_12** (el mismo tipo de dato
que ya tienen para B2_01, solo que completo). En cuanto lo tenga, corro
`ajustar_modelo_desplazamiento` (ya probado y funcionando) y reporto k, j, t_torcha, R² y
predicho-vs-real por panel — con el mismo nivel de detalle auditable que el informe de β.

— Punto
