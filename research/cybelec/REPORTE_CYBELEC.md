# Reporte de ingeniería inversa — Control Cybelec (plegadora ADIRA)

**Fecha:** 2026-06-20
**Autor:** Claude (sesión nocturna autónoma)
**Encargo:** Analizar a fondo el CD ADIRA y el software Cybelec; aprender cómo
calcula la secuencia de plegado y las posiciones X/Y por medida y ángulo, con
vistas a desarrollar un control numérico propio.

> **Resumen ejecutivo.** El control de la plegadora es un **Cybelec** (DNC 60 /
> familia DNC 800-880S/ModEva). Reconstruí su modelo de cálculo completo a
> partir de los manuales de referencia 2D, reverseé el **formato binario de los
> archivos de datos `.DAT`** (Microsoft Binary Format + strings con prefijo),
> recuperé el **manifiesto y la arquitectura del software PC1200** (app Visual
> Basic 6, motor en `Dnc.dll`, dongle Sentinel) desde el instalador, y decodifiqué
> la **biblioteca de útiles de fábrica** (matrices V6–V100 y punzones). Entregué
> además un **motor de cálculo funcional en Python** (`bend_engine.py`) ya
> validado. **No se necesitó autorización para nada**: todo el análisis fue
> estático (lectura, `strings`, decodificación), sin ejecutar binarios ni red
> salvo consultas técnicas públicas (DIN 6935).

---

## 1. Qué hay en el CD (inventario relevante)

| Carpeta | Contenido | Valor para el proyecto |
|---|---|---|
| `ModEva_manuals` | Manuales de referencia 2D (ES), CYCAD, técnicos CTI42-48 | **Alto** — la "física" del cálculo |
| `swbmhl2/disk1..13` | Instalador del **PC1200** (InstallShield, 785 archivos) | **Alto** — el software de programación offline |
| `Tools/cycad` | Conversor **DXF→plegado** + ejemplos `.DXF` + tablas `.DAT` | **Alto** — directamente aplicable a tu proyecto DXF |
| `Tools/Cyback` | Backup de parámetros máquina | Medio |
| `Tools/LINK7000` | Comunicación PC↔control | Medio |
| `Tools/cyb2000_4000`, `EPROM`, `Flash` | Config de motores/servos, flash EPROM | Bajo (no es cálculo) |
| `Tools/PROT_KEY`, `Sentinel_*` | Dongle de protección | Informativo |

---

## 2. Arquitectura del software PC1200 (recuperada del instalador)

El `data1.cab` (InstallShield "ISc(" v5/6) trae el manifiesto en claro. Componentes clave:

- **`TDNC9.exe`, `Dncpanel.exe`** — UI principal (emula el control en PC).
- **`Dnc.dll`, `Dncsvr.exe`** — motor de lógica/cálculo y servidor de comunicación.
- **`CybAXWrapper.dll`, `Cybhook.dll`, `Cybuinst.dll`** — wrappers ActiveX de Cybelec.
- **`MSVBVM60.DLL`, `MSCOMM32.OCX`, `Mfc42.dll`** → **es una aplicación Visual Basic 6** (con piezas MFC/C++) y puerto serie por MSComm.
- **`Lf*/Lt*12n.dll`** — librerías de imagen **LEAD Technologies** (manejo de gráficos/DXF).
- **`sentw9x.*`, `snti386.dll`, `sentinel.hlp`** — protección **Sentinel** (dongle en puerto paralelo).
- **Datos** (`*.DAT`): `Lstmat.dat` (matrices), `Lstpoin.dat` (punzones), `Lstcple.dat` (pares), `Lstmac.dat` (máquina), `Dirpie.dat` (índice de piezas), `Pi*.dat` (piezas).

**Implicancia:** el cálculo "fino" (desarrollo, simulación, colisión) vive en el
PC1200/`Dnc.dll`; el lazo de control en tiempo real (mover trancha y topes) vive
en el hardware del DNC. Para un control propio hay que reimplementar **ambos**,
pero el primero es matemática conocida (este reporte) y el segundo es
electrónica/servo (otro proyecto).

> Extracción pendiente: el contenido de los `.cab` está comprimido (zlib por
> archivo). Recuperar los binarios requiere `unshield`/`i6comp`. **No es
> necesario** para entender el cálculo —ya está documentado— pero serviría para
> auditar valores exactos. Es lo único que dejaría para una segunda pasada si lo
> querés.

---

## 3. El formato `.DAT` (reverse-engineereado y verificado)

Decodificado al 100 % en su parte legible. Ver `dat_decoder.py` y
`decoded_dat_tables.txt`.

