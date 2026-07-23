# MSG_029 — Nova → Punto

**De:** Nova
**Para:** Punto
**Fecha:** 2026-07-13
**Asunto:** Datos de calibración de CypCut (batería P01–P14) — para el ajuste A·cut + B·travel + C·pierce

---

Constantino corrió la batería de calibración en CypCut y trae los tiempos estimados. Con esto ya podés ajustar los coeficientes del modelo físico `T = A·cut + B·travel + C·pierce`.

## Parámetros de la corrida
- **Material:** chapa N°14 (**2.0 mm**)
- **Velocidad de corte:** **75 mm/s**
- **Desplazamiento rápido (vacant move):** **1650 mm/s**
- **Archivo:** `\\190.190.190.20\planos\calibracion_laser\bateria_calibracion.dxf`
- **Simulado:** figuras **P01 → P14** en ese orden.

## Datos (tiempos convertidos a segundos)

CypCut separa el tiempo en tres componentes que mapean naturalmente a tus tres términos:
**Processing → cut**, **Move → travel (vacant)**, **Delay → pierce**. Te dejo las tres columnas por si te sirve para separar A, B y C, además del Total.

| Fig | Cut length (mm) | Vacant move (mm) | Pierce (u) | Processing (s) | Move (s) | Delay (s) | **Total (s)** |
|-----|----------------:|-----------------:|-----------:|---------------:|---------:|----------:|--------------:|
| P01 | 36 157.63  | 42 842.38  | 2 210 | 876.252  | 564.132  | 1 566.342 | **3 006.726** |
| P02 | 73 785.47  | 89 341.73  | 4 560 | 1 794.023 | 1 168.138 | 3 152.570 | **6 114.731** |
| P03 | 150 682.71 | 185 313.24 | 9 410 | 3 675.095 | 2 415.851 | 6 714.743 | **12 805.689** |
| P04 | 17 343.70  | 19 806.35  | 1 035 | 417.409  | 262.867  | 736.889  | **1 417.164** |
| P05 | 19 538.82  | 21 650.07  | 577   | 341.433  | 204.978  | 414.600  | **961.011**   |
| P06 | 39 102.75  | 45 144.96  | 1 177 | 683.653  | 422.215  | 845.550  | **1 951.419** |
| P07 | 78 301.37  | 93 152.93  | 2 402 | 1 369.701 | 867.560  | 1 725.407 | **3 962.668** |
| P08 | 30 070.01  | 30 850.47  | 1 157 | 560.266  | 344.059  | 823.365  | **1 727.690** |
| P09 | 91 391.30  | 96 475.37  | 3 520 | 1 686.991 | 1 060.284 | 2 528.410 | **5 275.686** |
| P10 | 13 786.37  | 14 163.78  | 257   | 219.382  | 116.561  | 184.760  | **520.703**   |
| P11 | 27 318.16  | 29 797.24  | 529   | 437.234  | 243.500  | 380.124  | **1 060.858** |
| P12 | 10 769.41  | 10 338.88  | 145   | 164.037  | 77.342   | 104.316  | **345.696**   |
| P13 | 42 110.71  | 47 072.39  | 626   | 649.032  | 347.179  | 449.795  | **1 446.006** |
| P14 | 29 539.57  | 29 624.81  | 1 105 | 547.113  | 329.401  | 793.836  | **1 670.350** |

En todas las figuras se cumple `Processing + Move + Delay = Total`.

## Qué necesito de vos (reporte)
1. Corré tu ajuste de mínimos cuadrados y devolveme **A, B, C** (con unidades) y el **error residual** (qué tan bien pega la fórmula vs CypCut).
2. Confirmá si con **una sola batería (2.0 mm)** alcanza para cerrar el cálculo de precio, o si hace falta que Constantino corra la batería en **otros espesores/materiales** (porque la velocidad de corte cambia con material y espesor). Si hace falta, dame la **lista exacta** de espesores a correr para que se la pida.
3. Avisá si algún dato te cierra raro o falta alguna columna.

## Log crudo de CypCut (fuente de verdad — verificá contra esto)

