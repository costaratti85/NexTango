# DECISION_017 — Modelo de patrones: el DXF que carga Constantino ES el patrón; se repite por offsets, con solape permitido

**Fecha:** 2026-07-20 · **Definido por:** Constantino · **Registrado por:** Nova
**Estado:** Vigente — **canon del modelo de patrones**
**Afecta a:** Atlas (motor de generación/tileo), Punto (geometría), Vega (UI de patrones)
**Ampliada 2026-07-22:** posición, centrado y coordenada cero (§0, palabra final de Constantino, conversado con Atlas).

---

## 0. ⭐ CANON DE POSICIÓN, CENTRADO Y ORIGEN (palabra final de Constantino, 2026-07-22)

Tres reglas, definitivas:

- **a. Centrado al guardar — SOLO por vectorización.** Los patrones generados por **vectorización de imagen** se centran **al guardar**. Ese es el único momento y el único caso en que el sistema recentra un patrón.
- **b. Abrir NUNCA modifica la posición.** Abrir/cargar un patrón **no** cambia su posición — jamás. (Esto es exactamente lo que arregló el fix de Philo: `load_pattern` centraba al abrir, y estaba mal.)
- **c. La coordenada CERO es SIEMPRE la esquina donde se cruzan el margen inferior y el margen izquierdo.** No hay otro origen. Todo se referencia a esa esquina (abajo-izquierda del área útil).

**Consecuencia sobre el trabajo en curso (`PUNTO_CENTRADO_AL_GUARDAR_PATRONES`):** la tarea NO es "sacar el centrado al guardar en general". Según la regla **a**, el centrado al guardar **se conserva para los patrones de vectorización**. Lo que se elimina es el centrado **al abrir** (regla **b**) y cualquier recentrado indebido fuera del caso de vectorización. Ver la nota a Punto — hay que **acotar** ese cambio al canon, no aplicarlo en bloque.

---

## 1. La regla definitiva

1. **Todo DXF que Constantino carga en la carpeta de patrones ES un patrón.** Punto.
2. **El sistema NO juzga si el contenido "es válido"** ni si "parece un patrón". No hay criterio de forma, tamaño ni contenido que descalifique un archivo cargado.
3. **El patrón se repite EXACTAMENTE según los offsets que él escribe:** `step_x = Offset X`, `step_y = Offset Y`. Las copias se estampan cada `step_x` a lo ancho y cada `step_y` a lo alto, hasta **cubrir toda la chapa**.
4. **El tile PUEDE ser más grande que el offset.** Cuando lo es, **las repeticiones se SOLAPAN / se intersectan — A PROPÓSITO.**

## 2. El solape es una FEATURE, no un error

Hay patrones cuyo motivo **se encadena con su propia repetición**: el DXF tiene áreas pensadas para intersectar la copia vecina. Por eso el bounding box del patrón puede ser **mayor** que el offset, y eso es **correcto y deseado**.

> **Regla dura:** que un tile sea más ancho/alto que su offset **NO es una señal de error**. Es la forma en que los motivos se encadenan. **Nunca** tratar `bbox > offset` como validación fallida ni como motivo para estampar una sola copia.

## 3. Qué refuta esto

Refuta la premisa de que **"un patrón debe ser una celda del tamaño del offset"** (Atlas, MSG_173). Esa premisa **nunca fue fijada por Constantino** — se infirió de los patrones que ya existían. El modelo real es al revés: el offset es el **paso de repetición**, no el **tamaño de la celda**; el tile puede exceder el paso.

## 4. El bug que esto expone (para Atlas)

El motor calculaba **1 sola columna** cuando el DXF era **más ancho que `step_x`** — porque asumía que un tile más ancho que el paso "ya cubría". El eje **Y no tenía ese problema** (por eso las filas sí tileaban). El fix: **estampar copias cada `step_x` hasta cubrir toda la chapa, con solape permitido**, **simétrico al eje Y**. Ver la orden directa de Constantino a Atlas.

**Verificación obligatoria:** el panel real **Philo v3, 550 × 1500 mm**. No se da por cerrado sin reproducir ese caso lleno de columnas.

## 5. 🎓 Aprendizaje de proceso — esto es lo más importante de la decisión

Atlas, de un conjunto de patrones existentes, **infirió una "regla"** ("un patrón es una celda del tamaño del offset") y **con esa regla descalificó un archivo que había cargado Constantino** ("no era un patrón válido").

**Eso se pasó de la raya.** Es exactamente el caso que cubre la cláusula de conflicto de la `SOURCE_OF_TRUTH_MATRIX`:

> Si algo contradice el modelo, el agente **PARA y produce un decision pack** — no concluye que el **input de Constantino** está mal.

**La regla, explícita para todo el equipo:**

> Cuando un agente infiere una regla a partir de los ejemplos existentes, y esa regla lo llevaría a **descalificar algo que cargó o pidió Constantino**, tiene que **PARAR y ESCALAR a Nova** — **nunca** concluir que el input está mal.

Constantino es la fuente de verdad del criterio (Brújula regla 8: el sistema sugiere, el humano decide). Una generalización sobre los datos existentes **no es** una regla del negocio hasta que Constantino la confirme. Descartar su input con una regla que él nunca fijó es invertir quién manda.

## 6. Relación con el canon

Coherente con Brújula §3 (*"reglas del patrón: margen, offset X/Y…"*) — esta decisión **precisa** que el offset es el paso de repetición y que el solape es válido. No enmienda Brújula: la desarrolla.