- **Strings**: 1 byte de longitud `N` + `N` bytes ASCII.
- **Números**: **Microsoft Binary Format** (float single, 4 bytes), orden
  *exponente-primero*: `[exp][mant_lo][mant_mid][mant_hi]`

      valor = (-1)^sign · (1 + frac) · 2^(exp − 128)
      sign  = bit7 de mant_hi
      frac  = ((mant_hi & 0x7F)<<16 | mant_mid<<8 | mant_lo) / 2^23

  **Validación:** `86 00 00 20` → 1.25·2⁶ = **80.0 mm** (coincide con los segmentos
  de 80 mm del `EXEMPLE1.DXF`). Otros: `82 00 00 20`→4.0, factor k, ángulos 90/180, etc.

### Biblioteca de matrices de fábrica (`LSTMAT.DAT`)
Nombres `V-ang-largo`: V de **6, 8, 10, 12, 16, 24, 32, 40, 60, 80, 100 mm**,
ángulo de matriz **30°/60°**. Cada registro trae geometría (altura, hombros,
radio de matriz, tonelaje admisible). Ej. la columna final escala con V
(1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 10, 14, 20, 24) ≈ **radio de matriz / espesor mínimo**.

### Biblioteca de punzones (`LSTPOIN.DAT`)
Nombres tipo `5_1.0_H`, `2-1.0`, `4-3.0-H`, `7-7.5`… con **radio de punta**
(rp = 1.0, 2.0, 3.0…), altura, y el perfil del punzón (segmentos para colisión).
El punzón `5_1.0_H` (radio de punta 2.0, altura 510) es el que usa el producto de
ejemplo `PI20000` (código `10-30-60`, sobre `EXEMPLE.DXF`).

### Piezas (`Pi*.dat`) e índice (`DIRPIE.DAT`)
Cada pieza guarda: DXF de origen, fecha, código de útiles, material, y los
campos numéricos (alas, ángulos, cotas X, profundidades). El índice lista
nombre/descripción/fecha por pieza.

---

## 4. Cómo se programa una pieza desde un DXF (convención CYCAD)

CYCAD lee un DXF organizado en **capas** (lo identifica por un texto
`CYCAD : XXX`). Esto es **directamente replicable** en tu pipeline DXF:

- **`OUTLINE`** — contorno cerrado (líneas+arcos) + cortes internos. Parámetros
  como textos `clave = valor`: `Thick=`, `Punch=`, `Die=`, `Sigma=`, `Radius=`,
  `DefAngle=`, `Name=`, `DIN`, `Inch`, `ScaleX/Y=`.
- **`BENDS`** — líneas de pliegue. Texto cerca del medio de cada línea = **ángulo**.
  Campos por pliegue separados por `/`:
  `P=` punzón, `D=` matriz, `R=` radio interno, `C=` nº de pliegues de curva ideal,
  `I` pliegue invertido. Ej.: `90.5 / D=M1 / R=3.1 / C=5 / P=P1`.
- **`SECTIONS`** (opcional) — secciones + orden y apoyos: `b1,b2,…` (orden),
  `s1,s2,…` (apoyo), `e1,e2,…` (contacto tope delantero).

Entidades soportadas: `LINE`, `ARC`, `POLYLINE`, `LWPOLYLINE`, `TEXT` (los arcos
se segmentan). Límites: 1000 segmentos, 30 secciones, 130 pliegues.

---

## 5. El modelo de cálculo (lo que pediste)

Notación: **α** = ángulo interior de la pieza (90° = escuadra). **β = 180 − α** =
ángulo de plegado. **V** = apertura de matriz. **s** = espesor. **rᵢ** = radio interno.

### 5.1 Longitud desarrollada — norma **DIN 6935**

    L_desarrollada = Σ(alas medidas al vértice exterior) + Σ(v)

con el **valor de compensación** v por pliegue (normalmente negativo = descuento):

    v = (π·β/180)·(rᵢ + k·s/2) − 2·(rᵢ + s)·tan(β/2)        (β < 165°; v=0 si β≥165°)

y el **factor de fibra neutra**:

    k = 0.65 + 0.5·log₁₀(rᵢ/s)     para rᵢ/s < 5
    k = 1.0                         para rᵢ/s ≥ 5

(Verificado contra la tabla redondeada de DIN 6935: rᵢ/s≈1→k≈0.6, ≈2.4→0.8, ≥5→1.0.)
Cybelec agrega **encima** un factor empírico **K por material** (tabla MATERIAL,
10 coeficientes) que NO es el k de la fórmula — es ajuste de taller. También
admite cargar el desarrollo **REAL** medido y reparte la diferencia entre alas.

### 5.2 Posición Y (penetración → ángulo), plegado **al aire**

El ángulo es **geométrico**: lo fija cuánto penetra la punta del punzón en la V.

    profundidad d = (V/2)·tan(β/2)            (para α=90° ⇒ d = V/2)

Radio interno natural ≈ **V·0.16** (entre V/6 y V/8); si el punzón tiene radio
mayor, manda el del punzón.

**Sensibilidad PMB** (la del manual) = |dd/dα| = mm de profundidad por 1° de
ángulo. Si < 0.05 mm/° → usar V más ancha. Para V=16, α=90° ≈ 0.14 mm/°.

