# MSG_134 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino) + Dispatch
**Fecha:** 2026-07-16
**Asunto:** Modelo del pierce implementado (commit 3453051) + INFORME auditable de β

---

## PARTE 1 — Modelo del pierce: implementado

Commit **`3453051`** (origin/erpnext), pusheado.

- **γ (pierce) dejó de calibrarse.** Ahora es una constante prescripta:
  `PIERCE_SECONDS_SIN_FLYCUT = 3.0`, `PIERCE_SECONDS_CON_FLYCUT = 1.0` — universal, no lee
  ningún campo del material. Aplica igual en la fórmula calibrada y en la fórmula legacy
  (ahí también ignoré el `tiempo_perforacion_s` por-material de la tabla vieja, para ser
  consistente con "la diferencia entre espesores se ignora").
- **α y β NO se tocaron** — siguen siendo los de la Batería 2 (calibrados, validados contra
  la física real). No re-ajusté nada contra los tiempos de CypCut con el pierce forzado en
  3s, como pediste — eso habría corrompido α/β compensando en la dirección incorrecta.
- **`apto_flycut`**: parámetro nuevo en `calculate_consumed_resources()`. Está conectado en
  los 3 puntos donde se calcula costo (tresbolillo/cuadriculado circle vía engine legacy,
  cuadriculado cuadrado, tresbolillo hexágono) — falta solo que Vega agregue el checkbox en
  la UI y lo mande en el batch (`apto_flycut: true/false`); el backend ya lo respeta.
- `set_laser_coefs.py` actualizado: `laser_c_s_per_m2` pasa a 0 (ya no se usa).
- **8 tests nuevos** + suite completa: 92 passed (1 fail pre-existente sin relación —
  `si_preset` doctype stub, confirmado con git stash que no es mío).

---

## PARTE 2 — INFORME AUDITABLE: cómo se derivó β = 202 mm/s efectivos

Esto es la cuenta completa, no el R². Podés seguirla paso a paso y, si querés, reproducirla
vos mismo en una planilla.

### 2.1 — Datos de entrada (exactamente lo que vos midieron en CypCut, Batería 2)

| Panel | Cut (mm) | Travel (mm) | Pierce | Tiempo total CypCut (s) |
|-------|---------:|------------:|-------:|-------------------------:|
| B2_01 | 10640.00 |  2911.19 |   37 |  200.590 |
| B2_02 |  6320.00 |  2949.22 |   37 |  143.140 |
| B2_03 | 50080.00 | 23992.90 |  577 | 1472.215 |
| B2_04 |  9880.00 |  8091.79 |   50 |  229.871 |
| B2_05 |  7032.00 |  6310.07 |   85 |  226.439 |
| B2_06 |  5688.00 |  6314.98 |   85 |  208.539 |
| B2_07 | 13408.00 | 14654.96 |  197 |  485.957 |
| B2_08 | 34420.00 | 39407.14 | 1522 | 2459.030 |
| B2_09 | 10272.00 | 14659.87 |  197 |  444.164 |
| B2_10 |  5620.00 |  9407.14 |   82 |  217.540 |
| B2_11 | 12820.00 | 21207.14 |  442 |  799.413 |
| B2_12 |  7920.00 | 14663.55 |  197 |  412.819 |

12 paneles. Estos son los datos crudos, sin tocar — los mismos que vos ya tenés en tu log de
CypCut.

### 2.2 — El modelo y qué busca "mínimos cuadrados" (en criollo)

Para cada panel, la fórmula predice:

```
tiempo_predicho = α·cut + β·travel + γ·pierce + δ
```

Con 4 números desconocidos (α, β, γ, δ) y 12 paneles, hay 12 ecuaciones (una por panel) y
solo 4 incógnitas — el sistema está "sobre-determinado", no hay una solución que caiga
exacta en los 12 a la vez. **Mínimos cuadrados** busca los 4 números que hacen que la suma
de los errores al cuadrado (predicho − real, elevado al cuadrado, sumado en los 12 paneles)
sea lo más chica posible. No es una caja negra: es la solución de un sistema de 4 ecuaciones
lineales, que muestro abajo con los números reales.

### 2.3 — La cuenta exacta (sistema de 4 ecuaciones, 4 incógnitas)

Se arman 4 "sumas cruzadas" de los datos (esto es lo único que hace el algoritmo — sumar y
multiplicar columnas). Con los 12 paneles de arriba, las sumas dan:

