# HANDOFF — Cybelec / App de Plegado (memoria inicial para sesión integrada al equipo)

**Fecha:** 2026-07-01 · **Autor:** sesión Cybelec (aislada, ahora se reinicia integrada al equipo)
**Ubicación de todo el trabajo:** `research/cybelec/`
**Entregable vivo principal:** `research/cybelec/plegado_app/index.html`

---

## 1. Rol y objetivo

Línea del proyecto arrancada por Constantino: desarrollar herramientas de **control numérico / asistencia de plegado** para la plegadora **ADIRA (2007)** del taller, partiendo de la **ingeniería inversa del control Cybelec DNC 880**.

El objetivo concreto **evolucionó** desde "clonar el Cybelec" hacia un entregable inmediato y útil:

> **Una web-app asistente de plegado** para el controlador **Estun E21** que tiene la plegadora del taller (el E21 es "tonto", no tiene las funciones inteligentes del Cybelec).

**Qué hace la app:** el operario carga la geometría de la pieza (tramos = medidas externas + ángulos con signo, espesor, material, útiles) y la app calcula:
- **Desarrollo** (largo de chapa a cortar) por DIN 6935.
- **Secuencia de plegado** (en qué orden plegar, con detección de choque contra la geometría real de punzón/matriz).
- **Posiciones X (tope trasero) e Y (penetración de trancha)** por pliegue.

El operario carga X/Y en el E21 y **avanza paso a paso en pantalla**. Corre en un **iPad Air 1ª gen, iOS 12.5.8, Safari** → todo el JS es **vanilla compatible iOS 12** (sin `?.`/`??`, sin flex gap, `prompt`/`confirm` nativos, `localStorage`).

**Convención de máquina:** X horizontal (0 = centro de la V), Y hacia arriba +, 0 = hombros de la matriz. **Tope = derecha (atrás)**, **operario = izquierda (adelante)**; la chapa entra desde la izquierda. La máquina **siempre pliega hacia arriba** (el punzón baja y las dos alas suben simétricas metiéndose en la V).

---

## 2. Lo que estudié del Cybelec y la plegadora ADIRA

**Origen:** CD original en `C:\Users\vendo\OneDrive\Escritorio\cd ADIRA\cd ADIRA`.

Hechos técnicos ya establecidos (NO re-derivar):
- **Software PC1200** = app Visual Basic 6, motor en **`Dnc.dll`**, dongle **Sentinel**. Instalador InstallShield en `swbmhl2/disk*` (cabs sin extraer). **El algoritmo de secuencia está compilado en `Dnc.dll` → no es extraíble.** Implementamos los **criterios** documentados, no el código.
- **Formato `.DAT` crackeado:** strings con prefijo de longitud + floats en **Microsoft Binary Format** (`[exp][mant_lo][mant_mid][mant_hi]`, valor = (1+frac)·2^(exp−128)). Decodificador: `dat_decoder.py`.
- **Control real de la ADIRA = DNC 880** (familia DNC 800-880S / ModEva).
- **Cálculo Cybelec:** desarrollo por **DIN 6935** (k = 0.65 + 0.5·log10(ri/s)); **Y** = penetración geométrica `(V/2)·tan((180−α)/2)` + retorno elástico (springback); **X** = cotas externas − descuentos; tonelaje al aire; **secuencia por búsqueda con detección de colisión**.
- **CYCAD** convierte DXF → plegado por capas `OUTLINE / BENDS / SECTIONS`.

**Criterios de secuenciación del Cybelec (documentados en el manual, los que replicamos):**
1. **L. MÍN. CONTRA OPERARIO** — largo mínimo del lado del operario para poder sostener la pieza.
2. **MÍNIMO DE VOLTEADO / PIVOTADO / BASCULADO** — minimizar recolocaciones.
3. **MANIPULACIÓN ÓPTIMA.**
4. **N° MÁX PLEGADO CONTRA TOPE** — preferir reusar el mismo apoyo/tope en pliegues seguidos.
5. **No apoyar sobre segmento inclinado** — el tope debe topar contra un apoyo plano/estable.
6. **APOYO** = qué nodo/cara de la pieza descansa contra el tope.