**Retorno elástico (springback):** se **sobre-pliega**. Se forma a (α − Δα) y al
liberar la fuerza la chapa abre Δα hasta α. Δα viene de la tabla
**COMPENSACIÓN ELASTICIDAD** por material y franja de ángulo (ej. acero 76–90° →
−2.5°). El control aprende: cargás el ángulo medido y recalcula la corrección
(por pliegue, sección o pieza).

Modos: **al aire** (lo de arriba) vs **fondo de matriz/acuñado** (el ángulo lo da
la matriz, manda el tonelaje) vs **embutición** (baja hasta tope mecánico).

### 5.3 Posición X (tope trasero)

    X(pliegue i) = (cota del ala detrás de la línea de plegado)
                   ± correcciones de fibra neutra de los pliegues ya hechos

En curva ideal mueve también el eje **R** (altura del tope) automáticamente.
Ejes auxiliares: **Z1/Z2** (posición lateral de los dedos), **R** (altura).

### 5.4 Fuerza de plegado (tonelaje), al aire

    F[ton] = coef · Rm · L · s² / (V · 9810)        (Rm en N/mm²; L,s,V en mm)

coef ≈ 1.33 estándar; Cybelec usa coeficiente propio (1.75 al aire en la tabla
MATERIAL). Regla de partida: **V ≈ 8·s**. El control verifica que el tonelaje no
supere el admisible de los útiles (de `LSTMAT`/`LSTPOIN`).

### 5.5 Secuencia de plegado (el "orden de cortes")

Función **BUSCAR ORDEN PLEGADO**: prueba órdenes y descarta los que producen
**colisión** (la pieza pega contra trancha o bastidor), guiada por **criterios de
simulación** (prioritarios/no-prioritarios): mínimo de volteo/pivoteo/basculado,
manipulación óptima según espesor y relación largo/ancho, % de **flexibilidad**
(cuánta penetración teórica se tolera), longitud mínima del lado del operario,
apoyo sobre segmentos inclinados. Si no hay solución, **modo DESPLEGADO**: parte
de la pieza terminada y va del último pliegue al primero.

```
Entradas: alas+ángulos (del DXF), espesor, material(σ), punzón, matriz(V)
   ├─ DIN 6935 (+K) ─────────► Longitud desarrollada y descuentos
   ├─ Geometría V/penetración ► Y (PMB) por ángulo ──► + springback (tabla)
   ├─ Cotas − descuentos ─────► X (tope), R, Z
   ├─ Búsqueda con colisión ──► Secuencia de pliegues
   └─ σ·ancho·s²/V ───────────► Tonelaje (vs admisible de útiles)
```

---

## 6. Entregables en esta carpeta (`research/cybelec/`)

| Archivo | Qué es |
|---|---|
| `bend_engine.py` | **Motor de cálculo funcional** (DIN 6935 + Y + X + tonelaje + springback), con demo y autovalidación. Corre con `python bend_engine.py`. |
| `dat_decoder.py` | Lector del formato `.DAT` (MBF + strings). Corre sobre cualquier `LST*.DAT`/`Pi*.dat`. |
| `decoded_dat_tables.txt` | Volcado decodificado de las tablas de fábrica (matrices, punzones, pieza ejemplo, índice). |
| `text/` | Texto extraído de los manuales clave (ModEva 2D, PC1200 2D, CYCAD, CTI). |
| `REPORTE_CYBELEC.md` | Este documento. |

**Validaciones que pasan hoy:** penetración 90° = V/2 ✓; factor k DIN
(rᵢ/s=1→0.65, ≥5→1.0) ✓; desarrollo de U y tonelaje en rangos reales ✓;
decodificación MBF contra geometría conocida del DXF ✓.

---

## 7. Recomendación de camino (para decidir con vos)

1. **Calculadora de plegado** (extender `bend_engine.py`): entrada de pieza →
   desarrollo, X/Y por pliegue, tonelaje, con tablas de útiles y springback
   editables. Verificable contra piezas reales de tu taller. *(base ya hecha)*
2. **Lector DXF→plegado** estilo CYCAD, reutilizando el pipeline DXF de
   `Panel Decorativo`. Las convenciones de capas ya están documentadas (§4).
3. **Control completo** (cálculo + secuenciador con colisión + interfaz a
   hardware): proyecto grande, conviene por etapas. La parte de cálculo y el
   secuenciador son software; el lazo servo/hidráulico es el hito de hardware.

**Riesgo/realidad:** replicar el cálculo es factible y ya está encaminado.
Reemplazar el hardware del DNC (drivers de eje, seguridad, válvulas) es el
verdadero proyecto de ingeniería y conviene tratarlo aparte.

> Pendiente opcional (no bloqueante): extraer los `.cab` con `unshield` para
> auditar `Dnc.dll` y los valores exactos de las tablas de fábrica. Si lo querés,
> en la próxima sesión instalo la herramienta (requiere tu OK para `pip`/descarga).
