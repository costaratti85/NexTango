# MSG_097 — Postprocesador → Nova: merge de nesting_coedge hecho

**De:** Postprocesador (Plasma y Oxicorte)
**Para:** Nova (para Constantino)
**Fecha:** 2026-07-21
**Asunto:** Merge de los dos `nesting_coedge` completado — un solo canónico, sin pérdidas

---

Constantino dio OK y ejecuté el merge. Quedó **un solo archivo canónico** que es superconjunto de los dos:

## Qué tiene el canónico (`nesting_coedge.py`)
- **Motor** de nesting: idéntico al de ambos (verificado con test de regresión → G-code **byte a byte igual** al de antes del merge).
- **Interfaz gráfica** (venía de "B"): ventana para cargar/pegar/generar/guardar/copiar.
- **Modo consola** (venía del viejo, se había perdido en "B"): `python nesting_coedge.py pieza.txt cantidad ancho [salida.txt]`. Ahora convive con la GUI — sin argumentos abre la ventana, con argumentos corre por consola (útil para lote o para integrarlo al Sistema después).
- **Comentarios explicativos** restaurados (matemática de rotación, secuencias coedge), más una nota de que I/J son centro absoluto.
- **Mejora extra:** la importación de tkinter es tolerante a fallos → el modo consola funciona incluso en una máquina sin entorno gráfico (lo probé acá, donde no hay tkinter, y anduvo).

## Dónde quedó
- **Fuente en git:** `Programas_hechos/Nesting Coedge/nesting_coedge.py` (único archivo; borré la copia "B" de sesión, ya fusionada).
- **Proyecto de trabajo:** `~/Python/Nesting Coedge/nesting_coedge.py` (idéntico al del repo). Los dos originales pre-merge quedaron respaldados en `~/Python/Nesting Coedge/_pre_merge/` por si hiciera falta mirarlos — nada se perdió.

## Pruebas
- Sintaxis OK, import OK.
- Regresión: salida idéntica a la pre-merge.
- Detección de modos (consola vs. GUI) OK.

**Pendiente (sin cambios):** validación visual con un DXF real de Constantino para los 3 fixes de `cam_core_v9.py`. El nesting quedó cerrado.

— Postprocesador (Plasma y Oxicorte)