**Sentido de plegado = SIGNO del ángulo** (⭐): −90° dobla para el lado contrario que +90°. La elección de qué lado es positivo es libre pero **constante en toda la pieza**. No hay campo aparte de sentido.

---

## 3. Archivos leídos / generados y qué aprendí de cada uno

Todo bajo `research/cybelec/`:

| Archivo | Qué es / qué aprendí |
|---|---|
| `REPORTE_CYBELEC.md` | Reporte general del análisis del CD y el control. |
| `MANUALES_DNC880_hallazgos.md` | **Clave.** Hallazgos del Manual de Utilización DNC 880: flujo operativo real (ver §abajo). |
| `bend_engine.py` | Motor de cálculo validado (desarrollo, Y, X) en Python. |
| `dat_decoder.py`, `decoded_dat_tables.txt` | Decodificación del formato `.DAT`. |
| `cerebro.js` | Prototipo Node del secuenciador con detección de choque (permutaciones + colisión). Base del secuenciador de la app. |
| `tools_library.json`, `tools_geometry.json` | Geometría de útiles extraída de los DXF (segmentos, V, rotaciones). |
| `tools_dxf/Plegadora punzon y matriz.dxf` | Punzón + matriz originales (matriz V20 90°, punzón cuello de cisne). |
| `tools_dxf/Punzones y matrices.dxf` | Inventario de útiles del taller: **5 punzones** (Agudo 40°, Aplaste/dobladillo=hem, **Recto**, Cuello cisne B, Largo) + **3 matrices** (Aguda V24 40°, V20 90°, **Cuadrada 4V rotable**). |
| `adira_pdfs/` y `text/ADIRA_*.txt` | PDFs de manuales ADIRA (copiados de la red `\\190.190.190.9\...`) y su texto extraído. |
| `plegado_app/index.html` | **La app.** Único archivo autocontenido (HTML/CSS/JS). |

**Del Manual de Utilización DNC 880** (lo más valioso, en `MANUALES_DNC880_hallazgos.md`):
- Método **L-alfa (2D):** cargar longitud, ángulo, longitud, ángulo… la última ala sin ángulo. El manual sugiere cargar **primero todas las longitudes y después los ángulos** (más rápido). El perfil **se dibuja solo**.
- **Medidas externas (DIN).**
- **Corrección de ángulo empírica** (así "clava" los ángulos el Cybelec): plegar prueba → medir ángulo real → cargarlo → el control calcula solo la corrección de Y. Repetir 2-3 veces. **⭐⭐ Mejora pendiente #1 en precisión** (aún NO implementada en la app).
- **Corrección X** con cotas externas: restar el espesor a mano, o cargar cota externa + corrección constante ≈ −espesor + corrección fina por pliegue. **Mejora pendiente** (no implementada).
- Campos útiles: **CY** (repetir N pliegues iguales), **COPIAR PLIEGUE**, **SIGMA** en Kg/mm² (≈ daN/mm²; acero 37 manual, taller usa 45), **RETR. TOPE TRA.** (el tope retrocede durante el plegado para que el ala que sube no lo golpee), PMS, PCV, BOMBEADO.

---

## 4. Lo que construí / programé — `plegado_app/index.html`

App de 3 pantallas (Datos → Resumen/Secuencia → Operación paso a paso) + modales (Calibración, galería de útiles, **galería de piezas**). Tema claro y colorido, entrada tipo planilla (Enter salta y agrega ala, texto preseleccionado, flechas ↑↓).

**Motor de cálculo (funciones):**
- `din6935_k`, `din6935_v`, `desarrollo` → largo a cortar.
- `penetracion`, `sensibilidad`, `tonelaje`, `penClamp` → Y y fuerza.
- Calibración Y empírica básica: `getCal`/`setCal` (localStorage `plegado_cal`, `{y90, sign}`).