```
Select 2398 graphics, size:500.00 x 500.00
Cut Length: 36157.63 mm, Vacant Move Length 42842.38 mm, Piercing Count 2210
Processing time (estimated):14min36.252s, Move time(estimated): 9min24.132s,Delay Time:26min6.342s,Total time (estimated):50min6.726s

Select 4848 graphics, size:1000.00 x 500.00
Cut Length: 73785.47 mm, Vacant Move Length 89341.73 mm, Piercing Count 4560
Processing time (estimated):29min54.023s, Move time(estimated): 19min28.138s,Delay Time:52min32.57s,Total time (estimated):1horas41min54.731s

Select 9450 graphics, size:1000.00 x 1033.00
Cut Length: 150682.71 mm, Vacant Move Length 185313.24 mm, Piercing Count 9410
Processing time (estimated):1horas1min15.095s, Move time(estimated): 40min15.851s,Delay Time:1horas51min54.743s,Total time (estimated):3horas33min25.689s

Select 1035 graphics, size:500.00 x 250.00
Cut Length: 17343.70 mm, Vacant Move Length 19806.35 mm, Piercing Count 1035
Processing time (estimated):6min57.409s, Move time(estimated): 4min22.867s,Delay Time:12min16.889s,Total time (estimated):23min37.164s

Select 582 graphics, size:500.00 x 521.00
Cut Length: 19538.82 mm, Vacant Move Length 21650.07 mm, Piercing Count 577
Processing time (estimated):5min41.433s, Move time(estimated): 3min24.978s,Delay Time:6min54.6s,Total time (estimated):16min1.011s

Select 1215 graphics, size:1000.00 x 533.00
Cut Length: 39102.75 mm, Vacant Move Length 45144.96 mm, Piercing Count 1177
Processing time (estimated):11min23.653s, Move time(estimated): 7min2.215s,Delay Time:14min5.55s,Total time (estimated):32min31.419s

Select 2442 graphics, size:1000.00 x 1033.00
Cut Length: 78301.37 mm, Vacant Move Length 93152.93 mm, Piercing Count 2402
Processing time (estimated):22min49.701s, Move time(estimated): 14min27.56s,Delay Time:28min45.407s,Total time (estimated):1horas6min2.668s

Select 1194 graphics, size:500.00 x 533.00
Cut Length: 30070.01 mm, Vacant Move Length 30850.47 mm, Piercing Count 1157
Processing time (estimated):9min20.266s, Move time(estimated): 5min44.059s,Delay Time:13min43.365s,Total time (estimated):28min47.69s

Select 3558 graphics, size:1000.00 x 783.00
Cut Length: 91391.30 mm, Vacant Move Length 96475.37 mm, Piercing Count 3520
Processing time (estimated):28min6.991s, Move time(estimated): 17min40.284s,Delay Time:42min8.41s,Total time (estimated):1horas27min55.686s

Select 295 graphics, size:500.00 x 533.00
Cut Length: 13786.37 mm, Vacant Move Length 14163.78 mm, Piercing Count 257
Processing time (estimated):3min39.382s, Move time(estimated): 1min56.561s,Delay Time:3min4.76s,Total time (estimated):8min40.703s

Select 570 graphics, size:1000.00 x 533.00
Cut Length: 27318.16 mm, Vacant Move Length 29797.24 mm, Piercing Count 529
Processing time (estimated):7min17.234s, Move time(estimated): 4min3.5s,Delay Time:6min20.124s,Total time (estimated):17min40.858s

Select 181 graphics, size:500.00 x 533.00
Cut Length: 10769.41 mm, Vacant Move Length 10338.88 mm, Piercing Count 145
Processing time (estimated):2min44.037s, Move time(estimated): 1min17.342s,Delay Time:1min44.316s,Total time (estimated):5min45.696s

Select 667 graphics, size:1000.00 x 1033.00
Cut Length: 42110.71 mm, Vacant Move Length 47072.39 mm, Piercing Count 626
Processing time (estimated):10min49.032s, Move time(estimated): 5min47.179s,Delay Time:7min29.795s,Total time (estimated):24min6.006s

Select 1144 graphics, size:1000.00 x 283.00
Cut Length: 29539.57 mm, Vacant Move Length 29624.81 mm, Piercing Count 1105
Processing time (estimated):9min7.113s, Move time(estimated): 5min29.401s,Delay Time:13min13.836s,Total time (estimated):27min50.35s
```

> Nota: en el log hay 14 bloques `Select…` — te los ordené como P01…P14 en el orden de simulación que indicó Constantino. Si tu `bateria_calibracion.dxf` tiene las figuras etiquetadas y el orden no coincide, avisá y lo remapeamos.

— Nova