```
Σ(cut·cut)     = 4,569,263,216.00      Σ(cut·travel)   = 3,555,770,092.40
Σ(cut·pierce)  =    95,838,600.00      Σ(cut)          =       174,100.00
Σ(travel·travel)= 3,473,864,290.00     Σ(travel·pierce)=    94,324,806.52
Σ(travel)      =       164,569.95      Σ(pierce·pierce)=     2,987,616.00
Σ(pierce)      =         3,508.00      Σ(1)            =            12.00

Σ(cut·t)       =   192,275,616.56      Σ(travel·t)      = 176,524,138.70
Σ(pierce·t)    =     5,289,034.41      Σ(t)             =       7,299.72
```

(`t` = tiempo real de CypCut). Con esas 14 sumas se arma el sistema:

```
4569263216·α + 3555770092·β +   95838600·γ +    174100·δ = 192275616.56
3555770092·α + 3473864290·β +   94324806·γ +    164570·δ = 176524138.70
  95838600·α +   94324806·β +    2987616·γ +      3508·δ =   5289034.41
    174100·α +     164570·β +       3508·γ +        12·δ =      7299.72
```

**Resolver este sistema (4 ecuaciones, 4 incógnitas — cualquier planilla con `MINVERSA` +
`MMULT`, o Wolfram Alpha, o Python) da:**

```
α = 0.013372 s/mm    (corte)
β = 0.004948 s/mm    (desplazamiento)  ← ESTE es el que pediste
γ = 1.185179 s/pierce (queda reemplazado por el prescripto, no se usa más)
δ = -0.012756 s       (≈ 0, insignificante)
```

**Nota de precisión:** en mensajes anteriores redondeé β a 0.004946; recalculando ahora con
todos los decimales el valor correcto es **0.004948** (diferencia de 0.04%, sin impacto
práctico, pero te doy el número exacto ya que pediste poder auditarlo).

### 2.4 — De β a la velocidad efectiva

```
β = 0.004948 s/mm
1/β = 1 / 0.004948 = 202.1 mm/s
```

Eso es todo el cálculo: β es "segundos que tarda por cada milímetro de desplazamiento en
rápido"; invertirlo da "milímetros por segundo" = velocidad efectiva.

### 2.5 — Prueba final: ¿la fórmula reproduce lo que vos mediste?

Con los 4 coeficientes de arriba, esto predice la fórmula para cada uno de tus 12 paneles,
contra lo que vos realmente cronometraste en CypCut:

| Panel | Real (s) | Predicho (s) | Error |
|-------|---------:|-------------:|------:|
| B2_01 |   200.59 |    200.52 | 0.04% |
| B2_02 |   143.14 |    142.94 | 0.14% |
| B2_03 |  1472.21 |   1472.20 | 0.00% |
| B2_04 |   229.87 |    231.39 | 0.66% |
| B2_05 |   226.44 |    225.98 | 0.20% |
| B2_06 |   208.54 |    208.03 | 0.24% |
| B2_07 |   485.96 |    485.26 | 0.14% |
| B2_08 |  2459.03 |   2459.06 | 0.00% |
| B2_09 |   444.16 |    443.35 | 0.18% |
| B2_10 |   217.54 |    218.86 | 0.61% |
| B2_11 |   799.41 |    800.19 | 0.10% |
| B2_12 |   412.82 |    411.92 | 0.22% |

Error máximo entre los 12: **0.66%**. Esa es la validación real — no un R² abstracto, sino
que la cuenta, aplicada a cada panel, casi no se separa de lo que vos cronometraste.

### 2.6 — ¿Por qué 202 mm/s y no 1650 mm/s?

Esto ya lo cerraste vos mismo en MSG_041: 1650 es la velocidad pico teórica de la máquina
una vez que la torcha subió y aceleró; β (202 mm/s efectivo) absorbe las rampas de
aceleración/desaceleración y la subida/bajada de la torcha en cada agujero — que es
exactamente lo que tus 12 paneles reales muestran, no un supuesto mío.

---

**Resumen:** α, β y δ salen de resolver un sistema de 4 ecuaciones lineales armado con sumas
de tus propios datos (mostrado arriba, número por número); β=0.004948 s/mm → 202 mm/s no es
una caja negra, es la solución de esa cuenta. Podés reproducirla en una planilla si querés
verificarla vos mismo.

— Punto