**Secuenciador (cerebro):**
- `profile(fl,an,dr,done)` → perfil de la pieza según pliegues hechos.
- `place(fl,an,dr,done,bi,mx,my,s)` → coloca la pieza para plegar `bi` en una orientación (`mx`=qué extremo va al tope; `my`=voltear).
- `clearCheck` → choques contra matriz (abajo) y punzón (geometría real del útil).
- `nodeFlat` / `feasible` → apoyo del tope: topa donde frena el material más atrás dentro del alcance del dedo (`FINGER_H=30`) y verifica **apoyo plano/estable** (no inclinado).
- `simulateOrder` → simula un orden completo; cuenta choques, opViol, apoyos inestables, volteos, giros, recolocaciones de tope.
- `buscarOrden` → prueba permutaciones (hasta 8!), score:
  `collisions·1e9 + opViol·1e7 + unstable·5e6 + flips·1e5 + giras·2e3 + refChg·1e3 + totalX·0.5`.
- Modo manual: `placeManual` / `simulateManual` — el operario elige pliegue + nodo de apoyo por paso.

**Constantes de máquina:** `TABLE_HALF=88, X_MIN=5, X_MAX=600, DIE_DEPTH=10, FINGER_H=30`.

**Dibujo:** `partPoints`, `fitDraw`, `drawFinished` (perfil apaisado, ángulos con signo, letras de nodo A,B,C… en naranja sin círculo), `machineGeom`/`drawMachine` (simulación en la máquina: V simétrica, ambas alas suben, tope en el nodo elegido).

**Útiles:** `setPunch`/`setDie`/`rotateDie` (dado cuadrado 4 caras), `openGallery`, `updateToolBtns`, `segsThumb`. Por defecto: **punzón Recto + matriz V20 90°**. `ri` por defecto 2.4.

### Cambios hechos en la ÚLTIMA sesión (importantes, ya commiteables):

1. **Bug de tope en modo manual** — `drawMachine` dibujaba el tope en el nodo automático más a la derecha, ignorando el nodo elegido. Ahora dibuja el tope en `st.gaugeNode` con su letra.

2. **DXF con arcos reales** (a pedido de Constantino). Reescrito el exportador:
   - `buildSheetElements(fl,an,dr,ri,s)` → contorno como **elementos geométricos exactos**: tramos rectos `{t:'L'}` + pliegues como **arcos de circunferencia** `{t:'A',C,R,a0,a1,phi}` (centro, radio, ángulos). Dos caras offset ±s/2 + dos tapas.
   - `elemsToDXF` → entidades **`ARC`** (CCW, invierte extremos si phi<0) y **`LINE`** nativas. **Nada de polígonos.**
   - Verificado: todas las piezas cierran (cada vértice tocado por exactamente 2 entidades), radios exactos **ri interno / ri+s externo**.

3. **Secuenciador — 2 criterios Cybelec + el bug de fondo de las piezas Z:**
   - Agregado "**no apoyar sobre segmento inclinado**" (`nodeFlat`/`stable`, alcance de dedo `FINGER_H`).
   - Agregado "**reusar el mismo tope**" (`refChg`, N° máx plegado contra tope).
   - **BUG DE FONDO CORREGIDO:** como la máquina siempre pliega hacia arriba, un pliegue de sentido opuesto exige **voltear la pieza**. Los flags `mx` y `my` **no son independientes**: **`mx XOR my` debe valer el signo del pliegue**. El código viejo probaba `[[false,myF],[true,myF]]` — la combo `(true,myF)` plegaba **al revés** (espejo simple = handedness invertida), y por eso **toda pieza con un pliegue opuesto (Z) chocaba siempre**. Corregido a `opts=[[false,myF],[true,!myF]]` en `simulateOrder` y `placeManual`. Las dos combos válidas son la **misma pieza rotada 180°** (elegir qué extremo va al tope = "gira").
   - Verificado en 8 formas: **Z y Escalón ahora sin choque** (antes chocaban); U/L/Caja/Canal siguen bien y con menos giros; **Sombrero/omega** sigue con 1 choque en el pliegue interno profundo — es real (la parte ya formada cuelga y pega contra la matriz; el cuello de cisne NO lo arregla porque despeja arriba, no abajo → requiere revisar setup, no es bug).

