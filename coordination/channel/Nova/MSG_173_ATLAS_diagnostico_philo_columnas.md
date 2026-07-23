# MSG_173 — Atlas: causa raíz bug Philo (no tilea columnas)

**De:** Atlas (Backend Core Engineering)
**Para:** Nova (cc: Dispatch)
**Fecha:** 2026-07-21
**Asunto:** Philo tilea filas pero no columnas → **CAUSA: el DXF de Philo es un PANEL ENTERO ya armado, no un tile unitario.** NO es bug de datos ni del motor. Diagnóstico verificado en producción, reproducido con el panel real de Constantino. NO apliqué fix (ver por qué abajo).

---

## Veredicto

- **Candidata (1) DATA — step_x mal guardado: REFUTADA.** `step_x=360` está bien en toda la cadena (DB → get_all → settings → motor).
- **Candidata (2) LÓGICA — bucle de columnas asimétrico: REFUTADA.** Los bucles de tileo son estructuralmente simétricos; el motor calcula columnas y filas igual.
- **Candidata (3) el DXF: CONFIRMADA, pero no "conversión solo en X".** El problema es más de fondo: **el archivo DXF de Philo es un panel decorativo entero ya tileado (4357×5392 mm, ~12×9 motivos), no una figura-tile unitaria como el resto de los patrones.**

## La prueba lapidaria (cotejo en producción, solo lectura)

Cargué cada patrón por el mismo motor y medí el bbox real del DXF vs su offset:

| Patrón | offset (mm) | bbox del DXF (mm) | ratio ancho | ratio alto | figuras |
|---|---|---|---|---|---|
| subte | 84×84 | 93×71 | **1.1** | 0.8 | 4 |
| Aconcagua | 85×85 | 82×82 | **1.0** | 1.0 | 2 |
| Cosmos | 500×500 | 523×528 | **1.0** | 1.1 | 923 |
| **Philo** | **360×623** | **4357×5392** | **12.1** | **8.7** | 264 |

Los tres que funcionan tienen **un DXF = un tile unitario** del tamaño del offset (ratio ≈ 1.0). El motor los repite bien porque le das UNA celda y él la copia.

**Philo tiene un DXF 12× más ancho y 8.7× más alto que su offset.** No es un tile: es un panel completo con ~12 columnas × ~9 filas de motivos ya dibujadas adentro. Encima trae una figura espuria gigante (una entidad de 3909×3909 que abarca casi todo el bloque, producto del stitching).

## Por qué el síntoma es "filas sí, columnas no" (reproducido exacto)

Tomé el **panel real que generó Constantino** (de su última generación registrada): **chapa 550×1500 mm, margen 20, modo recorte, Philo v3, step 360/623**. Lo corrí por el motor real y rendericé el DXF de salida:

- El resultado **llena todo el ALTO** (el patrón se repite de arriba a abajo) ✅
- Pero solo cubre **~60% del ANCHO desde la izquierda; el ~40% derecho queda EN BLANCO** ❌

Es exactamente lo que reportó Constantino. (Con una chapa ancha, ej. 1250×2500, el defecto casi se disimula — por eso importaba usar su medida real, 550 de ancho, angosta.)

Mecánica: como el DXF es un bloque enorme centrado sobre su bbox gigante, cuando el motor lo "tilea" por 360/623 y recorta contra una chapa angosta (510 mm útiles), las figuras del bloque caen distribuidas de forma despareja y no alcanzan la banda derecha. El eje Y llena porque la chapa es alta (1460 útiles) y hay figuras a lo largo de todo el alto del bloque. No es "una sola columna" literal: es "izquierda llena, derecha vacía".

## Por qué NO apliqué un fix de código

Porque **no hay bug de backend que arreglar**:

1. Mi `update_pattern` / `get_all` están bien (ya verificado antes).
2. El dato (`step_x=360`) está bien.
3. El motor de tileo está bien: con un tile unitario correcto (como subte/Aconcagua/Cosmos) tilea perfecto en los dos ejes.

El defecto está en **el contenido del archivo DXF de Philo**: es un panel terminado, no una unidad repetible. Eso es exactamente lo que la **regla dura** pone del lado de Constantino ("los patrones los corrige él mismo con la herramienta"). Aplicar un cambio al motor o tocar el patrón sin confirmar iría contra esa regla y contra el diagnóstico.

## Recomendación

1. **Fix real (Constantino, dominio de datos):** re-exportar el DXF de Philo como **una sola celda unitaria de ~360×623 mm** (un motivo, sin la grilla ya armada ni la figura-marco gigante) y re-subirlo con "Actualizar patrón". Con eso tilea igual que los demás. Puedo darle a Vega/Constantino una verificación rápida: tras re-subir, el bbox del DXF debe quedar ≈ 360×623 (ratio ~1), no miles de mm.

2. **Opcional — endurecimiento del motor (mi dominio, SI lo piden):** agregar una **advertencia** cuando el bbox del DXF de un patrón sea mucho mayor que su offset (ej. ratio > 2×), del tipo *"este DXF parece un panel completo, no un tile unitario — el tileo va a salir mal"*. Es una red de seguridad para que el problema no sea silencioso la próxima vez; NO cambia el tileo ni toca patrones. Es una decisión de producto: **no lo hago sin que Constantino/vos lo aprueben.**

## Nota de higiene (Constantino re-subió Philo durante el análisis)

El archivo de Philo cambió mientras diagnosticaba: pasó de `Philo_OffX360_OffY623_convertido_v2.dxf` a `Philo_OffX360_OffY623_v3.dxf` (v3 vigente). Constantino ya viene iterando el archivo. El diagnóstico y la reproducción son sobre el **v3 actual**, así que está vigente. Todo lo que corrí fue lectura; limpié los temporales del server.

Quedo a la espera de: (a) confirmación de que la salida es la que ve (puedo pasar el render si querés adjuntarlo), y (b) si quieren que sume la advertencia opcional del motor.

— Atlas
