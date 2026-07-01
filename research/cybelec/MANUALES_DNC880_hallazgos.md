# Hallazgos — Manual de Utilización DNC 880 / ModEva (flujo operativo real)

**Fecha:** 2026-06-20 · Fuente: manuales ADIRA en `adira_pdfs/` (copiados de `\\190.190.190.9\...`).
Texto extraído en `text/ADIRA_*.txt`.

Estado de cada manual:
- **DNC 880 Ref 2D** — idéntico al `ModEvaRef2D_es` ya estudiado (mismo conteo: 102 pág). Sin novedad.
- **CYCAD (inglés)** — idéntico al `CYCAD3_EN` ya estudiado (convenciones DXF). Sin novedad.
- **Mantenimiento** — mecánico (lubricación, anomalías, pares de apriete). No toca el control.
- **DNC 880 Manual de Utilización** — **NUEVO**: el flujo operativo paso a paso. De acá salen los hallazgos.

---

## Cómo programa el operario (lo que replicamos)

### Método L-alfa (modo 2D)
- Se "arranca" el perfil por un extremo y se cargan **longitud, ángulo, longitud, ángulo…**; la última ala no lleva ángulo. (= nuestro modelo.)
- **Sugerencia textual del manual:** *"Introduzca primero todas las longitudes y, a continuación, los ángulos. Este modo es mucho más rápido."* → valida nuestra entrada con Enter (cargar la tirada de medidas y después los ángulos).
- El perfil **se dibuja solo** a medida que se carga; el **radio interno** y el **desarrollo** se calculan automáticamente. (= nuestra vista en vivo.)

### Sentido de plegado = SIGNO del ángulo  ⭐
- *"La definición del sentido de plegado se realiza de manera inversa al signo del ángulo, aunque la elección del lado es arbitraria, si bien debe ser **constante en todo el perfil**."*
- O sea: **−90° dobla para el lado contrario que +90°**. No hay campo aparte de sentido: va en el signo del ángulo.
- Nuestro toggle ↑/↓ es funcionalmente equivalente (multiplica el giro por ±1). **Mejora posible:** permitir tipear el ángulo con signo (−90) para igualar el hábito del operario Cybelec.

### Medidas externas (DIN)
- *"Las medidas de los lados se acotan exteriormente, según la norma DIN."* (= nuestro modelo de cota externa.)

---

## Eje Y (profundidad) y corrección de ángulo  ⭐⭐ (lo más valioso)

- La **Y se calcula automáticamente** a partir del ángulo + herramientas + material. También se puede **forzar Y1/Y2 directamente** sin programar ángulo.
- **Ciclo de corrección empírico (así clava los ángulos Cybelec):**
  1. Plegar una pieza de prueba.
  2. **Medir el ángulo real obtenido** (ej. 93° cuando se pedían 90°).
  3. Cargar ese ángulo medido en la columna PLEGADO.
  4. El control **calcula solo la corrección de Y** (ej. −0.292 mm en Y1/Y2) para llegar al ángulo pedido.
  5. Repetir 2–3 veces si hace falta (es normal).
- **Implicación para nuestra app:** en vez de (o además de) un retorno elástico fijo, agregar en la pantalla de operación un campo **"medí el ángulo real"** que ajuste la cota Y de ese pliegue por geometría. Es la forma correcta y aprende solo. La relación: `ΔY ≈ (∂profundidad/∂ángulo) · (ángulo_medido − ángulo_objetivo)` = sensibilidad PMB × error.

---

## Eje X (tope) con cotas externas  ⭐

- Dos formas:
  1. El operario **resta el espesor** de la cota externa a mano.
  2. **(Recomendada por el manual)** cargar la **cota externa** en X y aplicar una **corrección constante negativa ≈ espesor** para toda la pieza (en el ejemplo: −2.00 mm para chapa de 2 mm).
- Encima, **corrección fina por medida**: se mide el ala real y se ajusta X (ej. −0.10) por pliegue.
- **Implicación:** ofrecer un campo de **corrección X global** (≈ espesor) + corrección por pliegue, en línea con cómo se trabaja realmente.

---

## Otros campos / funciones útiles

| Campo | Qué es |
|---|---|
| **CY** | Nº de pliegues idénticos a repetir (ej. CY=2 hace dos pliegues iguales). |
| **COPIAR PLIEGUE/PLEGADO** | Duplica la secuencia en curso (carga rápida de piezas repetitivas). |
| **SIGMA** | Resistencia del material en **Kg/mm²** (manual: acero = 37; taller usa 45). ≈ daN/mm². |
| **RETR. TOPE TRA.** | El **tope trasero retrocede** durante el plegado para que el ala que sube no lo golpee. (No aplica al Estun manual, pero explica por qué a veces el tope se aparta.) |
| **PMS** | Punto muerto superior (dónde para la trancha al subir). |
| **PCV** | Punto de cambio de velocidad (rápido → lento de plegado). |
| **BOMBEADO** | Compensación de flexión de la mesa en plegados largos (auto). |
| **DISTANCIA PV / TIEMPO PRESIÓN / VELOCIDAD PLEG.** | Parámetros de ciclo hidráulico. |

---

## Qué cambia/mejora en nuestra app (priorizado)

1. **Corrección de ángulo empírica** (medir ángulo real → ajustar Y). El salto más grande en precisión. ⭐⭐
2. **Corrección X** global (≈ espesor) + por pliegue, al estilo del manual. ⭐
3. **Ángulo con signo** opcional para el sentido (igualar el hábito Cybelec). ⭐
4. **CY / copiar pliegue** para piezas repetitivas (UX). 
5. Relabel sigma a **Kg/mm²** y usar ×9.81 en el tonelaje (hoy ×10; diferencia ~2%).

Lo que YA teníamos bien y el manual confirma: L-alfa, cotas externas DIN, desarrollo por DIN 6935, búsqueda automática del orden ("BUSCAR ORDEN DE PLEGADO"), Y desde el ángulo, dibujo en vivo.