4. **Galería de piezas (NUEVO, a pedido):** guardar/navegar/levantar piezas.
   - `localStorage` clave **`plegado_galeria`** (array). Guarda: `name`, `segs` (len+ang **con signo**), `s/V/ri/sb/Rm/L`, `punchId`, `dieId`, `rot`, `ts`.
   - Botones en pantalla de datos: **💾 Guardar** (pide nombre, sugiere "Pieza 50-80-50") y **📁 Galería**.
   - Modal `#partsModal`: tarjetas con **miniatura** del perfil (`partThumb` desde `partPoints`), nombre, info (nº alas · V · espesor). Tocar → `loadPart` restaura todo y vuelve a Datos. **✕** → `deletePart` (con confirmación).
   - Funciones: `getGaleria`/`setGaleria`/`partThumb`/`segsToFAD`/`partDefaultName`/`savePart`/`loadPart`/`deletePart`/`openParts`/`toolIndexById`/`escapeHtml`.
   - Verificado headless (guardar → leer → thumbnail → default name → restaurar V/ri → borrar). Sintaxis del archivo entero OK.

**Testing:** todo se prueba con Node headless extrayendo funciones del `index.html` (regex + balanceo de llaves) y stubbeando DOM/localStorage. Los scripts de prueba quedaron en el scratchpad de la sesión (no en el repo).

---

## 5. Ideas / planes para la galería de plegados de perfiles

**Ya hecho:** guardar, navegar (miniaturas), levantar, borrar — todo en `localStorage`, offline en el iPad.

**Ofrecido a Constantino, pendiente de que confirme (NO implementado):**
- **Renombrar** una pieza guardada (hoy solo se nombra al guardar).
- **Duplicar** una pieza para hacer variantes.
- **Exportar / importar** la galería completa (backup / pasar a otro iPad) — como JSON.

**Ideas propias para más adelante:**
- Guardar también desde la pantalla de Resumen (no solo desde Datos).
- Adjuntar a cada pieza guardada su **secuencia elegida** y sus **correcciones X/Y calibradas**, para que al levantarla ya venga afinada.
- Buscar/filtrar por nombre cuando haya muchas.

---

## 6. Otra info importante que no se debe perder

**Mejoras pendientes priorizadas (del manual):**
1. ~~**Corrección de ángulo empírica**~~ ✅ HECHA 2026-07-01 (ver abajo).
2. ~~**Corrección X** global + por pliegue~~ ✅ HECHA 2026-07-01 (ver abajo).
3. Permitir **tipear el ángulo con signo** (−90) para igualar el hábito Cybelec (hoy funciona por signo pero conviene reforzar la UX — falta criterio de Constantino sobre qué mejorar).
4. ~~**CY / copiar pliegue**~~ ✅ HECHA 2026-07-01 (botón ⧉ por fila).
5. ~~Relabel σ a **Kg/mm²** y revisar coef~~ ✅ HECHA 2026-07-01 (label kg/mm², conversión ×9.81; la fórmula 1.33·Rm·L·s²/V y el /9.81 a ton ya estaban bien).

