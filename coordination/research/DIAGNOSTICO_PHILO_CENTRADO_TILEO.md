# Diagnóstico y spec de fix — Philo no tilea columnas / centrado de patrones

**Autor:** Atlas (Backend Core Engineering)
**Fecha:** 2026-07-21
**Origen:** BUG MSG_022 (Philo genera una franja sin llenar en X). Sesión de diagnóstico con Constantino en directo; él definió el modelo canónico y luego delegó la ejecución al equipo.
**Estado:** diagnóstico cerrado y verificado. Fix especificado. Ejecución del CÓDIGO → Punto (es su dominio: motor legacy + vectorizador). Corrección de los DATOS (patrones) → Constantino, él mismo.

---

## 1. Síntoma

Al generar un panel con **Philo** (chapa 550×1500, margen 20, modo recorte), el patrón **llena todo el alto pero deja ~40% del ancho en blanco a la derecha**. Con chapa ancha el defecto se disimula; con la chapa angosta real (550) es evidente.

## 2. Causa raíz (verificada en producción, read-only)

**No es bug de datos (step_x) ni del bucle de tileo.** Es la **interacción del centrado-al-abrir con un bbox inflado por basura**:

1. **Todos los patrones se guardan SIN centrar**, anclados cerca del origen (esquina inferior-izquierda ≈ 0,0). Bboxes crudos: subte x=[-26,67], Aconcagua x=[-25,58], Cosmos x=[-23,500], Philo (núcleo) ~[-24,364].
2. El motor, en `load_pattern` (`Programas_hechos/Panel Decorativo/main.py`), **centra el patrón al abrir**, moviendo el centro del bbox al (0,0). Esto lo agregó Punto en el commit **`d7be7ba`** ("bbox centering", MSG_042/043).
3. **Philo es un tile bueno de ~360×623** (el 99% de su geometría: X p5–p95 = [-23,368], Y = [-17,596], = el offset). Pero tiene **~13 entidades sueltas de basura** (restos de vectorización) que se disparan hasta x=3281, y=4055 → **inflan su bbox a 4357×5392**.
4. El centrado-al-abrir centra sobre ese bbox inflado (centro ≈ (1102,1358)) → **corre el tile real ~1100 mm fuera de lugar** → el estampado desde el origen ya no lo cubre → **franja en blanco**.
5. Los patrones limpios (subte/Aconcagua/Cosmos) no lo sufren porque su bbox no tiene basura y el centrado apenas los mueve.

### Evidencia dura (bench console, panel real 550×1500, modo recorte)
- CON centrado (producción): cobertura X por banda de 55 mm = `[35,87,83,95,81,61,33,14,7,0]` → cae a 0 a la derecha (la franja).
- SIN centrado (mismo estampado original): `[71,62,79,100,74,100,75,90,89,45]` → **llena todo el ancho**. No rompe subte/Aconcagua/Cosmos.

## 3. Modelo canónico (definido por Constantino)

- Los patrones deben quedar **centrados**, para que el panel estampado **sangre (sobresalga) por los 4 márgenes** (izq/der/inf/sup). Si el patrón está anclado a la esquina, el margen inferior e izquierdo quedan sin cortar y aparecen vacíos.
- El **centrado tiene que estar en el ARCHIVO**, puesto **al guardar**, no metido por el programa al abrir.
  - Patrones **auto-generados** (vectorizar bitmap): el **vectorizador** los guarda centrados.
  - Patrones **a mano**: los ubica Constantino; la coordenada (0,0) del archivo es la esquina inferior-izquierda y él decide la posición. El programa **no** debe re-centrarlos.
- El tile **puede ser más grande que el offset**; las repeticiones se **solapan a propósito** (los motivos se encadenan). El solape es feature, no error.

### Validación del modelo (verificada)
Con los patrones **centrados** y el estampado **original** (sin centrado-al-abrir): subte/Aconcagua/Cosmos **sangran por los 4 lados y llenan** (izq=der=inf=sup=SÍ, cobertura pareja). O sea: **patrón centrado + estampado original = comportamiento deseado, sin tocar el bucle de estampado.**

## 4. Fix especificado (código = Punto)

Mover el centrado de "al abrir" a "al guardar":

- **(a)** **Sacar el centrado de `load_pattern`** en `Programas_hechos/Panel Decorativo/main.py` (revertir el bloque `d7be7ba`: las líneas que hacen `cx,cy = centro bbox; piece = piece.translated(-cx,-cy)`). El motor deja de centrar y respeta el archivo tal cual.
- **(b)** **El vectorizador guarda el DXF centrado** (bbox-center → origen) al generar un patrón desde bitmap. Es el lugar correcto para el auto-centrado.

**NO tocar** step_x/step_y, ni el bucle de estampado, ni recortar DXF. El estampado original ya produce sangrado 4-lados con patrones centrados (verificado).

### Descartado
La alternativa de "extender el rango de estampado para compensar el centrado" (Opción A que Atlas prototipó) **queda descartada**: el fix correcto es no centrar al abrir. El cambio de Atlas fue revertido, árbol limpio.

## 5. Transición / rollout (ojo, importante)

Hoy el centrado-al-abrir es lo que **le da el sangrado a los patrones limpios**. Si se saca (a) sin más, esos patrones **dejan de sangrar** hasta estar guardados centrados. Por eso es un **paquete**:

1. (a) + (b) juntos.
2. **Re-guardar centrados los patrones existentes** — **lo hace Constantino** (auto → re-vectorizar con el vectorizador ya arreglado; a mano → los reubica). Regla dura intacta: los datos los toca él.
3. **Philo además**: sacarle las ~13 entidades de basura. Re-centrar sobre basura vuelve a fallar; con el DXF limpio y centrado tilea perfecto. → también Constantino.

## 6. Reparto propuesto (respetando roles)

- **Punto** (dueño del motor legacy + vectorizador): (a) sacar centrado de `load_pattern` y (b) centrado-al-guardar en el vectorizador. Atlas queda disponible para revisar/aparear si Punto quiere.
- **Constantino**: re-guardar patrones centrados + limpiar la basura de Philo.
- **Orbit**: deploy del cambio de código cuando Punto lo tenga (coordinar orden con el re-guardado de patrones para no dejar ventana sin sangrado).
- **Atlas**: diagnóstico entregado (este documento). Sin trabajo de código pendiente salvo apoyo a Punto si lo pide.

### Nota de higiene (Orbit)
El app servido vive en `/home/costa/Nextango/apps/sistema_industrial/`, no en `/home/costa/frappe-bench/apps/`. Confirmar copia canónica y symlink.