**Hecho 2026-07-01 (sesión integrada al equipo, CYBELEC_TASK_001 + pedidos directos):**
- **Bug de sentido en `machineGeom` corregido**: en pasos con `mx`+`my` combinados, el dibujo animado invertía el giro de un brazo (pliegues "para lados opuestos"). Ahora el ángulo con signo sale de comparar `place()` con `done[bi]` false/true (misma geometría que valida el resto). El resaltado rojo de choque en el dibujo también quedó bien.
- **Zoom centrado en el pliegue** (TASK_001 Fix 1): vista de Operación por defecto = clip `MACHINE_CLIP=160`mm a cada lado del vértice activo; botón "🔍 Zoom pliegue" (default ON) alterna con vista pieza-completa. Botón "⬇ Bajar punzón" dibuja el punzón a fondo (PMI) en vez de en reposo.
- **"Guardar DXF como..."** (TASK_001 Fix 2): `showSaveFilePicker` en navegadores modernos, `prompt` como fallback iOS 12. Nombre sugerido: ref del pedido > `partDefaultName` > "pieza_corte".
- **Corrección de ángulo empírica ⭐⭐**: botón "📐 Plegué y medí el ángulo…" en Operación. Acumulativa (repetir hasta clavar), corrige Y por `penetracion()`, aplica a todos los pliegues del mismo ángulo objetivo, "R" borra, `state.angCorr` viaja con la pieza en la galería (`savePart`/`loadPart`). Decisión: por pieza, NO global por útiles (evita correcciones viejas silenciosas); cambiar si Constantino prefiere lo otro.
- **Análisis omega 15-15-300-15-15**: la secuencia "patitas primero" choca de verdad (geométrico, ambas orientaciones); "pliegues internos primero" (la automática) sale limpia.
- **Corrección X global + por pliegue ⭐**: global en modal Calibración (`cal.xg` en `plegado_cal`, offset de máquina); fina con botón "📏 Medí el ala…" en Operación (acumulativa, `state.xCorr` por bendIndex, "R" borra, viaja con la pieza en galería). X final = `Xraw + cal.xg + xCorr[bi]`; el secuenciador/choques/dibujo siguen con la X cruda. `enrich()` ahora expone `Xraw` y `X`.
- **CY / copiar pliegue**: botón ⧉ por fila en la tabla de medidas, duplica el ala a continuación; si se duplica la última, la original pasa a intermedia con 90°.
- **σ en kg/mm²**: label cambiado y conversión exacta ×9.81 (antes ×10 como daN).
- Reportes: `coordination/reports/CYBELEC_TASK_001_REPORT.md` + `coordination/channel/Nova/MSG_040_CYBELEC_task001_done.md`.

**Hecho 2026-07-02 — Port a Frappe (tarea de Constantino):**
- **Page `perfiles-plegados`** en la rama erpnext (`Nextango-erpnext/`, commit `2d24ac2`): `page/perfiles_plegados/` (json/html/css/js) portada de esta app con script mecánico (ids → prefijo `pp-`, CSS scopeado `#pp-root`, JS envuelto en `on_page_load`). Datos: `SI Material Corte` (`precio_por_kg`, `densidad_kg_m2`) + `SI Precios Globales` (`precio_por_plegado`) via `frappe.call`. Pedidos: `api/perfiles.py` (JSON files `PL-YYYYMMDD-NNNN`, DocType pendiente de definición). Tests: `tests/test_perfiles_pedidos.py`.
- **REGLA DE SINCRONÍA**: el motor vive acá (`plegado_app/index.html`, main) y se portea a la page Frappe — no editar el motor en la page directamente. El script de porteo quedó en el scratchpad de la sesión 2026-07-02 (re-crear si hace falta: extrae style/body/script, renombra ids, reescribe el bloque de integración).
- Coordinación: Vega hace armonización visual/navegación del desk (MSG_019 en su canal); deploy en el server pendiente (bench migrate + build).

**Lo que falta para "secuencias óptimas":** implementados los **criterios** documentados, pero afinar los pesos hasta óptimo necesita **casos reales**. **Pedido abierto a Constantino:** que mande **1-2 piezas concretas** que hace seguido (medidas de tramos, ángulos con signo, espesor) **y en qué orden las pliega él / el Cybelec**, para calibrar contra datos reales en vez de adivinar pesos. El caso **sombrero/omega** es el más difícil (canal profundo con pestañas) y puede requerir setup especial.

**Preferencias de Constantino (memoria del equipo):**
- Responder siempre en **español**.
- Solo **escalar a Constantino** lo que bloquea el sprint o requiere criterio de negocio; el resto va a backlog.
- Empresa metalúrgica; stack ERPNext + Tango + Excel + CypCut.

**Estado del proyecto general (del equipo):** ERPNext no instalado aún; primera meta = panel decorativo cotizable end-to-end. Esta línea (Cybelec/plegado) es paralela. Equipo: Nova (dirige, no programa), Atlas, Lechu, Punto, Nido, Tango, Gemu, Vega, Orbit. Coordinación en `coordination/`; memoria en `.claude/projects/C--SistemaIndustrial-Nextango/memory/`.

**Memorias relevantes existentes:** `project_cnc_propio_cybelec.md` (esta línea), `project_context.md`, `system_current_state.md`, `team_roles.md`, `team_sessions.md`.

**Para abrir la app:** abrir `research/cybelec/plegado_app/index.html` en el navegador (en el iPad: Safari → Compartir → "Agregar a inicio").
